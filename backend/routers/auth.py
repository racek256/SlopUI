from fastapi.responses import JSONResponse
from fastapi import FastAPI, Depends, Request, HTTPException, Cookie, APIRouter
from pydantic import BaseModel
from auth.user import CreateUser, LoginUser, VerifyToken, Error 
from DB.connection import get_conn

class UserData(BaseModel):
    username: str 
    password: str 
class Token(BaseModel):
    username:str
    token:str

async def authenticate(request: Request):
    request.state.user = None
    try:
        token = request.cookies.get("token")
        if token:
            request.state.user = VerifyToken(token)
        else:
            request.state.user = None
    except Exception:
        request.state.user = None

router = APIRouter(prefix="/auth",tags=["auth"])

@router.post("/register")
def RegisterUser(data:UserData, conn = Depends(get_conn)):
    try:
        CreateUser(conn, data.username, data.password)
        return JSONResponse(content={"message":"user sucesfully created"}, status_code=201)
    except Error as e:
        if(e.error_type == "validation"):
            return JSONResponse(content={"error":e.error_message}, status_code=422)
        else:
            return HTTPException(status_code=500, detail="internal server error")

@router.post("/login")
def LoginUserEndpoint(data:UserData, conn = Depends(get_conn)):
    try: 
        result = LoginUser(conn, data.username, data.password)
        return JSONResponse(content={"success":True, "token":result}, status_code=201)
    except Error as e:
        if(e.error_type == "auth_failure"):
            return JSONResponse(content={"error":"wrong password"},status_code=401)
        else:
            return HTTPException(status_code=500, detail="internal server error")
@router.post("/verify")
def VerifySession(data:Token):
    try:
        username = VerifyToken(data.token)
        return JSONResponse(content={"username":username}, status_code=200)
    except Error as e: 
        if e.error_type == "auth_failure":
            return JSONResponse(content={"error":"Session Expired"}, status_code=401)





