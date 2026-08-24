import trafilatura
import time
import os
import httpx
import numpy as np
from concurrent.futures import ThreadPoolExecutor
from litellm import embedding, rerank 
from sentence_transformers import CrossEncoder
import re


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

def fetch_page(client: httpx.Client, url: str):
    try:
        resp = client.get(url)
    except httpx.HTTPError:
        return None
    if resp.status_code != 200:
        return None
    markdown = trafilatura.extract(resp.text, output_format="markdown", include_links=True)
    meta = trafilatura.extract_metadata(resp.text, default_url=url)
    title = meta.title if meta and meta.title else url
    if not markdown:
        return None
    return {"url": str(resp.url), "content": markdown, "title": title}


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
    print("starting embedding")
    content = []
    for result in results:
        for chunk in chunk_text(result["content"]):   
            content.append({"url": result["url"], "content": chunk, "title":result["title"]})

    if not content:
        return []

    e_query = embedding(model=os.environ["EMBEDDING_MODEL"], input=query, num_retries=3)
    embeds = embedding(
        model=os.environ["EMBEDDING_MODEL"],
        input=[c["content"] for c in content],
        num_retries=3
    )

    query_vec = np.array(e_query["data"][0]["embedding"], dtype=np.float32)
    results_vec = np.array(
        [item["embedding"] for item in embeds["data"]], dtype=np.float32
    )

    idx, scores = top_k_similar(query_vec, results_vec, 35)

    print(f"finished embedding in {time.perf_counter()-starttime}, starting reranking")

    if os.environ["RERANKER_RUNNER"] == "local":
        # Reranker magic
        model = CrossEncoder("cross-encoder/ettin-reranker-68m-v1")

        
        scores = model.predict([(query, doc["content"]) for doc in content])
    else:
        results = rerank_openrouter(
            query=query,
            documents=[doc["content"] for doc in content],
        )
        # results: list of {index, relevance_score}, sorted by score desc
        scores = [None] * len(content)
        for r in results:
            scores[r["index"]] = r["relevance_score"]
    print(f"finished reranking in {time.perf_counter()-starttime}")

    results = []
    # constructing array from scores
    for i, score in enumerate(scores):
        results.append({
            "url":content[i]["url"],
            "title":content[i]["title"],
            "content":content[i]["content"],
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

    print(f"search query finished in {time.perf_counter()-start}")
    pages_result = pages(urls)
    print(f"all pages fetched in {time.perf_counter()-start}")

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
