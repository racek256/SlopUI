# Blank file
## One day this file will contain backend
import asyncio
import bcrypt
from contextlib import asynccontextmanager
from dotenv import load_dotenv
import logging
import os
import sqlite3
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
load_dotenv('../.env')
from stuff.settings import get_settings

from stuff.logging_setup import setup_logging
setup_logging()

logger = logging.getLogger(__name__)

from auth.user import CreateUser
from routers.auth import router as auth_router
from routers.chat import router as chat_router

# MCP stuff
from stuff.MCP.mcp_manager import SessionManager
from stuff.memory.memory_engine import batch_scan

#MCP_CONFIGS = {
#    "lightpanda":  {"command": "/home/racek/.local/bin/lightpanda", "args": ["mcp"]},
#}
MCP_CONFIGS = {item["name"]: item for item in get_settings()["MCPS"]}


# Schedulers setup
async def reaper_loop(app: FastAPI, interval_sec: float):
    while True:
        try:
            await asyncio.sleep(interval_sec)
            count = await app.state.mcp.reap_idle()
            if count:
                logger.info("Reaped %d idle MCP sessions", count)
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("reaper_loop error")


async def memory_loop(interval_sec: float, limit: int):
    while True:
        try:
            await asyncio.sleep(interval_sec)
            await asyncio.to_thread(batch_scan, limit)
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("memory_loop error")


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.mcp = SessionManager(MCP_CONFIGS, idle_timeout=300.0)
    app.state._jobs = [
        asyncio.create_task(reaper_loop(app, 60 * 120)),
        asyncio.create_task(memory_loop(60 * 30, 40)),
    ]
    try:
        yield
    finally:
        for job in app.state._jobs:
            job.cancel()
        for job in app.state._jobs:
            try:
                await job
            except asyncio.CancelledError:
                pass
        await app.state.mcp.close_all()


# router stuff
app = FastAPI(lifespan=lifespan)
app.include_router(auth_router)
app.include_router(chat_router)


# cors stuff
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://100.64.0.32:5173",
        "http://dev.racek.xyz",
        "https://dev.racek.xyz",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# main stuff
def main():
    conn = initDB()
    setupDemo(conn)
    conn.close()
    if __name__ == "__main__":
        uvicorn.run(app, host="0.0.0.0", port=8000)

def initDB():
    if not os.path.exists("db.db"):
        logger.info("DB not found creating new")
    f = open("init.sql")
    init = f.read()
    conn = sqlite3.connect('db.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.executescript(init)
    # dev env check
    if(os.path.exists("dev.sql")):
        logger.info("Dev enviroment was found and activated")
        f = open("dev.sql")
        dev = f.read()
        cursor.executescript(dev)
    conn.commit()
    return conn

# Demo setup
def setupDemo(conn):
    cursor = conn.cursor()
    demoacc = cursor.execute("select * from users where username = 'demo'").fetchone()
    if (get_settings()["app"]["demo_mode"] == "true"):
        if demoacc is None:
            bytes = "demo".encode('utf-8')
            salt = bcrypt.gensalt()
            hash = bcrypt.hashpw(bytes, salt)
            cursor.execute("insert into users (username, password_hash) values (?,?)", ("demo", hash))
            conn.commit()
    else:
        if demoacc is not None:
            cursor.execute("delete from users where id = ?", (demoacc["id"],))
            conn.commit()


main()
