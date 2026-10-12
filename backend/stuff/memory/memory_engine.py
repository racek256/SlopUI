import os
import httpx
import numpy as np
import litellm
from dotenv import load_dotenv
load_dotenv("../.env", override=True)
load_dotenv(".env", override=True)

import sqlite3
from stuff.memory.memory_filter import memory
from stuff.memory.conv_parser import parser
from stuff.settings import get_settings


def _embedding_conf():
    """Resolve embedding config: (baseURL, api_key, model)."""
    cfg = get_settings().get("embedding", {}) or {}
    model = cfg.get("model", "perplexity/pplx-embed-v1-0.6b")
    base_url = cfg.get("baseURL", cfg.get("base_url", "https://openrouter.ai/api/v1"))
    api_key_env = cfg.get("api_key_env", "EMBEDDING_API_KEY")
    api_key = os.environ.get(api_key_env) if api_key_env else None
    if not api_key:
        raise KeyError(f"embedding api key missing: set {api_key_env} in the environment")
    return base_url, api_key, model


def _memory_conf():
    """Resolve memory config dict with safe fallbacks (never crashes on missing section)."""
    try:
        cfg = get_settings().get("memory", {}) or {}
    except Exception:
        cfg = {}
    base_url = cfg.get("baseURL", cfg.get("base_url"))
    model = cfg.get("model")
    return {
        "provider": cfg.get("provider"),
        "base_url": base_url,
        "api_key_env": cfg.get("api_key_env"),
        "model": model,
        "filter_model": cfg.get("filter_model", model),
    }


def _reranker_conf():
    """Resolve reranker config: (baseURL, api_key, model)."""
    cfg = get_settings().get("reranker", {}) or {}
    model = cfg.get("model", "rerank-english-v3.0")
    base_url = cfg.get("baseURL", cfg.get("base_url", "https://api.cohere.com/v1"))
    api_key_env = cfg.get("api_key_env", "RERANKER_API_KEY")
    api_key = os.environ.get(api_key_env) if api_key_env else None
    if not api_key:
        raise KeyError(f"reranker api key missing: set {api_key_env} in the environment")
    return base_url, api_key, model


def _cohere_rerank(query, documents, top_n=None):
    """POST to a Cohere-compatible /rerank endpoint. Returns
    list of {index, relevance_score} sorted by score desc."""
    base_url, api_key, model = _reranker_conf()
    base = (base_url or "").rstrip("/")
    if base.endswith("/rerank"):
        url = base
    elif base.endswith("/v1"):
        url = base + "/rerank"
    else:
        url = base + "/v1/rerank"
    payload = {
        "model": model,
        "query": query,
        "documents": documents,
    }
    if top_n is not None:
        payload["top_n"] = top_n
    resp = httpx.post(
        url,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=30,
    )
    resp.raise_for_status()
    return sorted(resp.json()["results"], key=lambda r: r.get("relevance_score", 0), reverse=True)

def test(conn, chat_id):
    # testing params
    # load DB
    cursor = conn.cursor()

    messages = cursor.execute("select * from messages where chat_id = ?",(chat_id,)).fetchall()
    # Rebuilding chat array




    query = cursor.execute("select id from messages where chat_id = ? order by id desc limit 1", (chat_id,)).fetchone()
    last_message = query["id"]

    # Start for loop of finding message parent_message_id and store into array 
    history = []
    found = False 
    while not found:
        for message in messages:
            if message["id"] == last_message:
                if message["role"] == "assistant":
                    history.append({
                        "role":"assistant",
                        "content":message["content"]
                        })
                else:
                    history.append({
                        "role":"user",
                        "content":[{"type":"text", "text":message["content"]}]
                        })

                if message["parent_message_id"] is not None:
                    last_message = message["parent_message_id"]
                else:
                    found = True

    # reverse the array 
    history.reverse()
    _conf = _memory_conf()
    _model = _conf.get("model")
    if not _model:
        raise KeyError("memory.model missing: set memory.model in config.yaml")
    return parser(_model, history)
    
import asyncio

async def user_run(user_id,limit):
    conn = sqlite3.connect("./db.db", check_same_thread=False)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    conversations = []
    last_50 = cursor.execute("select id from chats where user_id = ? and (memorized = 0 or memorized is NULL) and name is not null and last_model is not null order by id desc limit ?",(user_id,limit)).fetchall()
    ids = [k[0] for k in last_50]
    for idx, i in enumerate(ids):
        print(f"scanning conversation:{idx + 1}/{len(ids)} (chat_id={i})", flush=True)
        conversations.append(test(conn, i))
    print(conversations)
    ready_convs = []
    for conv in conversations:
        for item in conv:
            if "memory" in item and item["memory"]:
                try:
                    ready_convs.append(conv)
                except:
                    ready_convs.append(conv)

                break;
    current_memory = cursor.execute("select * from memories where user_id = ?",(user_id,))
    processed_memory = [{"id":k["id"],"content":k["content"]} for k in current_memory]
    _mconf = _memory_conf()
    _filter_model = _mconf.get("filter_model", _mconf.get("model"))
    if not _filter_model:
        raise KeyError("memory.filter_model missing: set memory.filter_model in config.yaml")
    local_memory = memory(processed_memory, conversations, _filter_model)
    fr_memory = local_memory.filter()
    # tag chats as memorized
    placeholders = ', '.join('?' for _ in ids) 
    cursor.execute(f"update chats set memorized = 1 where id in ({placeholders})", ids)
    conn.commit()
    await updater(conn, fr_memory, user_id)



async def updater(conn, memory, user_id):
    cursor = conn.cursor()
    # get existing chunks
    existing = cursor.execute('select local_id from memories where user_id = ?',(user_id,)).fetchall()
    exist_list = [k[0] for k in existing]
    # Remove deleted/updated chunks
    memory_exist = [x["id"] for x in memory if "updated" not in x]
    delete = [x for x in exist_list if x not in set(memory_exist)]

    if delete:
        placeholders = ', '.join('?' for _ in delete)
        cursor.execute(f'delete from memories where user_id = ? and local_id IN ({placeholders})',
           [user_id] + delete)
    # Compute embeddings (for new/edited embeddings)

    updated = [el["id"] for el in memory if el["id"] not in exist_list or "updated" in el]



    if updated:
        by_id = {el["id"]: el for el in memory}
        emb_base, emb_key, emb_model = _embedding_conf()
        emb = litellm.embedding(model=f"openai/{emb_model}", api_base=emb_base, api_key=emb_key, input=[by_id[k]["content"] for k in updated]) 
        # add new/updated chunks
        for i, indx in enumerate(updated):
            blob = np.array(emb["data"][i]["embedding"], dtype=np.float32).tobytes()
            cursor.execute("insert into memories (user_id, local_id, content, embed) VALUES (?, ?, ?, ?)",(user_id, indx, by_id[indx]["content"], blob))

    conn.commit()

import time
async def search(conn, user_id, query):
    """search"""
    start = time.perf_counter()
    
    cursor = conn.cursor()
    emb_base, emb_key, emb_model = _embedding_conf()
    emb = litellm.embedding(model=f"openai/{emb_model}", api_base=emb_base, api_key=emb_key, input="Instruct: Given a web search query, retrieve relevant passages that answer the query\nQuery: " + query)

    q = np.array(emb["data"][0]["embedding"], dtype=np.float32)
    q /= np.linalg.norm(q)  # belt-and-suspenders

    embeds = cursor.execute("select local_id, content, embed from memories where user_id = ?",(user_id,)).fetchall()
    scored = []
    for local_id, content, embed in embeds:
        vec = np.frombuffer(embed, dtype=np.float32)
        score = float(np.dot(q, vec))
        scored.append((score, local_id, content))
    scored.sort(key=lambda x: x[0], reverse=True)
    # Reranker grill

    prefilter = (get_settings().get("reranker", {}) or {}).get("chunks_limit", 10)
    scored=scored[:prefilter]
    if not scored:
        # new user with no memories: nothing to rerank, rerankers reject empty docs
        return []
    rr = _cohere_rerank(query, [k[2] for k in scored])

    end =time.perf_counter()
    print(f"Elapsed {end-start:.6f} seconds")


    results = [[scored[k["index"]][1],scored[k["index"]][2]] for k in rr]
    for result in results: 
        print(result)

    return results[:3]





def batch_scan(limit):
    import logging
    logger = logging.getLogger(__name__)
    conn = sqlite3.connect("./db.db", check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        cursor = conn.cursor()

        users_to_scan = cursor.execute("select id from users where (select count(*) from chats where user_id = users.id and (memorized = 0 or memorized is NULL)) >10").fetchall()
        for user in users_to_scan:
            try:
                asyncio.run(user_run(user[0], limit))
            except Exception:
                logger.exception("batch_scan failed for user %s", user[0])
    finally:
        conn.close()






if __name__ == "__main__":
    conn = sqlite3.connect("./db.db", check_same_thread=False)
    conn.row_factory = sqlite3.Row
    asyncio.run(user_run(1,-1))

    #while True:
    #    query = input("enter search query: ")
    #    asyncio.run(search(conn,1,query))

