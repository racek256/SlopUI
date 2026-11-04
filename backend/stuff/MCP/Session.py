from mcp import McpError
from litellm import experimental_mcp_client
from types import SimpleNamespace
import asyncio
import copy
import logging
import time
from .mcp_session import MCPsession

logger = logging.getLogger(__name__)

class Session:
    def __init__(self, session_id: str, user_id: int, mcp_configs: dict, home):
        self.session_id = session_id
        self.user_id = user_id
        self.mcp_configs = mcp_configs
        self.home = home  # the SessionManager owning the home loop
        self.sessions: dict[str, MCPsession] = {}
        self.created = time.monotonic()  # ordering key for FILO teardown
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
        # Must run inside the home owner task: it opens stacks and may
        # close+reopen a dead one, all of which are task-affine.
        self._owner = asyncio.current_task()
        # Upstream mcp bug (python-sdk #577): with more than one stdio stack
        # alive, closing out of FILO (newest-first) order cascades anyio
        # cancel-scope errors. So if ANY server is dead, tear down every
        # session newest-first and rebuild everything.
        broken = []
        for name, cfg in self.mcp_configs.items():
            s = self.sessions.get(name)
            if s is None or s._stack is None or s.session is None:
                broken.append((name, cfg))
                continue
            try:
                await asyncio.wait_for(s.session.send_ping(), timeout=5.0)
            except Exception:
                broken.append((name, cfg))
        if broken:
            for s in reversed(list(self.sessions.values())):
                try:
                    await s.close()
                except Exception:
                    logger.exception("Error closing MCP session %r during teardown", s.mcp_name)
            self.sessions.clear()
            for name, cfg in self.mcp_configs.items():
                s = MCPsession(self.user_id, name, cfg["command"], cfg["args"])
                await s.start()
                self.sessions[name] = s
        self.touch()

    def all_tools(self) -> list:
        # Pure read of cached tool dicts - safe from any thread/loop.
        self.touch()
        result = []
        for mcp_name, s in self.sessions.items():
            for t in s.tools:
                copy_t = copy.deepcopy(t)
                copy_t["function"]["name"] = f"{mcp_name}_{t['function']['name']}"
                result.append(copy_t)
        return result

    async def execute(self, prefixed_name: str, arguments: dict):
        """Tool execution hops to the home loop: the MCP SDK streams/stacks
        live there, and anyio memory streams may not be touched cross-loop."""
        self.touch()
        return await self.home.submit("execute", (self.session_id, prefixed_name, arguments))

    async def run_tool(self, prefixed_name: str, arguments: dict):
        """Runs inside the home owner task via the manager's execute op."""
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
        # Newest stack first (mcp python-sdk #577: FIFO teardown fails).
        for s in reversed(list(self.sessions.values())):
            try:
                await s.close()
            except Exception:
                logger.exception("Error closing MCP server %s", s.mcp_name)
        self.sessions.clear()
