"""
NagaAgent_core - 娜迦AI助手核心功能包

包含娜迦AI助手的核心功能模块：
- 流式工具调用处理
- MCP服务管理
- 消息和会话管理
- 工具调用解析和执行
"""

__version__ = "1.0.0"
__author__ = "NagaAgent Team"
__email__ = "naga@example.com"

# 导入主要模块
try:
    from .streaming import StreamingToolCallExtractor, StreamingResponseProcessor
    from .mcp import MCPManager, Handoff, HandoffError
    from .messages import MessageManager
    from .tools import parse_tool_calls, execute_tool_calls
except ImportError:
    # 如果相对导入失败，尝试绝对导入
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    from streaming import StreamingToolCallExtractor, StreamingResponseProcessor
    from mcp import MCPManager, Handoff, HandoffError
    from messages import MessageManager
    from tools import parse_tool_calls, execute_tool_calls

# 定义公开的API
__all__ = [
    # 版本信息
    "__version__",
    "__author__", 
    "__email__",
    
    # 流式处理
    "StreamingToolCallExtractor",
    "StreamingResponseProcessor",
    
    # MCP管理
    "MCPManager",
    "Handoff",
    "HandoffError",
    
    # 消息管理
    "MessageManager",
    
    # 工具调用
    "parse_tool_calls",
    "execute_tool_calls",
]
