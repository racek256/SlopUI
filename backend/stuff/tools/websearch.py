import trafilatura
import httpx
import numpy as np
import pprint
from concurrent.futures import ThreadPoolExecutor
from tokenizers import Tokenizer
from litellm import embedding  # sync version of aembedding
from flashrank import Ranker, RerankRequest
from sentence_transformers import CrossEncoder

tok = Tokenizer.from_pretrained("BAAI/bge-m3")


def chunk_text(text, max_tokens=512, overlap=64):
    """Split text into overlapping chunks of ~max_tokens tokens."""
    ids = tok.encode(text).ids
    chunks = []
    start = 0
    while start < len(ids):
        end = min(start + max_tokens, len(ids))
        chunks.append(tok.decode(ids[start:end], skip_special_tokens=True))
        if end == len(ids):
            break
        start = end - overlap
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
    headers = {"User-Agent": "SlopUI-bot/0.1 (research tool)"}

    if not urls:
        return []
    with httpx.Client(timeout=10.0, headers=headers, follow_redirects=True) as client:
        with ThreadPoolExecutor(max_workers=min(len(urls), 20)) as pool:
            futures = [pool.submit(fetch_page, client, u) for u in urls]
            results = [f.result() for f in futures]
    return [r for r in results if r is not None]


def embeddings(query, results):
    content = []
    for result in results:
        for chunk in chunk_text(result["content"]):   
            content.append({"url": result["url"], "content": chunk, "title":result["title"]})

    if not content:
        return []

    print("running Embedding")
    e_query = embedding(model="ollama/nomic-embed-text-v2-moe", input=query)
    embeds = embedding(
        model="ollama/nomic-embed-text-v2-moe",
        input=[c["content"] for c in content],
    )

    query_vec = np.array(e_query["data"][0]["embedding"], dtype=np.float32)
    results_vec = np.array(
        [item["embedding"] for item in embeds["data"]], dtype=np.float32
    )

    print("scoring embeddings")
    idx, scores = top_k_similar(query_vec, results_vec, 35)

    print("running Reranker")
    # Reranker magic
    model = CrossEncoder("cross-encoder/ettin-reranker-68m-v1")
    #ranker = Ranker(model_name="ms-marco-MiniLM-L-12-v2", cache_dir="/opt")

    # construct array
    #passages = []
    #for i,idx in enumerate(idx):
    #    passages.append({
    #        "id":i,
    #        "text":content[idx]["content"],
    #        "meta": {"url":content[idx]["url"], "title":content[idx]["title"]}
    #        })

    scores = model.predict([(query, doc["content"]) for doc in content])

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
    pprint.pp(results)

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
    with httpx.Client(timeout=10) as client:
        response = client.get(
            f"http://127.0.0.1:8888/search?q={query}&format=json&safesearch=0"
        )
    data = response.json()

    urls = [r["url"] for r in data.get("results", [])][:15]
    print(urls)
    if not urls:
        return []

    return embeddings(query, pages(urls))

def top_k_similar(query, results, k=None):
    q = query / np.linalg.norm(query)
    R = results / np.linalg.norm(results, axis=1, keepdims=True)
    scores = q @ R.T
    top_idx = np.argsort(scores)[::-1]
    if k is not None:
        top_idx = top_idx[:k]
    return top_idx, scores[top_idx]
