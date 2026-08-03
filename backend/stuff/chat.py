from stuff.chatUtils import InsertMessage, CreateChat
import json
from stuff.harness import harness, title
def chat(conn,user_id, chat_id, content, model):
    cursor = conn.cursor()
    
    chat = None
    if(chat_id):
        # Verify chat existence
        chat = cursor.execute("select * from chats where id = ?",(chat_id,)).fetchone()
    else:
        chat_id = CreateChat(conn, user_id, title(content)) 
        # calling title function here is slow and unefficent should instead start async job that renames chat later 
        chat = cursor.execute("select * from chats where id = ?",(chat_id,)).fetchone()

    # Insert user message
    last_message = InsertMessage(conn, user_id, chat_id, "user", content)

    # Load chat messages
    if chat is None:
        print("nope replace with error later")
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
    
    # start harness
    active = True 
    g = harness(history,None,model)
    response = None


    ### TODO: Forward streaming to router

    while True: 
        try:
            yield next(g)
        except StopIteration as e:
            response = e.value  
            break

    last_message = InsertMessage(conn, user_id, chat_id, "assistant", response["content"], json.dumps(response["chain"]))

    yield json.dumps({
            "chat_id":chat_id
            })

    return({
        "chain":response["chain"],
        "response":response["content"]
        })
