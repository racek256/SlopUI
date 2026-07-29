import bcrypt
import os
import jwt
class Error(Exception):
    def __init__(self, error_msg: str, error_type: str) -> None:
        self.error_message = error_msg
        self.error_type = error_type
        super().__init__(error_msg)

def CreateUser(conn, username, password):
    print("Creating user")
    cursor = conn.cursor();
    # Prechecks 
    if len(username) <= 3:
        raise Error("username needs to be at least 4 characters long", "validation")
    elif cursor.execute("select username from users where username = ?", (username,)).fetchone():
        raise Error("username already exists", "validation")
    elif len(password) <= 7:
        raise Error("password needs to be at least 8 characters", "validation") 

    # Password hashing 
    bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hash = bcrypt.hashpw(bytes,salt)
    # DB insertion
    cursor.execute("insert into users (username, password_hash) values (?,?)", (username, hash))
    try:
        conn.commit()
    except Exception as e:
        raise Error(e, "system error")

def LoginUser(conn, username, password):
    bytes = password.encode('utf-8')
    cursor = conn.cursor()
    row = cursor.execute("select password_hash from users where username = ?", (username,)).fetchone()
    hash = row[0]
    if not bcrypt.checkpw(bytes,hash):
        raise Error("Incorrect password", "auth_failure")
    encoded = jwt.encode({"username": username}, os.environ["SECRET"], algorithm="HS256")
    return encoded

def VerifyToken(token):
    decoded = jwt.decode(token, os.environ["SECRET"], algorithms="HS256")
    return decoded["username"]


    
