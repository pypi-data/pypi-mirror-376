"""
MCP服务管理模块

提供MCP服务的连接、管理和调用功能
"""

from .manager import MCPManager, Handoff, HandoffError, HandoffInputData
from .registry import MCP_REGISTRY, scan_and_register_mcp_agents

# 全局MCP管理器实例
_MCP_MANAGER = None

def get_mcp_manager():
    """获取全局MCP管理器实例"""
    global _MCP_MANAGER
    if not _MCP_MANAGER:
        _MCP_MANAGER = MCPManager()
    return _MCP_MANAGER

__all__ = [
    "MCPManager",
    "Handoff", 
    "HandoffError",
    "HandoffInputData",
    "MCP_REGISTRY",
    "scan_and_register_mcp_agents",
    "get_mcp_manager"
]