import rs_trafilatura
import logging
import time
import os
import httpx
import numpy as np
from concurrent.futures import ThreadPoolExecutor
from litellm import embedding, rerank
from sentence_transformers import CrossEncoder
import re

logger = logging.getLogger(__name__)

# upstream embedding provider (pplx-embed via OpenRouter) limits per request:
# max 512 items AND max 120,000 total tokens. The old estimator assumed
# ~2 chars/token, but token-dense text (code, CJK, markdown symbols) can be
# close to ~1 char/token, so a "100k estimated" batch could actually be
# ~150k+ tokens and 400. Assume worst case 1 char ~= 1 token and keep a
# large headroom below the 120k cap. Individual inputs are hard-truncated
# so one monster chunk can never blow a batch, and batches that still get
# rejected are recursively halved.
EMBED_MAX_ITEMS = 128
EMBED_TOKEN_BUDGET = 60_000
EMBED_CHARS_PER_TOKEN = 1
MAX_EMBED_CHARS = 2000
MAX_QUERY_CHARS = 2000


def _truncate(s: str, limit: int) -> str:
    return s[:limit] if len(s) > limit else s


def batch_embed_inputs(inputs):
    batches = []
    cur, cur_tokens = [], 0
    for raw in inputs:
        item = _truncate(raw, MAX_EMBED_CHARS)
        est = max(1, len(item) // EMBED_CHARS_PER_TOKEN)
        # single item must never exceed the budget on its own
        if est > EMBED_TOKEN_BUDGET:
            item = _truncate(item, EMBED_TOKEN_BUDGET * EMBED_CHARS_PER_TOKEN)
            est = max(1, len(item) // EMBED_CHARS_PER_TOKEN)
        if cur and (len(cur) >= EMBED_MAX_ITEMS or cur_tokens + est > EMBED_TOKEN_BUDGET):
            batches.append(cur)
            cur, cur_tokens = [], 0
        cur.append(item)
        cur_tokens += est
    if cur:
        batches.append(cur)
    return batches


def _is_token_limit_error(e: Exception) -> bool:
    msg = str(e).lower()
    return ("exceeds maximum" in msg or "maximum is" in msg) and "token" in msg


def _embed_batches(model: str, batches):
    """Embed batches, recursively halving any batch the provider rejects
    for exceeding its token limit. Returns flat list of data items."""
    from litellm.exceptions import BadRequestError

    data = []
    queue = list(batches)
    while queue:
        batch = queue.pop(0)
        if not batch:
            continue
        try:
            embeds = embedding(
                model=model,
                input=batch,
                num_retries=2,
                timeout=30,
            )
            data.extend(embeds.data)
        except BadRequestError as e:
            if len(batch) == 1:
                # single truncated input still too big: halve its chars and retry
                item = batch[0]
                if len(item) <= 1 or not _is_token_limit_error(e):
                    raise
                logger.warning("single embed input rejected, halving %d chars", len(item))
                queue.insert(0, [item[: len(item) // 2]])
            elif _is_token_limit_error(e):
                mid = len(batch) // 2
                logger.warning("embed batch rejected (%d items), splitting %d/%d", len(batch), mid, len(batch) - mid)
                queue.insert(0, batch[mid:])
                queue.insert(0, batch[:mid])
            else:
                raise
    return data


def chunk_text(text, max_chars=2000, overlap=200):
    """Pure-Python overlapping chunker — no native tokenizer."""
    text = text.strip()
    if not text:
        return []
    if len(text) <= max_chars:
        return [text]
    # split on sentence boundaries where possible
    parts = re.split(r'(?<=[.!?])\s+', text)
    chunks, cur = [], ""
    for p in parts:
        if len(cur) + len(p) + 1 <= max_chars:
            cur = (cur + " " + p).strip() if cur else p
        else:
            if cur:
                chunks.append(cur)
            if len(p) > max_chars:               # hard-split a monster sentence
                for i in range(0, len(p), max_chars - overlap):
                    chunks.append(p[i:i + max_chars])
                cur = chunks.pop()[-overlap:] if overlap else ""
            else:
                cur = p
    if cur:
        chunks.append(cur)
    if overlap and len(chunks) > 1:              # re-apply overlap window
        chunks = [chunks[0]] + [(chunks[i-1][-overlap:] + " " + c).strip()
                                for i, c in enumerate(chunks[1:], 1)]
    return chunks

# rs-trafilatura panics (kills the process) when extracted text exceeds its
# hardcoded 1MB byte cap and the cut lands inside a multibyte UTF-8 char.
# Clamp input so extracted text can never reach that cap.
MAX_HTML_BYTES = 900_000

def clamp_html(html: str) -> str:
    data = html.encode("utf-8")
    if len(data) <= MAX_HTML_BYTES:
        return html
    return data[:MAX_HTML_BYTES].decode("utf-8", "ignore")

def fetch_page(client: httpx.Client, url: str):
    try:
        resp = client.get(url)
        if resp.status_code != 200:
            return None
        result = rs_trafilatura.extract(
            clamp_html(resp.text),
            url=str(resp.url),        # helps page-type classification
            output_markdown=True,
            include_tables=True,
        )
        md = result.content_markdown or result.main_content
        if not md or (result.extraction_quality or 0) < 0.5:
            return None
        return {"url": str(resp.url), "content": md, "title": result.title or url}
    except Exception:
        return None

def pages(urls):
    headers = {"User-Agent": "SlopUI-bot/0.1"}

    if not urls:
        return []
    with httpx.Client(timeout=10.0, headers=headers, follow_redirects=False) as client:
        with ThreadPoolExecutor(max_workers=min(len(urls), 20)) as pool:
            futures = [pool.submit(fetch_page, client, u) for u in urls]
            results = [f.result() for f in futures]
    return [r for r in results if r is not None]


def embeddings(query, results, starttime):
    logger.debug("starting embedding")
    content = []
    for result in results:
        for chunk in chunk_text(result["content"]):   
            content.append({"url": result["url"], "content": chunk, "title":result["title"]})

    if not content:
        return []

    inputs = [_truncate(query, MAX_QUERY_CHARS)] + [
        _truncate(c["content"], MAX_EMBED_CHARS) for c in content
    ]
    data = _embed_batches(os.environ["EMBEDDING_MODEL"], batch_embed_inputs(inputs))
    e_query = data[0]
    content_embeds = data[1:]

    query_vec = np.array(e_query["embedding"], dtype=np.float32)
    results_vec = np.array([item["embedding"] for item in content_embeds], dtype=np.float32)

    idx, _ = top_k_similar(query_vec, results_vec, 35)

    # embedding narrowed all chunks down to the 35 most similar —
    # reranker only judges those
    rerank_docs = [content[i] for i in idx]

    logger.debug(f"finished embedding in {time.perf_counter()-starttime}, starting reranking")

    if os.environ["RERANKER_RUNNER"] == "local":
        # Reranker magic
        model = CrossEncoder("cross-encoder/ettin-reranker-68m-v1")

        
        scores = model.predict([(query, doc["content"]) for doc in rerank_docs])
    else:
        results = rerank_openrouter(
            query=query,
            documents=[doc["content"] for doc in rerank_docs],
        )
        # results: list of {index, relevance_score}, sorted by score desc
        scores = [None] * len(rerank_docs)
        for r in results:
            scores[r["index"]] = r["relevance_score"]
    logger.debug(f"finished reranking in {time.perf_counter()-starttime}")

    results = []
    # constructing array from scores
    for i, score in enumerate(scores):
        results.append({
            "url":rerank_docs[i]["url"],
            "title":rerank_docs[i]["title"],
            "content":rerank_docs[i]["content"],
            "score":score
            })
    results.sort(key=lambda r: r["score"], reverse=True)
    results = results[:8]
        


    #rerankrequest = RerankRequest(query=query, passages=passages)
    #results = ranker.rerank(rerankrequest)

    # reconstruct structure to be LLM friendly
    response = []
    for result in results:
        found = False
        for i,element in enumerate(response):
           if element["url"] == result["url"]:
               found = True
               response[i]["content"].append(result["content"])
        if found == False:
            response.append({
                "url":result["url"],
                "title":result["title"],
                "content":[result["content"]],
                "score":float(result["score"])
                })
            
       


    return response

def websearch(query):
    start = time.perf_counter() 
    with httpx.Client(timeout=10) as client:
        response = client.get(
            f"http://127.0.0.1:8888/search?q={query}&format=json&safesearch=0"
        )
    data = response.json()

    urls = [r["url"] for r in data.get("results", [])][:15]
    if not urls:
        return []

    logger.debug(f"search query finished in {time.perf_counter()-start}")
    pages_result = pages(urls)
    logger.debug(f"all pages fetched in {time.perf_counter()-start}")

    return embeddings(query, pages_result, start)

def top_k_similar(query, results, k=None):
    q = query / np.linalg.norm(query)
    R = results / np.linalg.norm(results, axis=1, keepdims=True)
    scores = q @ R.T
    top_idx = np.argsort(scores)[::-1]
    if k is not None:
        top_idx = top_idx[:k]
    return top_idx, scores[top_idx]



def rerank_openrouter(
    query: str,
    documents: list[str],
    top_n: int | None = None,
    model: str | None = None,
) -> list[dict]:
    model = model or os.environ["RERANKER_MODEL"]
    payload: dict[str, object] = {
        "model": model,
        "query": query,
        "documents": documents,
    }
    if top_n is not None:
        payload["top_n"] = top_n
    resp = httpx.post(
        "https://openrouter.ai/api/v1/rerank",
        headers={
            "Authorization": f"Bearer {os.environ['OPENROUTER_API_KEY']}",
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()["results"]
