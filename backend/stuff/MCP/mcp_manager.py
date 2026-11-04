import asyncio
import logging
import os
import signal
import threading
import time
from .Session import Session

logger = logging.getLogger(__name__)

# The MCP event loop lives in its own daemon thread (the "home" thread). Every
# MCP stack enter/exit and every tool call happens in that loop, so nothing the
# uvicorn loop does (request cancellation, reload, lifespan teardown) can ever
# poison an anyio scope there. Proven 100%-CPU failure mode this prevents:
# an anyio scope left with tasks that never finish makes `_deliver_cancellation`
# re-schedule itself every loop tick forever.
# The probe watcher bounds the blast radius of ANY wedge inside the home loop:
# if noop probes fail HARD_STRIKES times in a row the whole thread is torn
# down and rebuilt (sessions are re-opened lazily by the next request).
HOME_PROBE_TIMEOUT = 20.0    # seconds a probe may wait behind other ops
HOME_PROBE_INTERVAL = 30.0   # seconds between probes
HOME_PROBE_STRIKES = 3       # consecutive failed probes before a rebuild
HOME_CLOSE_TIMEOUT = 15.0    # seconds shutdown/restart waits for close_all
HOME_READY_TIMEOUT = 15.0    # seconds to wait for a fresh home to answer


def _resolve(fut: asyncio.Future, fn) -> None:
    """Deliver to a future whose reader may have vanished mid-wait."""
    if fut.done():
        return  # submitter cancelled; nobody will read the result
    try:
        fn()
    except Exception:
        logger.exception("Failed to deliver MCP op result")


class SessionManager:
    """Registry of per-chat MCP sessions, isolated in one home thread."""

    def __init__(self, mcp_configs: dict, idle_timeout: float = 300.0):
        self.mcp_configs = mcp_configs
        self.idle_timeout = idle_timeout
        # Session objects are touched by server-loop tasks (touch/get) and by
        # the home loop (creation, ensure), so guard the dict with a real lock.
        self._dict_lock = threading.Lock()
        self._sessions: dict[str, Session] = {}
        # Serialises startup/restart decisions (all callers are server-loop tasks).
        self._home_lock = asyncio.Lock()
        self._home_thread: threading.Thread | None = None
        self._home_loop: asyncio.AbstractEventLoop | None = None
        self._ops: asyncio.Queue | None = None   # created inside the home loop
        self._owner_task: asyncio.Task | None = None
        self._ready = threading.Event()
        self._probes_failed = 0

    # ---- public API (server loop) ------------------------------------ #
    async def submit(self, op: str, payload=None):
        """Hand one op to the home owner task (used by Session.execute too)."""
        return await self._submit(op, payload)

    async def ensure_ready(self, session_id, user_id) -> Session:
        """Get or build the per-chat session, pinging/rebuilding dead ones."""
        session = await self._submit("ensure_ready", (session_id, user_id))
        return session

    async def retire_idle(self, now: float | None = None) -> int:
        """Close sessions idle for longer than idle_timeout (home-run close)."""
        current = time.monotonic() if now is None else now
        limit = current - self.idle_timeout
        expired: dict[str, Session] = {}
        with self._dict_lock:
            for sid, session in list(self._sessions.items()):
                if session.last_touched <= limit:
                    expired[sid] = session
                    self._sessions.pop(sid, None)
        # Newest stack first (mcp python-sdk #577: FIFO teardown fails).
        ordered = sorted(expired.values(), key=lambda s: s.created, reverse=True)
        for session in ordered:
            logger.info("Retiring idle MCP session %s", session.session_id)
            try:
                await self._submit("close", session)
            except Exception:
                logger.exception("Error retiring MCP session %s", session.session_id)
        return len(ordered)

    async def health_check(self) -> None:
        try:
            await asyncio.wait_for(self._submit("noop"), timeout=HOME_PROBE_TIMEOUT)
            self._probes_failed = 0
        except Exception:
            self._probes_failed += 1
            logger.exception(
                "MCP home probe failed %d/%d",
                self._probes_failed, HOME_PROBE_STRIKES,
            )
            if self._probes_failed >= HOME_PROBE_STRIKES:
                logger.error("MCP home loop is wedged; restarting it")
                await self._restart_home()

    async def startup(self) -> None:
        async with self._home_lock:
            await self._start_home()

    async def shutdown(self) -> None:
        thread = self._home_thread
        if thread is not None and thread.is_alive():
            try:
                await asyncio.wait_for(
                    self._submit("close_all"), timeout=HOME_CLOSE_TIMEOUT)
            except asyncio.TimeoutError:
                logger.error(
                    "MCP close_all did not finish in %.0fs; abandoning teardown",
                    HOME_CLOSE_TIMEOUT)
            except Exception:
                logger.exception("MCP home failed to close sessions on shutdown")
        self._teardown_home()
        await self._join_home_thread()

    # ---- home thread plumbing ---------------------------------------- #
    async def _submit(self, op: str, payload=None):
        if self._home_thread is None or not self._home_thread.is_alive() \
                or self._home_loop is None:
            async with self._home_lock:
                if self._home_thread is None or not self._home_thread.is_alive():
                    logger.warning("MCP home thread not running; starting fresh for op %r", op)
                    await self._start_home()
        try:
            cf = asyncio.run_coroutine_threadsafe(
                self._enqueue(op, payload), self._home_loop)
        except RuntimeError:
            # The loop closed between the check and the submit: rebuild once.
            logger.exception("MCP home loop vanished during submit; rebuilding")
            async with self._home_lock:
                self._teardown_home()
                await self._start_home()
            cf = asyncio.run_coroutine_threadsafe(
                self._enqueue(op, payload), self._home_loop)
        # Awaiting the bridge future from the server loop is what decouples
        # this op from any request task: a cancelled request never poisons
        # the home owner (it just drops the bridge).
        return await asyncio.wrap_future(cf)

    async def _enqueue(self, op: str, payload):
        """Runs inside the home loop: hand the op to the owner task."""
        fut = self._home_loop.create_future()
        self._ops.put_nowait((op, payload, fut))
        return await fut

    async def _start_home(self):
        if self._home_thread is not None and self._home_thread.is_alive():
            return
        # Leftover subprocesses from an earlier home have nowhere to go now.
        self._kill_stale_mcp_children(signal.SIGTERM)
        self._ready.clear()
        self._announce_clear()
        thread = threading.Thread(target=self._home_main, name="mcp-home", daemon=True)
        self._home_thread = thread
        self._probes_failed = 0
        thread.start()
        ok = await asyncio.get_running_loop().run_in_executor(
            None, self._ready.wait, HOME_READY_TIMEOUT)
        if not ok:
            raise RuntimeError("MCP home thread failed to become ready")

    async def _restart_home(self):
        thread = self._home_thread
        if thread is not None and thread.is_alive():
            try:
                await asyncio.wait_for(
                    self._submit("close_all"), timeout=HOME_CLOSE_TIMEOUT)
            except asyncio.TimeoutError:
                logger.error("close_all hung during MCP restart; stopping home loop")
            except Exception:
                logger.exception("Error closing MCP sessions during restart")
        self._teardown_home()
        await self._join_home_thread()
        async with self._home_lock:
            await self._start_home()

    def _teardown_home(self) -> None:
        loop = self._home_loop
        if loop is not None and not loop.is_closed():
            # Stop works even against a call_soon storm: the storm re-schedules
            # at the tail, so the queued stop callback is eventually reached.
            loop.call_soon_threadsafe(loop.stop)
        self._announce_clear()

    async def _join_home_thread(self) -> None:
        thread = self._home_thread
        if thread is None:
            return
        if thread.is_alive():
            await asyncio.get_running_loop().run_in_executor(None, thread.join, 10.0)
            if thread.is_alive():
                logger.error("MCP home thread did not stop in 10s; abandoning it "
                             "(its subprocesses will be reaped on next start)")
        self._home_thread = None
        self._home_loop = None

    def _announce_clear(self) -> None:
        """Drop all session references: after a home change every open stack
        belongs to a dead owner task, so no new task may ever close them."""
        with self._dict_lock:
            self._sessions.clear()

    def _kill_stale_mcp_children(self, sig: int) -> None:
        """Kill MCP server subprocesses still parented to us by an older home."""
        commands = tuple(str(cfg.get("command", "")) for cfg in self.mcp_configs.values())
        mine = os.getpid()
        for entry in os.listdir("/proc"):
            if not entry.isdigit() or int(entry) == mine:
                continue
            try:
                with open(f"/proc/{entry}/stat", "rb") as f:
                    ppid = int(f.read().rsplit(b")", 1)[1].split()[1])
                with open(f"/proc/{entry}/cmdline", "rb") as f:
                    cmd = f.read().replace(b"\0", b" ").decode("utf-8", "replace")
            except (OSError, ValueError, IndexError):
                continue
            if ppid == mine and any(c and c in cmd for c in commands):
                try:
                    os.kill(int(entry), sig)
                    logger.info("Killed stale MCP child %s with %s", entry, sig)
                except OSError:
                    pass

    def _home_main(self):
        """Thread body: an isolated loop owning every MCP anyio task group."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            self._home_loop = loop
            # Leftover children from the SIGTERM pass get no more grace.
            self._kill_stale_mcp_children(signal.SIGKILL)
            loop.run_until_complete(self._start_owner())
            loop.run_forever()
        finally:
            self._cancel_owner()
            try:
                loop.run_until_complete(loop.shutdown_asyncgens())
            except Exception:
                pass
            loop.close()
            if self._home_loop is loop:
                self._home_loop = None

    def _cancel_owner(self):
        """Teardown: cancel the owner task inside its own loop so it ends
        cleanly instead of being destroyed mid-await when the loop closes."""
        task = self._owner_task
        loop = self._home_loop
        if task is None or loop is None or loop.is_closed() or task.done():
            return
        task.cancel()
        try:
            loop.run_until_complete(task)
        except asyncio.CancelledError:
            pass
        except BaseException:
            logger.exception("MCP owner task errored during teardown")

    async def _start_owner(self) -> None:
        self._ops = asyncio.Queue()
        task = asyncio.create_task(self._owner_loop(), name="mcp-owner")
        self._owner_task = task
        # If the owner ever dies, its open scopes die with it and no later
        # task may close them: drop all sessions so nothing stale is closed
        # cross-task, and immediately build a clean owner.
        def on_owner_done(done: asyncio.Task):
            if done.cancelled():
                return  # thread teardown; nothing to restore
            logger.exception("MCP owner task died; rebuilding it")
            loop = self._home_loop
            if loop is None or loop.is_closed():
                return  # home is going away anyway
            self._announce_clear()
            loop.call_soon(self._spawn_owner)
        task.add_done_callback(on_owner_done)
        # Round-trip one op so `_ready` means an answerable owner exists.
        await self._run_op("noop", None)
        self._ready.set()

    def _spawn_owner(self) -> None:
        loop = self._home_loop
        if loop is None or loop.is_closed():
            return
        loop.create_task(self._start_owner())

    async def _owner_loop(self):
        """Single owner task in the home loop: consumes ops from the queue.

        Anyio scopes are task-affine, so every stack enter/exit in every
        session runs here and nowhere else. The loop is deliberately
        unkillable from the inside: nothing below may ever escape and end
        this task (a dead owner means poisoned scopes), except a teardown
        cancel from the home thread itself.
        """
        ops: asyncio.Queue = self._ops
        try:
            while True:
                op, payload, fut = await ops.get()
                if fut.done():
                    # Submitter's request task was cancelled while waiting;
                    # nobody would read the result.
                    continue
                try:
                    result = await self._run_op(op, payload)
                except asyncio.CancelledError:
                    # Only teardown cancels the owner now. Fail the op, then
                    # die so the done-callback builds a clean owner.
                    _resolve(fut, lambda f=fut, e=RuntimeError("MCP operator cancelled"):
                             f.set_exception(e))
                    raise
                except BaseException as exc:  # noqa: BLE001 - the owner must survive ops
                    logger.exception("MCP op %r failed", op)
                    if not isinstance(exc, Exception):
                        exc = RuntimeError(f"MCP op failed: {exc!r}")
                    _resolve(fut, lambda f=fut, e=exc: f.set_exception(e))
                else:
                    _resolve(fut, lambda f=fut, r=result: f.set_result(r))
        except asyncio.CancelledError:
            raise
        except (GeneratorExit, SystemExit):
            # Thread teardown closing the loop: not a crash.
            raise
        except BaseException:
            # The task ends; the done-callback respawns it with clean state.
            logger.exception("MCP owner loop crashed")
            raise

    async def _run_op(self, op: str, payload):
        if op == "noop":
            return None
        if op == "ensure_ready":
            session_id, user_id = payload
            sid = str(session_id)
            with self._dict_lock:
                session = self._sessions.get(sid)
                if session is None:
                    session = Session(sid, user_id, self.mcp_configs, home=self)
                    self._sessions[sid] = session
            # ensure_all opens/rebuilds stacks: owned by this task, same loop.
            await session.ensure_all()
            session.touch()
            return session
        if op == "close":
            await payload.close()
            return None
        if op == "close_all":
            with self._dict_lock:
                sessions = list(self._sessions.values())
                self._sessions.clear()
            # Newest stack first (mcp python-sdk #577: FIFO teardown fails).
            for session in sorted(sessions, key=lambda s: s.created, reverse=True):
                try:
                    await session.close()
                except Exception:
                    logger.exception("Error closing MCP session %s", session.session_id)
            return len(sessions)
        if op == "execute":
            session_id, prefixed_name, arguments = payload
            with self._dict_lock:
                session = self._sessions.get(str(session_id))
            if session is None:
                raise KeyError("MCP session was reset; retry the tool call")
            return await session.run_tool(prefixed_name, arguments)
        raise ValueError(f"unknown MCP op: {op!r}")
