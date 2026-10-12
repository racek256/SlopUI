import litellm
import json
import os
from stuff.settings import get_settings


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
        # Builtin LiteLLM provider: no registry entry needed; credentials
        # from api_key_env are passed explicitly in filter().
        return
    from litellm.llms.openai_like.json_loader import JSONProviderRegistry, SimpleProviderConfig
    JSONProviderRegistry._providers[provider] = SimpleProviderConfig(
        provider,
        {
            "base_url": base_url,
            "api_key_env": api_key_env or "",
        },
    )
SystemPrompt = """You are memory filter system 
your job is to take existing memory + new memory and cleanup/manage/edit memory to stay efficent and unbloated

from user you will receive existing memory chunks with:
- timestamp
- content

you will also receive new unprocessed potentional memory chunks including their compacted conversations 
those memory chunks are auto detected and may include unwanted/useless information thats why you exist

in summary:
# INPUT
{existing memory chunks}
{compacted conversations with suggested memory chunks}
# Your task 
you are given multiple tools to work with 
- add - adds memory chunk to permanent memory
- remove - remove existing memory chunk cause its no longer needed
- edit - edit existing chunk to merge/update information

# your job
your main job is keeping most important information focused around user to be able to help him in future conversations even more and create personalized enviroment 

# system information

- compacted conversations you receive are not yet stored you must decide yourself if you want to keep any of memory chunks and manually add them with ADD tool or include them in existing relevant memory chunk with edit tool 
- if new memory chunk contradicts with existing one you can remove the existing one 
- if existing memory chunks are mess you can also edit/merge or manage them 

you will work with tools provided and you can't ask any questions


keep memory under 100 memory chunks if it ever reaches such a high amount do drastic memory cleanup with merging and removing old or unrelevant memory


- memory managment is your responsibility so you are responsible for quality of stored messages 
- you store only chunks that hold enough information to be usefull in future conversations with user 
- you filter out unneeded information
- feel free to reformulate edit or remove even existing memory chunks


# Lookup roles ( list of rules to ensure memories usable for future lookup)
- Never rely on a brand/model/project name alone to say what something is. ( MOST IMPORTANT RULE!!! )

- ONE topic per chunk. Never mix unrelated facts. Merge only chunks about the same thing. 
- Start with the subject in plain everyday words, then details:
  "User's laptop is a ThinkPad L480 ...", "User's home server runs ...",
  "User's diet: vegetarian since 2024 ...", "User's school: ...".
- Use the common word AND the specific name: "laptop (ThinkPad L480)",
  "note-taking app Obsidian", "chat server Matrix Synapse".
- 1-3 sentences, under ~60 words. If it needs more, it is two topics.
- Write in English, even if the conversation was in Czech. Keep Czech proper
  nouns (Kounicova, maturita) as they are.
- Keep durable facts: who the user is, what they own, use, study, build,
  prefer, can't do (allergies, diet, disabilities), and their ongoing goals.
- Drop transient details: exact package/BIOS versions, one-off errors that
  were already solved, prices on a given day, what the assistant suggested
  unless the user adopted it.
- If a new fact updates an old one, EDIT the old chunk (don't add a second
  chunk about the same thing). If it contradicts it, keep only the newer fact.
- Before adding, check whether a chunk about that subject already exists;
  if yes, edit it instead.


- If you notice problems with existing memories feel free to edit them to follow all rules your job is not only to manage new entries but also old and existing ones
"""



tools = [
    {
        "type": "function",
        "function": {
            "name": "add",
            "description": "create new permanent memory chunk",
            "parameters": {
                "type": "object",
                "properties": {
                    "content": {"type": "string" , "description": "content of this memory chunk keep it short"}
                },
                "required": ["content"]
            }
        }
    },
    {
        "type":"function",
        "function":{
            "name":"remove",
            "description":"remove existing memory chunk",
            "parameters":{
                "type":"object",
                "properties":{
                    "id":{"type":"integer", "description":"id of memory chunk you want to remove"}
                    }
                }
            }
    },
    {
        "type":"function",
        "function":{
            "name":"edit",
            "description":"rewrite existing memory chunk",
            "parameters":{
                "type":"object",
                "properties":{
                    "id":{"type":"integer", "description":"id of memory chunk you want to edit"},
                    "content":{"type":"string", "description":"new content of edited memory chunk"}
                    }
                }
            }
    },
    {
        "type":"function",
        "function":{
            "name":"list",
            "description":"lists current state of stored memory once again"
            }
    }
    ]



class memory:
    def __init__(self, chunks, conversations, model):
        self.memory = chunks
        self.conversations = conversations
        self.model = model
    def add(self,args):
        """adds new memory chunk into memory"""
        id = (self.memory[len(self.memory)-1]["id"]  + 1 ) if self.memory else 0
        self.memory.append({
            "id":id,
            "content":args["content"]
            })
        return f"chunk created with id {id}"
    def remove(self,args):
        """removes memory chunk from memory"""
        exists = any(d.get("id") == args["id"] for d in self.memory)
        if exists:
            self.memory = [d for d in self.memory if d["id"] != args["id"]]
        else:
            return f"chunk with id: {args["id"]} doesn't exist"
        return f"chunk with id: {args["id"]} was succesfully removed"

    def edit(self, args):
        exists = any(d.get("id") == args["id"] for d in self.memory)
        if exists:
            for chunk in self.memory:
                if chunk["id"] == args["id"]:
                    chunk["content"] = args["content"]
                    chunk["updated"] = True
                    break
        else:
            return f"chunk with id: {args["id"]} was not found"
        return f"chunk with id: {args["id"]} was succesfully edited"
    def list(self):
        return str(self.memory)
    def filter(self):
        """filter memory and add new chunks"""
        go_headers = {"x-opencode-session": str("kfjdlshefjdaj"), "User-Agent": "SlopUI/1.0"}
        history = self.construct_conv()
        chain = []
        conf = _memory_conf()
        _api_key_env = conf.get("api_key_env")
        _api_key = os.environ.get(_api_key_env) if _api_key_env else None
        _api_base = conf.get("base_url")
        _kwargs = {}
        if _api_key:
            _kwargs["api_key"] = _api_key
        if _api_base:
            _kwargs["api_base"] = _api_base
        while True:
            response = litellm.completion(self.model, history+chain, tools=tools, extra_headers=go_headers, **_kwargs)
            message = response.choices[0].message 
            chain.append(message.model_dump(exclude_none=True))
            if message.tool_calls:
                for tool in message.tool_calls:
                    args = json.loads(tool.function.arguments)
                    result = ""
                    print(tool.function.name)
                    match tool.function.name:
                        case "add":
                            result = self.add(args)
                        case "remove":
                            result = self.remove(args)
                        case "edit":
                            result = self.edit(args)
                        case "list":
                            result = self.list()
                        case _:
                            result = "unknown tool called"
                    chain.append({"role":"tool", "tool_call_id":tool.id,"content": result})
            else:
                print(message)
                print("finished")
                break
        return self.memory

    def construct_conv(self):
        history = [{"role":"system","content":SystemPrompt},]
        userPrompt = f"""Existing memory chunks:
        {self.memory if self.memory else "memory is empty"}
        suggested memory conversations:
        {self.conversations}
        Start Processing memory after you are done respond with exactly <MEMORY_FILTERED>
        """
        history.append({
            "role":"user",
            "content":userPrompt
            })
        return history
   




        

from litellm.llms.openai_like.json_loader import JSONProviderRegistry  # noqa: F401 (re-export for existing importers)
import logging as _logging

try:
    _register_memory_provider()
except Exception:
    _logging.getLogger(__name__).exception("memory provider registration failed")


