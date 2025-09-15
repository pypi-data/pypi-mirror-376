"""
系统API路由
"""

import logging
from typing import Dict, List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

logger = logging.getLogger(__name__)

# 响应模型
class SystemInfoResponse(BaseModel):
    version: str
    status: str
    available_services: List[str]
    api_key_configured: bool

class HealthResponse(BaseModel):
    status: str
    timestamp: str
    uptime: str

# 创建路由器
system_router = APIRouter(prefix="/system", tags=["system"])

@system_router.get("/", response_model=Dict[str, str])
async def root():
    """API根路径"""
    return {
        "name": "NagaAgent API",
        "version": "3.0",
        "status": "running",
        "docs": "/docs",
        "websocket": "/ws/mcplog"
    }

@system_router.get("/health", response_model=HealthResponse)
async def health_check():
    """健康检查"""
    import time
    return HealthResponse(
        status="healthy",
        timestamp=str(int(time.time())),
        uptime="0:00:00"  # 这里应该计算实际运行时间
    )

@system_router.get("/info", response_model=SystemInfoResponse)
async def get_system_info():
    """获取系统信息"""
    try:
        # 这里应该从配置系统获取信息
        available_services = [
            "example_service"
        ]
        
        return SystemInfoResponse(
            version="3.0.0",
            status="running",
            available_services=available_services,
            api_key_configured=True  # 这里应该检查实际配置
        )
    except Exception as e:
        logger.error(f"获取系统信息失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取系统信息失败: {str(e)}")

@system_router.post("/devmode")
async def toggle_devmode():
    """切换开发模式"""
    try:
        # 这里应该实现开发模式切换逻辑
        return {"message": "开发模式已切换", "status": "success"}
    except Exception as e:
        logger.error(f"切换开发模式失败: {e}")
        raise HTTPException(status_code=500, detail=f"切换开发模式失败: {str(e)}")

@system_router.get("/memory/stats")
async def get_memory_stats():
    """获取内存统计信息"""
    try:
        import psutil
        memory = psutil.virtual_memory()
        return {
            "total": memory.total,
            "available": memory.available,
            "percent": memory.percent,
            "used": memory.used,
            "free": memory.free
        }
    except ImportError:
        return {"error": "psutil not available"}
    except Exception as e:
        logger.error(f"获取内存统计失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取内存统计失败: {str(e)}")
