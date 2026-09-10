from stuff.chatUtils import InsertMessage, CreateChat, RenameChat
from stuff.MCP.mcp_manager import SessionManager
import logging
from stuff.generations import publish, DONE
from DB.connection import get_conn
import json
from stuff.harness import harness, title
import sqlite3

logger = logging.getLogger(__name__)

async def run_generation(gen, conn,user_id, chat_id, content, model, mcp):
    conn = sqlite3.connect("db.db", check_same_thread=False)
    conn.row_factory = sqlite3.Row
    async for item in chat(conn, user_id, chat_id, content, model, mcp):
        publish(gen, item)
    publish(gen, DONE)
                
                


async def chat(conn,user_id, chat_id, content, model, mcp):
    cursor = conn.cursor()


    
    
    chat = None
    if(chat_id):
        # Verify chat existence
        chat = cursor.execute("select * from chats where id = ?",(chat_id,)).fetchone()
        if chat["current_message_id"] is None:
            RenameChat(conn, user_id, chat_id, title(content))
    else:
        chat_id = CreateChat(conn, user_id, title(content)) 
        # calling title function here is slow and unefficent should instead start async job that renames chat later 
        chat = cursor.execute("select * from chats where id = ?",(chat_id,)).fetchone()

    try:
        cursor.execute("update users set last_model = ? where id = ?", (model, user_id))
        cursor.execute("update chats set last_model = ? where user_id = ? and id = ?", (model, user_id, chat_id))
    except:
        logger.warning("updating last model failed")


    last_message = None
    if content != "[REGEN_USER_MESSAGE]":
        # Insert user message
        last_message = InsertMessage(conn, user_id, chat_id, "user", content)
    else:
        query = cursor.execute("select id from messages where chat_id = ? order by id desc limit 1", (chat_id,)).fetchone()
        last_message = query["id"]

    # Load chat messages
    if chat is None:
        logger.warning("nope replace with error later")
    messages = cursor.execute("select * from messages where chat_id = ?",(chat_id,)).fetchall()
    # Rebuilding chat array

    # Start for loop of finding message parent_message_id and store into array 
    history = []
    found = False 
    while not found:
        for message in messages:
            if message["id"] == last_message:
                if message["role"] == "assistant":
                    chain = json.loads(message["chain"])
                    chain.reverse()
                    history += chain
                else:
                    history.append({
                        "role":"user",
                        "content":message["content"]
                        })
                if message["parent_message_id"] is not None:
                    last_message = message["parent_message_id"]
                else:
                    found = True

    # reverse the array 
    history.reverse()



    # prepare MCP harness

    session = await mcp.get(chat_id)
    if session == None:
        session = await mcp.create(user_id, chat_id)
        await session.ensure_all()

    
    
    # start harness
    #g = harness(history,None,model, session)
    response = None


    ### TODO: Forward streaming to router


    async for item in harness(history, None, model, session):
        if type(item) != str:
            response = item
            last_message = InsertMessage(conn, user_id, chat_id, "assistant", response["content"], json.dumps(response["chain"]))
            yield json.dumps({
            "chat_id":chat_id
            })
            break

        else:
            yield item
           
