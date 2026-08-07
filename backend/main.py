# Blank file 
## One day this file will contain backend
from dotenv import load_dotenv
import os
import uvicorn
import sqlite3
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
load_dotenv()

from auth.user import CreateUser 
from routers.auth import router as auth_router
from routers.chat import router as chat_router

app = FastAPI()
app.include_router(auth_router)
app.include_router(chat_router)

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

def main():
    initDB().close()
    if __name__ == "__main__":
        uvicorn.run(app, host="0.0.0.0", port=8000)

def initDB():
    if not os.path.exists("db.db"):
        print("DB not found creating new")
    f = open("init.sql")
    init = f.read()
    conn = sqlite3.connect('db.db')
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
    
main()
