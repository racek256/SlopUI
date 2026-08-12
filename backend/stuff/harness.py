from stuff.tools.webfetch import webfetch
from litellm import completion, stream_chunk_builder
from tavily import TavilyClient
import json
import os 
from stuff.tools.websearch import websearch 
from litellm.llms.openai_like.json_loader import JSONProviderRegistry, SimpleProviderConfig

JSONProviderRegistry.load()  # ensure existing ones are loaded first
JSONProviderRegistry._providers["opencode-zen"] = SimpleProviderConfig(
    "opencode-zen",
    {
        "base_url": "https://opencode.ai/zen/v1",
        "api_key_env": "OPENCODE_ZEN_API_KEY",
    },
)

JSONProviderRegistry.load()  # ensure existing ones are loaded first
JSONProviderRegistry._providers["opencode-go"] = SimpleProviderConfig(
    "opencode-go",
    {
        "base_url": "https://opencode.ai/zen/go/v1",
        "api_key_env": "OPENCODE_GO_API_KEY",
    },
)
tools = [
    {
        "type": "function",
        "function": {
            "name": "websearch",
            "description": "Get up to date information from search engine",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "your search query"}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "websearch-beta",
            "description": "newer version of websearch still in development",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "your search query"}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "webfetch",
            "description": "fetches all data from webpage and returns content in markdown",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "url of any page"}
                },
                "required": ["url"]
            }
        }
    }

    ]

tavily_client = TavilyClient(api_key=os.environ["TAVILY_API"])
def websearchold(query):
    for x in range(2):
        try:
            return tavily_client.search(query)
        except:
            pass
    return {
            "message":"Websearch failed please try again later"
            }


    

def harness(history,request, model):
    # main harness loop
    chain = []
    active = True
    while active:
        messages = history + ([{"role":"user","content":request}] if request else []) + chain
        for msg in messages:
            if msg.get("role") == "assistant" and "reasoning_content" not in msg:
                msg["reasoning_content"] = ""
        print(messages)
        print("Starting round of harness")
        response = completion(model, messages, tools=tools, stream=True)
        chunks = []
        for chunk in response:
            chunks.append(chunk)
            delta = chunk['choices'][0]['delta']
            print(delta)
            yield delta.model_dump_json() + "\n"

        response = stream_chunk_builder(chunks)
        message = response.choices[0].message 
        chain.append(message.model_dump(exclude_none=True))

        if message.tool_calls:
            for tool in message.tool_calls:
                print(f"Agent has called tool {tool.function.name}")
                print(tool.function.arguments)
                args = json.loads(tool.function.arguments)
                match tool.function.name:
                    case "websearch-beta":
                        data = websearch(args["query"]) 
                        print(data)
                    case "websearch":
                        data = websearchold(args["query"])
                        print(data)
                    case "webfetch":
                        data = webfetch(args["url"])
                    case _:
                        data = "called tool does not exist"
                chain.append({"role":"tool", "tool_call_id":tool.id, "content": json.dumps(data)})

        else:
            active = False


    return({
        "chain":chain,
        "content":chain[-1]["content"]
        })


system_prompt = """You are a title classifier. Read the user's message and output a short title summarizing it.

Rules:
- Output ONLY the title, nothing else (no quotes, no punctuation at the end, no preamble like "Title:")
- 1-4 words, shorter is better
- Not a full sentence — a label, like a tab title or search query
- Match the language of the input (Czech in, Czech title; English in, English title)
- Never leave it looking cut off mid-word
"""

def title(content):
    response = completion("openrouter/google/gemini-2.5-flash-lite", messages=[{"role":"system", "content":system_prompt},{"role":"user","content":content}]) 
    return(response.choices[0].message["content"])






    
