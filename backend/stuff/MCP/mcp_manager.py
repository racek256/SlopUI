import asyncio
import logging
import time
from .Session import Session

logger = logging.getLogger(__name__)


class SessionManager:
    """Registry of per-chat MCP sessions.

    anyio task groups and AsyncExitStack scopes are task-affine: a scope must be
    exited by the task that entered it. Request tasks die, so a session opened
    inside a request can never be closed by the reaper or by shutdown. Every
    stack operation (start / aclose) therefore runs inside one long-lived owner
    task; callers only enqueue an op and await its future. Waiting on that
    future from any task is legal - only the stack exit itself is task-bound.
    """

    def __init__(self, mcp_configs: dict, idle_timeout: float = 300.0):
        self.mcp_configs = mcp_configs
        self._sessions: dict[str, Session] = {}
        self._lock = asyncio.Lock()
        self.idle_timeout = idle_timeout
        self._ops: asyncio.Queue = asyncio.Queue()
        self._owner_task: asyncio.Task | None = None
        self._owner: asyncio.Task | None = None
        # True once shutdown() starts: _submit must fail fast instead of
        # resurrecting the owner on a dying loop (e.g. reload races).
        self._shutting_down = False

    # ---- owner task plumbing -------------------------------------------------

    async def startup(self):
        """Start the owner task. Called from the app lifespan."""
        if self._owner_task is not None and not self._owner_task.done():
            return
        self._shutting_down = False
        self._ops = asyncio.Queue()
        self._owner = None
        self._owner_task = asyncio.create_task(self._owner_loop(), name="mcp-owner")
        # Round-trip one op so the owner has recorded itself before we return.
        await self._submit("noop")

    async def shutdown(self):
        """Close every session inside the owner task, then stop the owner."""
        self._shutting_down = True
        task = self._owner_task
        if task is None or task.done():
            self._owner_task = None
            return
        try:
            await self._submit("close_all")
        except Exception:
            logger.exception("MCP owner failed to close sessions during shutdown")
        self._owner_task = None
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

    async def _owner_loop(self):
        self._owner = asyncio.current_task()
        try:
            while True:
                op, payload, fut = await self._ops.get()
                if fut.cancelled():
                    continue
                try:
                    result = await self._run_op(op, payload)
                except asyncio.CancelledError:
                    # Shutdown cancel: the owner must die with the loop.
                    if self._shutting_down:
                        raise
                    # Stray cancellation mid-life (e.g. an op cancelled from
                    # outside while the owner itself was never asked to stop).
                    # Ending the task here would strand every future submit, so
                    # fail this op loudly and keep the owner alive instead.
                    logger.exception("MCP owner op %r cancelled unexpectedly; owner continues", op)
                    if not fut.done():
                        fut.set_exception(asyncio.CancelledError("mcp owner op cancelled"))
                    continue
                except Exception as exc:
                    if not fut.done():
                        fut.set_exception(exc)
                else:
                    if not fut.done():
                        fut.set_result(result)
        finally:
            self._owner = None

    async def _submit(self, op: str, payload=None):
        task = self._owner_task
        if task is None or task.done():
            if self._shutting_down:
                raise RuntimeError("MCP session owner task is not running")
            # Owner died mid-life (never during a clean shutdown): revive it
            # so one stray failure can't strand every future MCP call.
            # Serialized on the dict lock; no caller holds it across _submit.
            async with self._lock:
                task = self._owner_task
                if task is None or task.done():
                    logger.warning("MCP owner task dead, restarting it for op %r", op)
                    await self.startup()
        fut = asyncio.get_running_loop().create_future()
        self._ops.put_nowait((op, payload, fut))
        return await fut

    async def _run_op(self, op: str, payload):
        if op == "noop":
            return None
        if op == "ensure_ready":
            return await self._ensure_ready(*payload)
        if op == "close":
            await payload.close()
            return None
        if op == "close_all":
            async with self._lock:
                sessions = list(self._sessions.values())
                self._sessions.clear()
            for s in sessions:
                try:
                    await s.close()
                except Exception:
                    logger.exception("Error closing MCP session")
            return len(sessions)
        raise ValueError(f"unknown MCP owner op: {op!r}")

    async def _ensure_ready(self, session_id, user_id) -> Session:
        """Runs in the owner task: get-or-create, ping/rebuild, touch."""
        sid = str(session_id)
        async with self._lock:
            session = self._sessions.get(sid)
            if session is None:
                session = Session(sid, user_id, self.mcp_configs)
                self._sessions[sid] = session
        await session.ensure_all()
        session.touch()
        return session

    # ---- pure-dict ops (no stack access, safe from any task) ------------------

    async def create(self, user_id: int, session_id: int, mcp_configs: dict | None = None) -> Session:
        session = Session(str(session_id), user_id, mcp_configs or self.mcp_configs)
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

    # ---- stack-affine ops (routed through the owner task) ---------------------

    async def ensure_ready(self, chat_id, user_id) -> Session:
        """Get-or-create the chat's Session and make sure its MCP servers are up.

        Startup and ping-failure rebuilds happen in the owner task, so the
        stack is entered and (if needed) exited by the same task.
        """
        return await self._submit("ensure_ready", (chat_id, user_id))

    async def retire_idle(self, now=None) -> int:
        if now is None:
            now = time.monotonic()
        async with self._lock:
            expired = [sid for sid, s in self._sessions.items()
                       if now - s.last_touched > self.idle_timeout]
            sessions = [self._sessions.pop(sid) for sid in expired]
        for s in sessions:
            try:
                await self._submit("close", s)
            except Exception:
                logger.exception("Error closing idle session")
        return len(sessions)

    async def close(self, session_id: str):
        async with self._lock:
            s = self._sessions.pop(str(session_id), None)
        if s:
            await self._submit("close", s)

    async def close_for_user(self, user_id: int):
        async with self._lock:
            expired = [sid for sid, s in self._sessions.items()
                       if s.user_id == user_id]
            sessions = [self._sessions.pop(sid) for sid in expired]
        for s in sessions:
            await self._submit("close", s)

    async def close_all(self):
        await self._submit("close_all")
