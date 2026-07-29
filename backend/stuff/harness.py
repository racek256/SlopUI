from litellm import completion, stream_chunk_builder
import json
import os 
from tavily import TavilyClient


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
            "name": "followup",
            "description": "give user simple followup question to select from premade answer feel free ",
            "parameters": {
                "type": "object",
                "properties": {
                    "question": {"type": "string", "description": "question for the user"},
                    "answers": {"type": "array", "description": "array of possible answers"}
                },
                "required": ["query"]
            }
        }
    }
]

tavily_client = TavilyClient(api_key=os.environ["TAVILY_API"])
def websearch(query):
    return tavily_client.search(query)

    

def harness(history,request, model):
    # main harness loop
    chain = []
    active = True
    while active:
        response = completion(model, messages= history + [ {"role":"user","content":request}] + chain, tools=tools, stream=True)
        chunks = []
        for chunk in response:
            chunks.append(chunk)
            delta = chunk['choices'][0]['delta']
            yield chunk

        response = stream_chunk_builder(chunks)
        message = response.choices[0].message 
        chain.append(message.model_dump(exclude_none=True))
        if message.tool_calls:
            print("Agent has called tool")
            for tool in message.tool_calls:
                args = json.loads(tool.function.arguments)
                
                match tool.function.name:
                    case "websearch":
                        data = websearch(args["query"])
                    case _:
                        data = "called tool does not exist"
                chain.append({"role":"tool", "tool_call_id":tool.id, "content": data})

        else:
            active = False


    return({
        "chain":chain,
        "response":chain[-1]["content"]
        })

    





    
harness([], input("enter your prompt: "), "ollama_chat/gemma4:e4b")
