from routers.auth import authenticate
import json
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel
from fastapi import  Depends, Request, HTTPException, Cookie, APIRouter, Response
from stuff.chat import chat
from DB.connection import get_conn
from stuff.chatUtils import RenameChat, GetChat, GetChats
from stuff.configUtils import listModels, checkModel
from deps import get_mcp
from stuff.MCP.mcp_manager import SessionManager
router = APIRouter(prefix="/chat", tags=["chat"])

class MessageData(BaseModel):
    content: str 
    chat_id: str | None = None
    model: str
class RenameChatData(BaseModel):
    chat_id: str 
    chat_name: str


@router.post("/send",  response_class=StreamingResponse)
async def sendMessage(data: MessageData, conn = Depends(get_conn), user_id = Depends(authenticate), mcp: SessionManager = Depends(get_mcp)):
    if user_id == None: 
        raise HTTPException(status_code=401, detail="Unauthorized request")
    if not checkModel(data.model):
        raise HTTPException(status_code=404, detail="Model not availible")
    async def generate():
        async for item in chat(conn, user_id, data.chat_id, data.content, data.model, mcp):
            yield item
    return StreamingResponse(generate(),media_type="application/x-ndjson")


@router.post("/rename")
def renameChat(data: RenameChatData,conn = Depends(get_conn), user_id = Depends(authenticate)):
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
def getModels(conn = Depends(get_conn), user_id = Depends((authenticate))):
    try:
        models = listModels()
        cursor = conn.cursor()
        user = cursor.execute("select last_model from users where id = ?", (user_id,)).fetchone()
        last_model = user["last_model"] if user else None
        for i,model in enumerate(models):
            if model["id"] == last_model:
                models[i]["default"] = True

        return JSONResponse(status_code=200, content={"models":models}) 
    except Exception as e:
        print(e)
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


