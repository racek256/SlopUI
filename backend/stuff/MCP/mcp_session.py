import asyncio 
import os
import time
from contextlib import AsyncExitStack
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from litellm import experimental_mcp_client

class MCPsession:
    def __init__(self, user_id: int, mcp_name: str, command: str, args):
        self.user_id = user_id
        self.mcp_name = mcp_name
        # NOTE: the MCP SDK only inherits a safelist (HOME, PATH, ...) into
        # subprocesses, so pass the full server environ (populated from .env
        # via load_dotenv) through to every MCP server.
        self.server_params = StdioServerParameters(command=command,args=args,env=dict(os.environ))
        self._stack = None
        self.session = None
        self.tools = None
        self.last_used = 0
        # Task that entered the AsyncExitStack; only it may exit the stack.
        self._owner = None

    async def start(self):
        # enter_async_context opens anyio task groups: remember the task so
        # close() can never exit the stack from a different one.
        self._owner = asyncio.current_task()
        self._stack = AsyncExitStack()

        read, write = await self._stack.enter_async_context(
                stdio_client(self.server_params)
                )
        self.session = await self._stack.enter_async_context(
                ClientSession(read,write)
                )
        await self.session.initialize()
        self.tools = await experimental_mcp_client.load_mcp_tools(
                session=self.session, format="openai"
                )
        self.last_used = time.monotonic()
    async def close (self):
        if self._stack is not None:
            # Exiting a scope from another task spins anyio's cancellation
            # delivery forever, so refuse loudly instead.
            assert asyncio.current_task() is self._owner, (
                "MCPsession.close() must run in the task that opened it"
            )
            await self._stack.aclose()
            self._stack = None
            self.session = None
            self.tools = None

