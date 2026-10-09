from litellm import completion, acount_tokens
import json
import sqlite3

SystemPrompt="""You are memory analysis system 
your job will be to analyse conversation between user and assistant and return structured analysis and compacted conversation

# Conversation compaction 
you will analysie long conversations between user and assistant which is why you need to extremely compact their chat so they can be instantly analyzed by other systems 

Example: 
user: Can you explain how ownership, borrowing, and the borrow checker actually work in Rust? I keep hitting "cannot borrow as mutable" errors and I understand that they happen, but I don't get why the compiler enforces these rules. Walk me through the three rules (one writer OR many readers, never while someone's reading/writing), tie them to memory safety, and give me a small code example where I'd get a borrow error and how to fix it. Bonus: explain Rc/Arc and Cell/RefCell as the escape hatches when the borrow checker says no.
Compacted: Question about rust ownership rules
Assistant: sure its actually quite simple...
Compacated: Answer to users question

# Memory Extraction
Alongside ultra compacting conversations you will extract Key memories from users or Assistants responses it must remember 

Example:
user: i love potatos
extraction "user loves potatos"
quite simple but you need to extract the comacted key memory peice only while keeping it understandable

# Content you will receive
you will see entire conversation between you and user only user/assistant turns
last thing you will receive is prompt <START_MEMORY>
this means your next response will be the memory analysis nothign else

# Response Structure
Your response must be strictly JSON in this exact format
- every message must have separate tag both users and assistants

[{
    "turn":"user",
    "compaction":"Question about Rust",
    "memory":"User loves rust"
},
{
    "turn":"assistant",
    "compaction":"answered question",
    "memory":""
}]

!KEEP EVERYTHING AS SHORT AS POSSIBLE LIKE IN THIS EXAMPLE this example is realistic and allowed use

# Extraction quality rules
- you don't need to extract memory at all if nothing worth remembering is present in message less memories = better if you decide not to remember anything keep the memory empty string
- compaction must be provided for every message but if it contains nonesense or you dont understand it just enter "nonesense" as compaction string

# critical rules
- keep everything super short compaction doesn't need full context
- keep only genuenly usefull information
- info from assistant is not needed that much so remembering that is beneficial only if he mentiones something critical
- always assign memory to correct and most relevant message and keep messages in same order as original chat 
- remember as little as possible
- DO NOT SKIP ANY MESSAGES
- do not write duplicate memories even when message is mentioned multiple times
- do not remember single time user things single time question only keep in memory information that will be relevant for a long time
- memory must hold context so even without context of the memory you know what it mens
"""


def parser(model, history):
    history.insert(0,{
        "role":"system",
        "content":SystemPrompt
        })
    history.append({
        "role":"user",
        "content":"<START_MEMORY>"
        })
    go_headers = {"x-opencode-session": str("default"), "User-Agent": "SlopUI/1.0"}
    response = completion(model, history, extra_headers=go_headers)
    #print(response["choices"][0]['message']['content'])
    return json.loads(response["choices"][0]['message']['content'])





# config stealer
import logging
logger = logging.getLogger(__name__)
from litellm.llms.openai_like.json_loader import JSONProviderRegistry, SimpleProviderConfig

JSONProviderRegistry._providers["opencode-go"] = SimpleProviderConfig(
    "opencode-go",
    {
        "base_url": "https://opencode.ai/zen/go/v1",
        "api_key_env": "OPENCODE_GO_API_KEY",
    },
)

# Testing importer




