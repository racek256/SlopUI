import sqlite3
from stuff.memory.memory_filter import memory
from stuff.memory.conv_parser import parser
def test(chat_id):
    # testing params
    # load DB
    conn = sqlite3.connect("./db.db", check_same_thread=False)
    conn.row_factory = sqlite3.Row

    cursor = conn.cursor()

    messages = cursor.execute("select * from messages where chat_id = ?",(chat_id,)).fetchall()
    # Rebuilding chat array



    query = cursor.execute("select id from messages where chat_id = ? order by id desc limit 1", (chat_id,)).fetchone()
    last_message = query["id"]

    # Start for loop of finding message parent_message_id and store into array 
    history = []
    found = False 
    while not found:
        for message in messages:
            if message["id"] == last_message:
                if message["role"] == "assistant":
                    history.append({
                        "role":"assistant",
                        "content":message["content"]
                        })
                else:
                    history.append({
                        "role":"user",
                        "content":[{"type":"text", "text":message["content"]}]
                        })

                if message["parent_message_id"] is not None:
                    last_message = message["parent_message_id"]
                else:
                    found = True

    # reverse the array 
    history.reverse()
    return parser("opencode-go/deepseek-v4-flash", history)
    
import asyncio 

async def testloop():
    conversations = []
    for i in range(700,760):
        conversations.append(test(i))
    print(conversations)
    ready_convs = []
    for conv in conversations:
        for item in conv:
            if item["memory"] != "":
                ready_convs.append(conv)
                break;
    local_memory = memory([],conversations, "opencode-go/deepseek-v4-flash")
    print(local_memory.filter())



asyncio.run(testloop())
