import asyncio 
from .Session import Session

class SessionManager:
    def __init__(self, mcp_configs: dict, idle_timeout: float = 300.0):
        self.mcp_configs = mcp_configs
        self._sessions: dict[str, Session] = {}
        self._lock = asyncio.Lock()
        self.idle_timeout = idle_timeout

    async def create(self, user_id: int, session_id:int, mcp_configs: dict | None = None) -> Session:
        session = Session(session_id, user_id, mcp_configs or self.mcp_configs)
        async with self._lock:
            self._sessions[session_id] = session
        return session

    async def get(self, session_id: str) -> Session:
        async with self._lock:
            try:
                return self._sessions[session_id]
            except KeyError:
                return None

    def list_for_user(self, user_id:int) -> list[Session]:
        return [s for s in self._sessions.values() if s.user_id == user_id]

    async def close(self, session_id: str):
        async with self._lock:
            s = self._sessions.pop(session_id, None)
            if s:
                await s.close()

    async def close_for_user(self, user_id: int):
        async with self._lock:
            for sid in [sid for sid, s in self._sessions.items()
                        if s.user_id == user_id]:
                await self._sessions.pop(sid).close()

    async def close_all(self):
        async with self._lock:
            for s in list(self._sessions.values()):
                await s.close()
            self._sessions.clear()



