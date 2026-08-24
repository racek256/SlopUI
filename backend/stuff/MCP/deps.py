# deps.py
from fastapi import Request
from mcp_manager import SessionManager

def get_mcp(request: Request) -> SessionManager:
    return request.app.state.mcp
