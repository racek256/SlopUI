import asyncio 
from contextlib import AsyncExitStack
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from litellm import experimental_mcp_client

class MCPsession:
    def __init__(self, user_id: int, mcp_name: str, command: str, args):
        self.user_id = user_id
        self.mcp_name = mcp_name
        self.server_params = StdioServerParameters(command=command,args=args)
        self._stack = None
        self.session = None
        self.tools = None
        self.last_used = 0

    async def start(self):
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
        self.last_used = asyncio.get_running_loop().time()
    async def close (self):
        if self._stack is not None:
            await self._stack.aclose()
            self._stack = None
            self.session = None
            self.tools = None


