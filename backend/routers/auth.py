from fastapi.responses import JSONResponse
from fastapi import FastAPI, Depends, Request, HTTPException, Cookie, APIRouter
from pydantic import BaseModel
from auth.user import CreateUser, LoginUser, VerifyToken, Error 
from DB.connection import get_conn

class UserData(BaseModel):
    username: str 
    password: str 
class Token(BaseModel):
    token:str

async def authenticate(request: Request):
    request.state.user = None
    try:
        token = request.cookies.get("token")
        print(request.cookies)
        if token:
            return(VerifyToken(token))
        else:
            return(None)
    except Exception:
        return(None)

router = APIRouter(prefix="/auth",tags=["auth"])

@router.post("/register")
def RegisterUser(data:UserData, conn = Depends(get_conn)):
    try:
        result = CreateUser(conn, data.username, data.password)
        return JSONResponse(content={"success":True, "token":result}, status_code=201)
    except Error as e:
        if(e.error_type == "validation"):
            return JSONResponse(content={"error":e.error_message}, status_code=422)
        else:
            raise HTTPException(status_code=500, detail="internal server error")


@router.post("/login")
def LoginUserEndpoint(data: UserData, conn = Depends(get_conn)):
    try:
        result = LoginUser(conn, data.username, data.password)
        response = JSONResponse(content={"success": True}, status_code=200)
        response.set_cookie(
            key="token",
            value=result,
            max_age=7 * 24 * 3600,   # 7 days, in seconds
            httponly=False,
            secure=False,             # False if testing over plain http://localhost
            samesite="lax",          # "none" if frontend/backend are truly cross-origin
        )
        return response
    except Error as e:
        print(e.error_type)
        if e.error_type == "auth_failure":
            return JSONResponse(content={"error": "wrong password"}, status_code=401)
        elif e.error_type == "not_found":
            raise HTTPException(status_code=404, detail="user doesn't exist")
        else:
            raise HTTPException(status_code=500, detail="internal server error")

@router.post("/login")
def LoginUserEndpoint(data:UserData, conn = Depends(get_conn)):
    try: 
        result = LoginUser(conn, data.username, data.password)
        return JSONResponse(content={"success":True, "token":result}, status_code=200)
    except Error as e:
        print(e.error_type)
        if(e.error_type == "auth_failure"):
            return JSONResponse(content={"error":"wrong password"},status_code=401)
        elif e.error_type == "not_found":
            raise HTTPException(status_code=404, detail="user doesn't exist")
        else:
            raise HTTPException(status_code=500, detail="internal server error")


@router.post("/verify")
def VerifySession(data:Token):
    try:
        username = VerifyToken(data.token)
        return JSONResponse(content={"username":username}, status_code=200)
    except Error as e: 
        if e.error_type == "auth_failure":
            return JSONResponse(content={"error":"Session Expired"}, status_code=401)
