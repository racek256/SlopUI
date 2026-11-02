from mcp import McpError
from litellm import experimental_mcp_client
from types import SimpleNamespace
import asyncio
import copy
import time
from .mcp_session import MCPsession

class Session:
    def __init__(self, session_id: str, user_id: int, mcp_configs:dict):
        self.session_id = session_id
        self.user_id = user_id
        self.mcp_configs = mcp_configs
        self.sessions: dict[str, MCPsession] = {}
        self.last_touched: float = time.monotonic()
        # Task that opened the MCP stacks; only it may close them.
        self._owner = None

    def touch(self):
        self.last_touched = time.monotonic()

    def _assert_owner(self):
        if self._owner is not None:
            assert asyncio.current_task() is self._owner, (
                "Session.close() must run in the task that opened the MCP stacks"
            )

    async def ensure_all(self):
        # Must run inside the SessionManager owner task: it opens stacks and
        # may close+reopen a dead one, all of which are task-affine.
        self._owner = asyncio.current_task()
        for name, cfg in self.mcp_configs.items():
            s = self.sessions.get(name)
            if s is None or s._stack is None or s.session is None:
                if s:
                    await s.close()
                s = MCPsession(self.user_id, name, cfg["command"], cfg["args"])
                await s.start()
                self.sessions[name] = s
                continue

            # A previously-good session can still have a dead transport if the
            # server closed its pipe; re-ping and rebuild so we never reuse it.
            try:
                await asyncio.wait_for(s.session.ping(), timeout=5.0)
            except Exception:
                await s.close()
                s = MCPsession(self.user_id, name, cfg["command"], cfg["args"])
                await s.start()
                self.sessions[name] = s
        self.touch()
    def all_tools(self) -> list:
        self.touch()
        result = []
        for mcp_name, s in self.sessions.items():
            for t in s.tools:
                copy_t = copy.deepcopy(t)
                copy_t["function"]["name"] = f"{mcp_name}_{t['function']['name']}"
                result.append(copy_t)
        return result
    async def execute(self, prefixed_name:str, arguments:dict):
        self.touch()
        for mcp_name, s in self.sessions.items():
            if prefixed_name.startswith(f"{mcp_name}_"):
                original = prefixed_name[len(mcp_name)+1:]
                tc = SimpleNamespace(
                        id="call_1",
                        function=SimpleNamespace(name=original, arguments=str(arguments)),
                        )
                tc = {
                        "id":"call_1",
                        "type":"function",
                        "function":{
                            "name": original,
                            "arguments": arguments,                            
                            }
                        }
                try:
                    return (await experimental_mcp_client.call_openai_tool(
                            session=s.session, openai_tool=tc
                            )).model_dump_json()
                except McpError as e:
                    return {
                            "error_type":"MCP_error",
                            "error_message":str(e)
                            }
        raise KeyError(f"No MCP in this session owns tool {prefixed_name}")

    async def close(self):
        self._assert_owner()
        for s in self.sessions.values():
            await s.close()
        self.sessions.clear()


