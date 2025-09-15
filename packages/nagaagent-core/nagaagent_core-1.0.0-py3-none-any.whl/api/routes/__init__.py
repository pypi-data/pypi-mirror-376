"""
API路由模块
"""

from .chat import chat_router
from .mcp import mcp_router  
from .system import system_router

__all__ = [
    "chat_router",
    "mcp_router", 
    "system_router"
]
