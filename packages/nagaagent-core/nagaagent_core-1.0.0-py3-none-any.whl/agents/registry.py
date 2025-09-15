"""
Agent注册表
"""

import json
import logging
import importlib
import inspect
from pathlib import Path
from typing import Dict, Any, Optional, List, Type
from .base import BaseAgent

logger = logging.getLogger(__name__)

class AgentRegistry:
    """Agent服务注册表"""
    
    def __init__(self):
        self.agents: Dict[str, BaseAgent] = {}
        self.agent_classes: Dict[str, Type[BaseAgent]] = {}
        self.manifests: Dict[str, Dict[str, Any]] = {}
    
    def register_agent_class(self, name: str, agent_class: Type[BaseAgent]):
        """注册Agent类"""
        if not issubclass(agent_class, BaseAgent):
            raise ValueError(f"Agent类 {agent_class} 必须继承自BaseAgent")
        
        self.agent_classes[name] = agent_class
        logger.info(f"注册Agent类: {name}")
    
    def create_agent(self, name: str, config: Dict[str, Any] = None) -> Optional[BaseAgent]:
        """创建Agent实例"""
        if name not in self.agent_classes:
            logger.error(f"未找到Agent类: {name}")
            return None
        
        try:
            agent_class = self.agent_classes[name]
            agent = agent_class()
            
            # 验证配置
            if config and not agent.validate_config(config):
                logger.error(f"Agent配置验证失败: {name}")
                return None
            
            # 初始化Agent
            if not agent.initialize():
                logger.error(f"Agent初始化失败: {name}")
                return None
            
            self.agents[name] = agent
            logger.info(f"创建Agent实例: {name}")
            return agent
            
        except Exception as e:
            logger.error(f"创建Agent失败 {name}: {e}")
            return None
    
    def get_agent(self, name: str) -> Optional[BaseAgent]:
        """获取Agent实例"""
        return self.agents.get(name)
    
    def remove_agent(self, name: str) -> bool:
        """移除Agent实例"""
        if name in self.agents:
            agent = self.agents[name]
            # 清理资源
            agent.cleanup()
            del self.agents[name]
            logger.info(f"移除Agent: {name}")
            return True
        return False
    
    def list_agents(self) -> List[str]:
        """列出所有Agent名称"""
        return list(self.agents.keys())
    
    def list_agent_classes(self) -> List[str]:
        """列出所有Agent类名称"""
        return list(self.agent_classes.keys())
    
    def get_agent_info(self, name: str) -> Optional[Dict[str, Any]]:
        """获取Agent信息"""
        agent = self.get_agent(name)
        if agent:
            return agent.get_info()
        return None
    
    def get_all_agents_info(self) -> Dict[str, Dict[str, Any]]:
        """获取所有Agent信息"""
        return {
            name: agent.get_info() 
            for name, agent in self.agents.items()
        }
    
    def load_manifest(self, manifest_path: Path) -> Optional[Dict[str, Any]]:
        """加载manifest文件"""
        try:
            with open(manifest_path, 'r', encoding='utf-8') as f:
                manifest = json.load(f)
            return manifest
        except Exception as e:
            logger.error(f"加载manifest失败 {manifest_path}: {e}")
            return None
    
    def scan_agents_directory(self, agents_dir: Path) -> List[str]:
        """扫描Agent目录"""
        discovered_agents = []
        
        if not agents_dir.exists():
            logger.warning(f"Agent目录不存在: {agents_dir}")
            return discovered_agents
        
        for agent_dir in agents_dir.iterdir():
            if not agent_dir.is_dir():
                continue
            
            manifest_path = agent_dir / "agent-manifest.json"
            if not manifest_path.exists():
                continue
            
            manifest = self.load_manifest(manifest_path)
            if not manifest:
                continue
            
            agent_name = manifest.get("name")
            if not agent_name:
                continue
            
            # 尝试加载Agent模块
            try:
                module_name = f"agents.{agent_dir.name}"
                module = importlib.import_module(module_name)
                
                # 查找Agent类
                for name, obj in inspect.getmembers(module):
                    if (inspect.isclass(obj) and 
                        issubclass(obj, BaseAgent) and 
                        obj != BaseAgent):
                        self.register_agent_class(agent_name, obj)
                        discovered_agents.append(agent_name)
                        break
                        
            except Exception as e:
                logger.error(f"加载Agent模块失败 {agent_dir.name}: {e}")
        
        logger.info(f"发现 {len(discovered_agents)} 个Agent: {discovered_agents}")
        return discovered_agents
    
    async def call_agent(self, name: str, data: dict) -> str:
        """调用Agent"""
        agent = self.get_agent(name)
        if not agent:
            return f"Agent {name} 不存在"
        
        try:
            result = await agent.handle_handoff(data)
            return result
        except Exception as e:
            logger.error(f"调用Agent失败 {name}: {e}")
            return f"Agent调用失败: {str(e)}"
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "total_agents": len(self.agents),
            "total_classes": len(self.agent_classes),
            "agents": list(self.agents.keys()),
            "classes": list(self.agent_classes.keys())
        }

# 全局注册表实例
_agent_registry = None

def get_agent_registry() -> AgentRegistry:
    """获取全局Agent注册表实例"""
    global _agent_registry
    if _agent_registry is None:
        _agent_registry = AgentRegistry()
    return _agent_registry
