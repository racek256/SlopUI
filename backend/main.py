# Blank file 
## One day this file will contain backend
from dotenv import load_dotenv
import os
import uvicorn
import sqlite3
from fastapi import FastAPI
load_dotenv()

from auth.user import CreateUser 
from routers.auth import router as auth_router

app = FastAPI()
app.include_router(auth_router)

def main():
    initDB().close()
    if __name__ == "__main__":
        uvicorn.run(app, host="0.0.0.0", port=8000)

def initDB():
    if not os.path.exists("db.sql"):
        print("DB not found creating new")
    f = open("init.sql")
    init = f.read()
    conn = sqlite3.connect('db.sql')
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
