"""
NagaAgent API服务器
"""

import asyncio
import logging
import uvicorn
from contextlib import asynccontextmanager
from typing import Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse

from .websocket import ConnectionManager
from .routes import chat_router, mcp_router, system_router

logger = logging.getLogger(__name__)

class NagaAPIServer:
    """NagaAgent API服务器"""
    
    def __init__(self, 
                 host: str = "127.0.0.1", 
                 port: int = 8000,
                 title: str = "NagaAgent API",
                 description: str = "智能对话助手API服务",
                 version: str = "3.0"):
        self.host = host
        self.port = port
        self.connection_manager = ConnectionManager()
        
        # 创建FastAPI应用
        self.app = FastAPI(
            title=title,
            description=description,
            version=version,
            lifespan=self._lifespan
        )
        
        # 配置CORS
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],  # 生产环境建议限制具体域名
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # 注册路由
        self._setup_routes()
        
        # 设置WebSocket
        self._setup_websocket()
    
    def _setup_routes(self):
        """设置API路由"""
        # 注册路由
        self.app.include_router(chat_router)
        self.app.include_router(mcp_router)
        self.app.include_router(system_router)
        
        # 根路径
        @self.app.get("/")
        async def root():
            return {
                "name": "NagaAgent API",
                "version": "3.0",
                "status": "running",
                "docs": "/docs",
                "websocket": "/ws/mcplog"
            }
    
    def _setup_websocket(self):
        """设置WebSocket端点"""
        @self.app.websocket("/ws/mcplog")
        async def websocket_endpoint(websocket: WebSocket):
            await self.connection_manager.connect(websocket)
            try:
                while True:
                    # 接收客户端消息
                    data = await websocket.receive_text()
                    logger.info(f"收到WebSocket消息: {data}")
                    
                    # 这里可以处理具体的消息逻辑
                    # 例如转发给MCP服务等
                    
            except WebSocketDisconnect:
                self.connection_manager.disconnect(websocket)
            except Exception as e:
                logger.error(f"WebSocket错误: {e}")
                self.connection_manager.disconnect(websocket)
    
    @asynccontextmanager
    async def _lifespan(self, app: FastAPI):
        """应用生命周期管理"""
        # 启动时执行
        logger.info("🚀 NagaAgent API服务器启动中...")
        try:
            # 这里可以初始化MCP管理器等
            logger.info("✅ 初始化完成")
        except Exception as e:
            logger.error(f"❌ 初始化失败: {e}")
        
        yield
        
        # 关闭时执行
        logger.info("🔄 正在关闭NagaAgent API服务器...")
        try:
            # 清理资源
            await self.connection_manager.broadcast("服务器正在关闭")
            logger.info("✅ 资源清理完成")
        except Exception as e:
            logger.error(f"❌ 资源清理失败: {e}")
    
    def run(self, 
            host: Optional[str] = None, 
            port: Optional[int] = None,
            reload: bool = False,
            log_level: str = "info"):
        """运行API服务器"""
        host = host or self.host
        port = port or self.port
        
        print(f"🚀 启动NagaAgent API服务器...")
        print(f"📍 地址: http://{host}:{port}")
        print(f"📚 文档: http://{host}:{port}/docs")
        print(f"🔄 自动重载: {'开启' if reload else '关闭'}")
        
        uvicorn.run(
            self.app,
            host=host,
            port=port,
            reload=reload,
            log_level=log_level,
            ws_ping_interval=None,
            ws_ping_timeout=None
        )
    
    async def start_server(self, 
                          host: Optional[str] = None, 
                          port: Optional[int] = None):
        """异步启动服务器"""
        host = host or self.host
        port = port or self.port
        
        config = uvicorn.Config(
            self.app,
            host=host,
            port=port,
            log_level="info"
        )
        server = uvicorn.Server(config)
        await server.serve()
    
    def get_app(self) -> FastAPI:
        """获取FastAPI应用实例"""
        return self.app

# 便捷函数
def create_api_server(host: str = "127.0.0.1", port: int = 8000) -> NagaAPIServer:
    """创建API服务器实例"""
    return NagaAPIServer(host=host, port=port)

def run_api_server(host: str = "127.0.0.1", port: int = 8000, reload: bool = False):
    """运行API服务器"""
    server = create_api_server(host, port)
    server.run(host=host, port=port, reload=reload)
