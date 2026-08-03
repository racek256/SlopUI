import bcrypt
from datetime import datetime, timedelta
import os
import jwt
class Error(Exception):
    def __init__(self, error_msg: str, error_type: str) -> None:
        self.error_message = error_msg
        self.error_type = error_type
        super().__init__(error_msg)

def CreateUser(conn, username, password):
    cursor = conn.cursor();
    # Prechecks 
    if len(username) <= 3:
        raise Error("short_username", "validation")
    elif cursor.execute("select username from users where username = ?", (username,)).fetchone():
        raise Error("username_used", "validation")
    elif len(password) <= 7:
        raise Error("short_password", "validation") 

    # Password hashing 
    bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hash = bcrypt.hashpw(bytes,salt)
    # DB insertion
    cursor.execute("insert into users (username, password_hash) values (?,?)", (username, hash)) 
    user_id = cursor.lastrowid
    encoded = jwt.encode({"username": username, "user_id":user_id, "exp": datetime.now() + timedelta(days=7)}, os.environ["SECRET"], algorithm="HS256")

    try:
        conn.commit()
        return encoded
    except Exception as e:
        raise Error(e, "system error")

def LoginUser(conn, username, password):
    bytes = password.encode('utf-8')
    cursor = conn.cursor()
    row = cursor.execute("select * from users where username = ?", (username,)).fetchone()
    if row is None:
        raise Error("user doesn't exist", "not_found")

    hash = row["password_hash"]
    if not bcrypt.checkpw(bytes,hash):
        raise Error("Incorrect password", "auth_failure")
    encoded = jwt.encode({"username": username, "user_id":row["id"]}, os.environ["SECRET"], algorithm="HS256")
    return encoded

def VerifyToken(token):
    decoded = jwt.decode(token, os.environ["SECRET"], algorithms="HS256")
    return decoded["user_id"]


    
