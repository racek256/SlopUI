from stuff.chatUtils import InsertMessage, SetCurrentMessage
import json
from stuff.harness import harness
def chat(conn,user_id, chat_id, content):
    cursor = conn.cursor()
    # Verify chat existence
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
                history += json.load(message["chain"])
                if message["parent_message_id"] is not None:
                    last_message = message["parent_message_id"]
                else:
                    found = True

    # reverse the array 
    history.reverse()
    
    # start harness
    active = True 
    g = harness()
    chunks = []
    response = None


    ### TODO: Forward streaming to router

    while True: 
        try:
            chunks.append(next(g))
        except StopIteration as e:
            response = e.value  
            break

    last_message = InsertMessage(conn, user_id, chat_id, "assistant", response["content"], json.dump(response["chain"]))
    SystemExit(conn, user_id, chat_id, last_message)

    print(response)

