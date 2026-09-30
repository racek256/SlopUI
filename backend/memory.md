# Memory system

# conversation parser
- after conversation with AI sits idle for some time its scanned with conversation parser
- conversation parser will be super cheap maybe even none reasoning LLM 
- conversation that its parsing will already have its reasoning and files filtered out
- parsers job:
    - reads entire conversation 
    - converts every prompt/response to single line summary + memory chunks eg:
        - user: question about trading bots. 
            - memory: ["user is curious about trading bots"]
- decisions:
    - can this run without seeing entire conversation but only one turn?
    - is it cheap enough?
    - is it actually good?
# memory filter
- after conversation parser memory chunks are for some time stored marked as unfinished just so lookups can quickly use them 
- memory filter runs on a schedule once unfinished memory accumulates 
- memory filter is also LLM but this time smarter than conversation parser
- it gets all memory chunks into context 
- its job is to compress,delete,edit,rewrite memory chunks to improve lookup quality
    - it also holds link to compressed conversation which it can look up at any time 
    - it can also view original message or turn of conversation when its really unsure about chunk of memory
- decisions:
    - is it cheap enough?
    - is it actually good? 
    - am i on fent?

# Search System
- nothing special 
- pipeline:
    - chunk messages
    - embed messages
    - cutoff unrelevant chunks
    - rerank chunks
    - Inject those memory chunks into end of user prompt marked as user_data
- Query: Each prompt
- decision: 
    - openrouter is fucking slow for embedding and reranking so much even local GPU is faster. But deployment target doesn't have GPU so openrouter is only option but searching memory on each prompt is gonna hurt both speed and cost.
        - messages can be embeded before lookup.
            - works but rerank is still slow
        - Keep memory search only as harness tool.
            - works but it defeats the porpuse of memory system.
        - fully skip reranking.
            - works but performance can be questionable needs benchmarks.

# Architecture solutions
- memory chunk must be injected in deterministic way to not pop cache 
    - include memory chunks inside messages table in DB directly so they can be rebuilt without displaying to user
# additional decisions
- should main agent have tool for memory lookup or should it be kept to harness?
- should main agent get tool that allows it to browser other session turns if memory chunk points to it?


