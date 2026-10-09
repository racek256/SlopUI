import litellm
import json
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
        while True:
            response = litellm.completion(self.model, history+chain, tools=tools, extra_headers=go_headers)
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



        
conversations = json.dumps("""{"type": "json_object", "messages": [{"turn": "user", "compaction": "nonsense", "memory": ""}, {"turn": "assistant", "compaction": "asked what to reason about", "memory": ""}, {"turn": "user", "compaction": "nonsense", "memory": ""}, {"turn": "assistant", "compaction": "acknowledged", "memory": ""}, {"turn": "user", "compaction": "asked what matrix multiplication is", "memory": ""}, {"turn": "assistant", "compaction": "explained matrix multiplication: row-column dot product rule, dimension match, non-commutativity, linear transformation composition", "memory": ""}]}
[{"turn":"user","compaction":"Question about matrix multiplication","memory":""},{"turn":"assistant","compaction":"Explained matrix multiplication","memory":""},{"turn":"user","compaction":"Asked to research freqtrade efficiency","memory":"User interested in freqtrade efficiency"},{"turn":"assistant","compaction":"Researched freqtrade efficiency","memory":""}]
[{
    "turn": "user",
    "compaction": "Asked to investigate benchmarks of space-bunny-free and identify the real model behind it",
    "memory": ""
},
{
    "turn": "assistant",
    "compaction": "Answered: space-bunny-free is an anonymous stealth model (1M ctx, video input, free), benchmark numbers mostly self-run/mixed, best lead MiniMax M3.1 via tokenizer fingerprint",
    "memory": "Space Bunny (free) is an anonymous stealth model; tokenizer fingerprinting points to MiniMax family, likely M3.1 — unconfirmed"
}]
{"type": "json_object", "messages": [{"turn": "user", "compaction": "Asked why Background React component still has left-to-right scale animation bug despite if-condition; shared code using ResizeObserver + useState number", "memory": "User works on React project with a 'Background' component that uses ResizeObserver and dynamically renders rotated gradient bars based on container width; has an 'expanded' prop toggling bar colors"}, {"turn": "assistant", "compaction": "Explained ResizeObserver fires per-frame during gradual width changes causing staggered bar appends (the wipe effect); gave 3 fixes: debounce updates, fixed bar pool sized once, or CSS repeating-linear-gradient; noted pitch is 60px not 56px and contentRect deprecated", "memory": ""}]}
[{"turn":"user","compaction":"Asked to convert alpha hex value to number (from #EA580C80)","memory":""},{"turn":"assistant","compaction":"Converted alpha 80 hex to 128/255 = 0.502 (~50%); gave rgba equivalents and JS formula","memory":""}]
[{"turn":"user","compaction":"Greeting","memory":""},{"turn":"assistant","compaction":"Greeted back, asked what user is doing","memory":""}]
[{
    "turn": "user",
    "compaction": "Asked what LangSmith is",
    "memory": ""
},
{
    "turn": "assistant",
    "compaction": "Explained LangSmith: LangChain's tracing/eval/prompt-manage/deploy platform, framework-agnostic, pricing tiers",
    "memory": ""
}]
{"messages":[{"turn":"user","compaction":"asks when Spider-Man Brand New Day releases online","memory":"User follows Spider-Man: Brand New Day release info"},{"turn":"assistant","compaction":"gave theatrical/PVOD/Netflix dates, unconfirmed by Sony","memory":"Brand New Day: theaters Jul 31 2026, PVOD ~Oct 6 2026, Netflix ~late Nov 2026"},{"turn":"user","compaction":"asks if PVOD release gets torrented same day","memory":"User interested in torrent/pirate availability of movies"},{"turn":"assistant","compaction":"explained piracy release stages CAM to WEB to remux","memory":""},{"turn":"user","compaction":"asks if physical release already torrented","memory":""},{"turn":"assistant","compaction":"explained disc is pre-order only, placeholder date","memory":"Brand New Day physical release tentative Nov 17 2026"},{"turn":"user","compaction":"asks when next multiverse Spider-Man comes","memory":""},{"turn":"assistant","compaction":"answered Beyond the Spider-Verse June 18 2027 plus other Spidey projects","memory":"Spider-Man: Beyond the Spider-Verse releases June 18 2027"},{"turn":"user","compaction":"asks what Spider-Noir is and who made it","memory":""},{"turn":"assistant","compaction":"explained Spider-Noir: Sony/Amazon series, Cage, May 2026, canceled after 1 season","memory":"Spider-Noir: Sony/Amazon series with Nicolas Cage, released May 2026, canceled after one season"}]}
[{
    "turn": "user",
    "compaction": "Question about Epic Games Linux dev status",
    "memory": "User interested in Epic Games Linux development"
},
{
    "turn": "assistant",
    "compaction": "Answered Epic Games Linux status: native client soon, EAC user-space, Fortnite denied, Rocket League works",
    "memory": ""
},
{
    "turn": "user",
    "compaction": "Questioned Linux anti-cheat kernel absence, mentions DKMS",
    "memory": "User has knowledge of Linux kernel modules and DKMS"
},
{
    "turn": "assistant",
    "compaction": "Explained Linux kernel anti-cheat barriers: DKMS needs source, no universal signing, GPL taint, user is root; eBPF/attestation paths",
    "memory": ""
},
{
    "turn": "user",
    "compaction": "Asked who develops EAC",
    "memory": ""
},
{
    "turn": "assistant",
    "compaction": "Answered EAC ownership: Epic Games since 2018, originally Finnish devs, renamed Kamu",
    "memory": ""
}]
[{
    "turn": "user",
    "compaction": "Asked if freqtrade strategies need scrapers",
    "memory": ""
},
{
    "turn": "assistant",
    "compaction": "Explained scrapers only needed for data outside exchange API, via informative_pairs/FreqAI/confirm_trade_entry; warned about lookahead bias in backtests",
    "memory": ""
}]
1350""")


from litellm.llms.openai_like.json_loader import JSONProviderRegistry, SimpleProviderConfig

JSONProviderRegistry._providers["opencode-go"] = SimpleProviderConfig(
    "opencode-go",
    {
        "base_url": "https://opencode.ai/zen/go/v1",
        "api_key_env": "OPENCODE_GO_API_KEY",
    },
)


#memory_chunks = []
#local_memory = memory(memory_chunks, conversations, "opencode-go/deepseek-v4-flash")
#print(local_memory.filter())

