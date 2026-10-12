import asyncio
import logging
import time
from .Session import Session

logger = logging.getLogger(__name__)

class SessionManager:
    def __init__(self, mcp_configs: dict, idle_timeout: float = 300.0):
        self.mcp_configs = mcp_configs
        self._sessions: dict[str, Session] = {}
        self._lock = asyncio.Lock()
        self.idle_timeout = idle_timeout

    async def create(self, user_id: int, session_id: int, mcp_configs: dict | None = None) -> Session:
        session = Session(session_id, user_id, mcp_configs or self.mcp_configs)
        async with self._lock:
            self._sessions[str(session_id)] = session
        return session

    async def get(self, session_id: str) -> Session:
        async with self._lock:
            try:
                return self._sessions[str(session_id)]
            except KeyError:
                return None

    def list_for_user(self, user_id: int) -> list[Session]:
        return [s for s in self._sessions.values() if s.user_id == user_id]

    async def touch(self, session_id: str):
        async with self._lock:
            s = self._sessions.get(str(session_id))
            if s is not None:
                s.touch()

    async def reap_idle(self, now=None) -> int:
        if now is None:
            try:
                now = asyncio.get_event_loop().time()
            except RuntimeError:
                now = time.monotonic()
        async with self._lock:
            expired = [sid for sid, s in self._sessions.items()
                       if now - s.last_touched > self.idle_timeout]
            sessions = [self._sessions.pop(sid) for sid in expired]
        for s in sessions:
            try:
                await s.close()
            except Exception:
                logger.exception("Error closing idle session")
        return len(sessions)

    async def close(self, session_id: str):
        async with self._lock:
            s = self._sessions.pop(str(session_id), None)
        if s:
            await s.close()

    async def close_for_user(self, user_id: int):
        async with self._lock:
            expired = [sid for sid, s in self._sessions.items()
                       if s.user_id == user_id]
            sessions = [self._sessions.pop(sid) for sid in expired]
        for s in sessions:
            await s.close()

    async def close_all(self):
        async with self._lock:
            sessions = list(self._sessions.values())
            self._sessions.clear()
        for s in sessions:
            await s.close()
