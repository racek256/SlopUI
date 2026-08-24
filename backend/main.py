# Blank file 
## One day this file will contain backend
import bcrypt
from dotenv import load_dotenv
import os
import uvicorn
import sqlite3
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
load_dotenv('../.env')

from auth.user import CreateUser 
from routers.auth import router as auth_router
from routers.chat import router as chat_router

from contextlib import asynccontextmanager
from fastapi import FastAPI


# MCP stuff
from contextlib import asynccontextmanager
from fastapi import FastAPI
from stuff.MCP.mcp_manager import SessionManager

MCP_CONFIGS = {
    "lightpanda":  {"command": "/home/racek/.local/bin/lightpanda", "args": ["mcp"]},
}

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.mcp = SessionManager(MCP_CONFIGS)
    yield
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
    conn =initDB()
    setupDemo(conn)
    conn.close()
    if __name__ == "__main__":
        uvicorn.run(app, host="0.0.0.0", port=8000)

def initDB():
    if not os.path.exists("db.db"):
        print("DB not found creating new")
    f = open("init.sql")
    init = f.read()
    conn = sqlite3.connect('db.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.executescript(init)
    # dev env check
    if(os.path.exists("dev.sql")):
        print("Dev enviroment was found and activated")
        f = open("dev.sql")
        dev = f.read()
        cursor.executescript(dev)
    conn.commit()
    return conn

# Demo setup 
def setupDemo(conn):
    cursor = conn.cursor()
    demoacc = cursor.execute("select * from users where username = 'demo'").fetchone()
    if (os.environ.get("DEMO_MODE") == "true"): 
        if demoacc is None:
            bytes = "demo".encode('utf-8')
            salt = bcrypt.gensalt()
            hash = bcrypt.hashpw(bytes,salt)
            cursor.execute("insert into users (username, password_hash) values (?,?)", ("demo", hash)) 
            conn.commit()
    else:
        if demoacc is not None:
            cursor.execute("delete from users where id = ?",(demoacc["id"],))
            conn.commit()

    conn.close()


        
            




    
main()
