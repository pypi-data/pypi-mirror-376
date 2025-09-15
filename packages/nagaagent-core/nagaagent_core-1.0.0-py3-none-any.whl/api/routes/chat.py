"""
聊天API路由
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, AsyncGenerator
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

logger = logging.getLogger(__name__)

# 请求模型
class ChatRequest(BaseModel):
    message: str
    stream: bool = False
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    session_id: Optional[str] = None
    status: str = "success"

# 创建路由器
chat_router = APIRouter(prefix="/chat", tags=["chat"])

@chat_router.post("/", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """对话接口 - 统一使用流式处理，支持工具调用"""
    try:
        # 这里需要集成NagaAgent实例
        # 暂时返回示例响应
        response = f"收到消息: {request.message}"
        
        return ChatResponse(
            response=response,
            session_id=request.session_id or "default",
            status="success"
        )
    except Exception as e:
        logger.error(f"聊天处理失败: {e}")
        raise HTTPException(status_code=500, detail=f"聊天处理失败: {str(e)}")

@chat_router.post("/stream")
async def chat_stream(request: ChatRequest):
    """流式聊天接口"""
    try:
        async def generate_response() -> AsyncGenerator[str, None]:
            # 模拟流式响应
            message = request.message
            words = message.split()
            
            for i, word in enumerate(words):
                yield f"data: {json.dumps({'chunk': word, 'index': i}, ensure_ascii=False)}\n\n"
                await asyncio.sleep(0.1)  # 模拟延迟
            
            yield f"data: {json.dumps({'done': True}, ensure_ascii=False)}\n\n"
        
        return StreamingResponse(
            generate_response(),
            media_type="text/plain",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
            }
        )
    except Exception as e:
        logger.error(f"流式聊天处理失败: {e}")
        raise HTTPException(status_code=500, detail=f"流式聊天处理失败: {str(e)}")

@chat_router.get("/sessions")
async def get_sessions():
    """获取会话列表"""
    try:
        # 这里应该从消息管理器获取会话列表
        sessions = [
            {
                "id": "session_1",
                "created_at": "2024-01-01T00:00:00Z",
                "last_updated": "2024-01-01T12:00:00Z",
                "message_count": 10
            }
        ]
        return {"sessions": sessions}
    except Exception as e:
        logger.error(f"获取会话列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取会话列表失败: {str(e)}")

@chat_router.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    """删除会话"""
    try:
        # 这里应该从消息管理器删除会话
        return {"message": f"会话 {session_id} 已删除", "status": "success"}
    except Exception as e:
        logger.error(f"删除会话失败: {e}")
        raise HTTPException(status_code=500, detail=f"删除会话失败: {str(e)}")
