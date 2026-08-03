class Error(Exception):
    def __init__(self, error_msg: str, error_type: str) -> None:
        self.error_message = error_msg
        self.error_type = error_type
        super().__init__(error_msg)


def CreateChat(conn, user_id, chatName=None):
    cursor = conn.cursor()
    if chatName:
        cursor.execute("insert into chats (user_id, name) values (?,?)",(user_id,chatName))
    else:
        cursor.execute("insert into chats (user_id) values (?)",(user_id,))
    chat_id = cursor.lastrowid
    conn.commit()
    return chat_id

def InsertMessage(conn, user_id, chat_id, role, content, chain=None):
    cursor = conn.cursor()
    chat = cursor.execute("select user_id, current_message_id from chats where id = ?",(chat_id,)).fetchone()
    if not chat: 
        raise Error("chat doesn't exist", "not_found")
    if not chat["user_id"] == user_id:
        raise Error("user is not owner of this chat", "permission")
    cursor.execute("insert into messages (chat_id, content, role, parent_message_id, chain) values (?,?,?,?,?)",(chat_id, content,role, chat["current_message_id"] or None, chain))
    message_id = cursor.lastrowid
    # Set to current message
    cursor.execute("update chats set current_message_id = ? where id = ?", (message_id, chat_id))
    conn.commit()
    return message_id

def RenameChat(conn, user_id, chat_id, new_name):
    cursor = conn.curosr()
    chat = cursor.execute("select user_id from chats where id = ?", (chat_id,)).fetchone()
    if chat["user_id"] != user_id:
        return Error("user is not owner of this chat","permission")
    cursor.execute("update chats set name = ? where id = ?",(new_name,chat_id))

    


def GetChat(conn, user_id, chat_id):
    cursor = conn.cursor()
    # Fetch chat and verify ownership
    chat = cursor.execute("select * from chats where id = ?",(chat_id,)).fetchone()
    if chat is None: 
        raise Error("chat doesn't exist", "not_found")
    if not chat["user_id"] == user_id:
        raise Error("user is not owner of this chat", "permission")
    # Fetch messages
    messages = cursor.execute("select * from messages where chat_id = ? order by id",(chat_id,)).fetchall()
    chatStruct = {
            "name":chat["name"],
            "current_message_id":chat["current_message_id"],
            "messages":[]
            }
    for message in messages:
        if message["role"] == "user":
            chatStruct["messages"].append({
                "id":message["id"],
                "content":message["content"],
                "role":message["role"],
                "parent_message_id": message["parent_message_id"]
                })
        else:
            chatStruct["messages"].append({
                "id":message["id"],
                "content":message["content"],
                "role":message["role"],
                "chain":message["chain"],
                "parent_message_id": message["parent_message_id"]
                })
    return chatStruct

def GetChats(conn, user_id, limit=10):
    cursor = conn.cursor()
    chats = cursor.execute("select * from chats where user_id = ? order by id desc limit ? ", (user_id, limit)).fetchall()
    chatsStruct = []
    for chat in chats:
        chatsStruct.append({
            "name":chat["name"] or "new chat",
            "id":chat["id"]
            })
    return chatsStruct

def DeleteChat(conn, user_id, chat_id):
    cursor = conn.cursor()
    owner = cursor.execute("select user_id from chats where id = ?", (chat_id,)).fetchone()
    if owner is None:
        raise Error("Chat doesn't exist", "not_found")
    if not owner["user_id"] == user_id:
        raise Error("User is not owner of this chat", "permission")
    cursor.execute("delete from chats where id = ?",(chat_id,))
    conn.commit()

def SetCurrentMessage(conn, user_id, chat_id, current_message_id):
    cursor = conn.cursor()
    owner = cursor.execute("select user_id from chats where id = ?",(chat_id,)).fetchone()
    message = cursor.execute("select chat_id from messages where id = ?", (current_message_id,)).fetchone()
    if owner is None:
        raise Error("Chat doesn't exist", "not_found")
    if not owner["user_id"] == user_id:
        raise Error("user is not owner of this chat", "permission")
    if message is None:
        raise Error("message doesn't exist", "not_found")
    if not message["chat_id"] == chat_id:
        raise Error("message doesn't belong to this chat", "validation")
    cursor.execute("update chats set current_message_id = ? where id = ?", (current_message_id,chat_id))
    conn.commit()

