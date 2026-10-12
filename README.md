<p align="center">
  <img src="frontend/src/Assets/logo.svg" alt="SlopUI" width="240" />
</p>

<p align="center">Self-hostable, open-source AI assistant.</p>

<p align="center">
  <img src="docs/hero-light.png#gh-light-mode-only" alt="SlopUI — Ask anything" width="800" />
  <img src="docs/hero-dark.png#gh-dark-mode-only" alt="SlopUI — Ask anything" width="800" />
</p>

<p align="center">
  <a href="https://slop.racek.xyz"><img src="https://img.shields.io/badge/Try%20it-%20slop.racek.xyz-00288e?style=for-the-badge" alt="Try SlopUI" /></a>
</p>

> [!NOTE]
> **SlopUI is under active development.** Expect breaking changes, rough edges, and occasional breakage — contributions, bug reports, and ideas are very welcome. Issues and pull requests are open.

## Try it out

**[→ slop.racek.xyz](https://slop.racek.xyz)**

- Due to privacy it requires signup, but all you need is a username and password

## Self-hosting

Want to run your own private AI assistant? See **[docs/SELFHOST.md](docs/SELFHOST.md)** for the full guide.

## Features

- Memory engine
    - The agent remembers everything important you ever tell it and automatically looks it up when needed
- Any model
    - Thanks to LiteLLM, swapping models and providers is effortless
- Mobile interface and app
    - SlopUI is optimized for mobile use and ships a PWA that looks just like any other Android app
- Free web search
    - Web search runs on your own SearXNG, with embeddings and reranking replacing the upstream providers
    - Upstream providers such as Tavily and Exa still work if you'd rather use them
- Fully local
    - You can self-host every part of this setup if you have the compute, for a fully local and private AI assistant

## Technologia

The memory engine is the most interesting part of this setup, split into three phases.

### 1. Parsing

- Once a user reaches a set amount of new chats, a cheap LLM analyzes and compacts all of those conversations, including suggestions for memory

### 2. Filtering

- After processing all conversations, another, preferably smarter, LLM gets:
    1. All compacted conversations with suggested memory updates from the parser
    2. All memory chunks already stored inside the database
- This agent is responsible for managing memory and deciding what to remember and what not. It gets a carefully crafted system prompt with instructions on what to remember, what to not, how to structure memories, how to remove old unwanted memories, and so on.

### 3. Search

The search pipeline for memory is really similar to the websearch pipeline:

1. Get the user's query
2. Get memories from the database
3. Run embedding search on them and choose the 10 closest matches
4. Run the reranker and choose the 3 most relevant memories
5. Those memories get injected into each user's message, without that being displayed to the user

### This was the crafting recipe for a fairly accurate memory engine

---

## Credits

### Stuff used
- [LiteLLM](https://github.com/BerriAI/litellm) 
- [SearXNG](https://github.com/searxng/searxng) 
- [Trafilatura](https://github.com/adbar/trafilatura) 
- [FastAPI](https://github.com/fastapi/fastapi) 
- [React](https://github.com/facebook/react) and [Vite](https://github.com/vitejs/vite)
- [MCP](https://github.com/modelcontextprotocol) 
- [NumPy](https://github.com/numpy/numpy) 

Created for Stardance Hackclub

