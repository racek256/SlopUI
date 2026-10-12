# Self-hosting SlopUI

Run the whole thing yourself: frontend, backend, database, and optionally your own web search.

## Requirements

- Python 3.14+, Node.js 20+, and an API key for any [LiteLLM](https://github.com/BerriAI/litellm)-supported provider
- Docker, only if you want your own SearXNG search

No database server — SlopUI uses a local SQLite file.

## Quick start

```bash
git clone https://github.com/racek256/SlopUI && cd SlopUI
cp .env.example .env
cp backend/config.yaml.example backend/config.yaml
```

Set a `SECRET` in `.env` (`openssl rand -hex 32`) and your provider key, then:

```bash
cd backend && pip install -r requirements.txt pyyaml && python main.py
```

In a second terminal:

```bash
cd frontend && npm install && npm run dev
```

Open **http://localhost:5173** and sign up. The database is created automatically on first run.

> Run the backend from inside `backend/`. The database, `init.sql`, and `.env` are all resolved relative to the working directory.

## Web search

Either your own SearXNG:

```bash
cd searxng && docker compose up -d    # serves on 127.0.0.1:8888
```

…or a hosted provider, in `.env`:

```bash
SEARCH_PROVIDER=remote
TAVILY_API=...        # or EXA_API=...
```

## Models

```yaml
# backend/config.yaml
models:
  - provider: openrouter
    format: builtin
    api_key_env: OPENROUTER_API_KEY
    models: [{id: "openrouter/qwen/qwen3.7-flash", name: "Qwen 3.7 flash"}]

  - provider: my-provider              # anything OpenAI-compatible
    baseURL: https://example.com/v1
    format: openai
    api_key_env: MY_PROVIDER_API_KEY
    models: [{id: "my-provider/some-model", name: "Some Model"}]
```

`api_key_env` is the *name* of a variable in `.env`, not the key itself. Models listed here appear in the UI picker.

## Embeddings and reranking

Only used with local search. Both take any compatible endpoint, so you are not locked to one vendor.

```yaml
# backend/config.yaml
embedding:
  baseURL: "https://openrouter.ai/api/v1"
  api_key_env: "EMBEDDING_API_KEY"
  model: "perplexity/pplx-embed-v1-0.6b"
  search_limit: 20

reranker:
  baseURL: "https://openrouter.ai/api/v1"
  api_key_env: "RERANKER_API_KEY"
  model: "cohere/rerank-4-fast"
  chunks_limit: 35
```

- **Embedding** — any OpenAI-compatible `/embeddings` endpoint
- **Reranker** — any Cohere-compatible `/rerank` endpoint

Put the values in `.env`:

```bash
EMBEDDING_API_KEY=...
RERANKER_API_KEY=...
```

## Demo mode and MCP

```yaml
# backend/config.yaml
app:
  demo_mode: "true"     # quoted — compared as a string

MCPS:
  - name: my-tools
    command: "/absolute/path/to/server"    # must be absolute
    args: [mcp]
```

Restart the backend after editing `config.yaml`.

## Troubleshooting

| Symptom | Cause |
|---|---|
| `FileNotFoundError: init.sql` | started from the wrong directory — `cd backend` |
| `ModuleNotFoundError: yaml` | `pip install pyyaml` |
| Web search returns nothing | `SEARCH_PROVIDER=local` and SearXNG up on port 8888 |
| `KeyError` about an API key | the variable named in `api_key_env` is empty in `.env` |
| No model in the picker | `models:` is empty or malformed in `config.yaml` |
| Frontend can't reach the API | backend not on port 8000, or not started from `backend/` |

## License

Do what the fuck you want to public license. See [LICENSE](../LICENSE).
