"""
回调函数管理器 - 统一处理同步/异步回调
"""

import asyncio
import logging
from typing import Dict, Optional, Callable, Any
from functools import wraps

logger = logging.getLogger(__name__)

class CallbackManager:
    """回调函数管理器 - 统一处理同步/异步回调"""
    
    def __init__(self):
        self.callbacks = {}
        self.callback_types = {}  # 缓存回调函数类型
    
    def register_callback(self, name: str, callback: Optional[Callable]):
        """注册回调函数"""
        if callback is None:
            return
            
        self.callbacks[name] = callback
        # 检查是否为协程函数
        self.callback_types[name] = asyncio.iscoroutinefunction(callback)
        logger.debug(f"注册回调函数: {name}, 类型: {'async' if self.callback_types[name] else 'sync'}")
    
    async def call_callback(self, name: str, *args, **kwargs):
        """调用回调函数"""
        if name not in self.callbacks:
            return None
            
        callback = self.callbacks[name]
        try:
            if self.callback_types[name]:
                # 异步回调
                return await callback(*args, **kwargs)
            else:
                # 同步回调
                return callback(*args, **kwargs)
        except Exception as e:
            logger.error(f"回调函数 {name} 执行失败: {e}")
            return None
    
    def has_callback(self, name: str) -> bool:
        """检查是否有指定的回调函数"""
        return name in self.callbacks
    
    def get_callback_names(self) -> list:
        """获取所有回调函数名称"""
        return list(self.callbacks.keys())
    
    def clear_callbacks(self):
        """清空所有回调函数"""
        self.callbacks.clear()
        self.callback_types.clear()