from routers.auth import authenticate
import json
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel
from fastapi import  Depends, Request, HTTPException, Cookie, APIRouter, Response
from stuff.chat import chat
from DB.connection import get_conn
from stuff.chatUtils import RenameChat, GetChat, GetChats
from stuff.configUtils import listModels, checkModel
router = APIRouter(prefix="/chat", tags=["chat"])

class MessageData(BaseModel):
    content: str 
    chat_id: str | None = None
    model: str
class RenameChatData(BaseModel):
    chat_id: str 
    chat_name: str

@router.post("/send", response_class=StreamingResponse)
def sendMessage(data: MessageData, conn = Depends(get_conn), user_id = Depends(authenticate)):
    if user_id == None: # Development hack remember to remove before commit
        print("user isn't authenticated")
        raise HTTPException(status_code=401, detail="Unauthorized request")
    if not checkModel(data.model):
        raise HTTPException(status_code=404, detail="Model not availible")
    def generate():
        g = chat(conn, user_id, data.chat_id, data.content, data.model)
        yield from g
    return StreamingResponse(generate(),media_type="application/x-ndjson")


@router.post("/rename")
def renameChat(data: RenameChatData,conn = Depends(get_conn), user_id = Depends(get_conn)):
    if not user_id: 
        raise HTTPException(status_code=401, detail="Unauthorized request")
    try:
        RenameChat(conn, user_id, data.chat_id, data.chat_name)
        return Response(status_code=200)
    except:
        raise HTTPException(status_code=500, detail="internal server error")

@router.get("/")
def Chats(limit: int =50, conn = Depends(get_conn), user_id = Depends(authenticate)):
    if user_id is None:
        raise HTTPException(status_code=401, detail="Unauthorized")
    try:
        chats = json.dumps(GetChats(conn, user_id, limit))
        return JSONResponse(content={"chats": chats}, status_code=200) 
    except:
        raise HTTPException(status_code=500, detail="internal server error")

@router.get("/models")
def getModels():
    try:
        models = listModels()
        return JSONResponse(status_code=200, content={"models":models}) 
    except:
        raise HTTPException(status_code=500, detail="internal server error")

@router.get("/{chat_id}")
def loadChat(chat_id:int, conn = Depends(get_conn), user_id= Depends(authenticate)):
    if user_id is None:
        raise HTTPException(status_code=401, detail="Unauthorized")
    try:
        chat = json.dumps(GetChat(conn, user_id, chat_id))
        return JSONResponse(status_code=200, content={"chat":chat})
    except:
        raise HTTPException(status_code=500, detail="internal server error")


