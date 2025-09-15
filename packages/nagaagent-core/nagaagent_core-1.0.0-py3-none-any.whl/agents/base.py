"""
基础Agent类
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class BaseAgent(ABC):
    """Agent基础类"""
    
    def __init__(self, name: str, instructions: str):
        self.name = name
        self.instructions = instructions
        self.logger = logging.getLogger(f"Agent.{name}")
    
    @abstractmethod
    async def handle_handoff(self, data: dict) -> str:
        """处理handoff请求"""
        pass
    
    def get_info(self) -> Dict[str, Any]:
        """获取Agent信息"""
        return {
            "name": self.name,
            "instructions": self.instructions,
            "type": self.__class__.__name__
        }
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """验证配置"""
        return True
    
    async def initialize(self) -> bool:
        """初始化Agent"""
        self.logger.info(f"初始化Agent: {self.name}")
        return True
    
    async def cleanup(self):
        """清理资源"""
        self.logger.info(f"清理Agent资源: {self.name}")
    
    def __str__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name})"
    
    def __repr__(self) -> str:
        return self.__str__()
