from litellm import completion, acount_tokens
import json
import os
import sqlite3
from stuff.settings import get_settings

SystemPrompt="""You are memory analysis system 
- your job will be to analyse conversation between user and assistant and return structured analysis and compacted conversation

# Conversation compaction 
you will analyse long conversations between user and assistant which is why you need to extremely compact their chat so they can be instantly analyzed by other systems 

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

- Each memory chunk will be held separately so it must hold its own context on its own so even without knowing context of the string you can understand it
- Use memory only when user mentions really valuable information


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
    "compaction":"answered question about rust",
}]

!KEEP EVERYTHING AS SHORT AS POSSIBLE LIKE IN THIS EXAMPLE this example is realistic and allowed use

# Extraction quality rules
- extract only high quality information that brings ongoing valuable information about user with relevant context
# critical rules
- keep everything extremely short
- always assign memory to correct and most relevant message and keep messages in same order as original chat 
- try to minimize amount of memory string while maximizing its value
- DO NOT SKIP ANY MESSAGES
- do not write duplicate memories
- only keep in memory information that will be relevant for a long time
- memory must hold context so even without context of the memory you know what it mens
"""
MEMORY_SCHEMA = {
    "type": "array",
    "items": {
        "type": "object",
        "properties": {
            "turn": {"type": "string", "enum": ["user", "assistant"]},
            "compaction": {"type": "string", "minLength": 1},
            "memory": {"type": "string", "maxLength": 200},
        },
        "required": ["turn", "compaction", "memory"],
        "additionalProperties": False,
    },
}
def _memory_conf():
    """Resolve memory provider config with safe fallbacks (never crashes on missing section)."""
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


def _register_memory_provider():
    conf = _memory_conf()
    provider = conf.get("provider")
    base_url = conf.get("base_url")
    api_key_env = conf.get("api_key_env")
    if not provider or not base_url:
        # Builtin LiteLLM provider: no registry entry needed; the api key
        # from api_key_env is passed explicitly in parser().
        return
    from litellm.llms.openai_like.json_loader import JSONProviderRegistry, SimpleProviderConfig
    JSONProviderRegistry._providers[provider] = SimpleProviderConfig(
        provider,
        {
            "base_url": base_url,
            "api_key_env": api_key_env or "",
        },
    )


def parser(model, history):
    conf = _memory_conf()
    if not model:
        model = conf.get("model")
    if not model:
        raise KeyError("memory.model missing: set memory.model in config.yaml")
    messages = [{"role": "system", "content": SystemPrompt}] + list(history) + [
        {"role": "user", "content": "<START_MEMORY>"}
    ]
    go_headers = {"x-opencode-session": "default", "User-Agent": "SlopUI/1.0"}
    api_key_env = conf.get("api_key_env")
    api_key = os.environ.get(api_key_env) if api_key_env else None
    api_base = conf.get("base_url")

    # top-level json_schema is the shape llama.cpp's OpenAI endpoint actually honors.
    # (nested json_schema under response_format is buggy on older builds — see #11988)
    common = {
        "model": model,
        "messages": messages,
        "extra_headers": go_headers,
        "temperature": 0,
        "extra_body": {"json_schema": MEMORY_SCHEMA},
    }
    if api_key:
        common["api_key"] = api_key
    if api_base:
        common["api_base"] = api_base

    response = completion(**common)
    content = response["choices"][0]["message"]["content"] or ""

    content = content.strip()
    if content.startswith("```"):
        content = content.split("\n", 1)[-1] if "\n" in content else content[3:]
        if content.startswith("json"):
            content = content[4:]
        content = content.rsplit("```", 1)[0]
    return json.loads(content)




# provider registry driven by config.yaml `memory:` section (see _register_memory_provider)
import logging
logger = logging.getLogger(__name__)

try:
    _register_memory_provider()
except Exception:
    logger.exception("memory provider registration failed")

# Testing importer




