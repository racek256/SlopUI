from auth.user import genToken
from fastapi.responses import JSONResponse
import httpx
import os
from urllib.parse import urlencode
from fastapi import FastAPI, Depends, Request, HTTPException, Cookie, APIRouter
from pydantic import BaseModel
from auth.user import CreateUser, LoginUser, VerifyToken, Error
from DB.connection import get_conn
import logging

logger = logging.getLogger(__name__)

class UserData(BaseModel):
    username: str 
    password: str 
class Token(BaseModel):
    token:str
class discord(BaseModel):
    code:str

async def authenticate(request: Request):
    request.state.user = None
    try:
        token = request.cookies.get("token")
        logger.debug(request.cookies)
        if token:
            return(VerifyToken(token))
        else:
            return(None)
    except Exception as e:
        logger.exception(e)
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
        logger.error(e.error_type)
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
        logger.error(e.error_type)
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

@router.post("/discord")
def discord(data:discord, conn=Depends(get_conn)):
    code = data.code
    try:       
        resp = httpx.post(
            "https://discord.com/api/oauth2/token",       # ← /api/oauth2/token
            data={                                         # ← form body (auto Content-Type)
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": os.environ["DISCORD_REDIRECT_URI"],
            },
            auth=(                                          # ← auto Authorization: Basic
                os.environ["DISCORD_CLIENT_ID"],
                os.environ["DISCORD_CLIENT_SECRET"],
            ),
        )
        print(resp.text)
        resp.raise_for_status()
        token = resp.json()["access_token"]

        me = httpx.get("https://discord.com/api/users/@me",
                  headers={"Authorization": f"Bearer {token}"})
        me.raise_for_status()
        user = me.json()

        # Find if user exists by discord_id
        cursor = conn.cursor()
        user_row = cursor.execute("select * from users where discord_id = (?)", (user["id"],)).fetchone()

        if user_row:
            # login stuff
            jwt_token = genToken(user_row["username"], user_row["id"])
            response = JSONResponse(content={"success": True}, status_code=200)

            response.set_cookie(
                key="token",
                value=jwt_token,
                max_age=7 * 24 * 3600,   # 7 days, in seconds
                httponly=False,
                secure=False,             # False if testing over plain http://localhost
                samesite="lax",          # "none" if frontend/backend are truly cross-origin
            )
            return response
        else:
            # create account
            new_user = cursor.execute("insert into users (username, discord_id) values (?,?)", (user["username"], user["id"])).fetchone() 
            user_id = cursor.lastrowid
            jwt_token = genToken(user["username"], user_id)
            try: 
                conn.commit()
                response = JSONResponse(content={"success": True}, status_code=200)
                response.set_cookie(
                    key="token",
                    value=jwt_token,
                    max_age=7 * 24 * 3600,   # 7 days, in seconds
                    httponly=False,
                    secure=False,             # False if testing over plain http://localhost
                    samesite="lax",          # "none" if frontend/backend are truly cross-origin
                )
                return response
            except Exception as e:
                logger.error(e)
                raise Error(str(e), "System error")



    except Exception as e:
        logger.error(e)
        raise HTTPException(status_code=500, detail="internal server error")



