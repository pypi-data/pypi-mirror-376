"""
MCP服务注册表

负责扫描和注册MCP服务
"""

import os
import json
import importlib
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

# MCP服务注册表
MCP_REGISTRY: Dict[str, Any] = {}

def load_manifest_file(manifest_path: Path) -> Optional[Dict[str, Any]]:
    """加载manifest文件"""
    try:
        with open(manifest_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"加载manifest文件失败 {manifest_path}: {e}")
        return None

def create_agent_instance(manifest: Dict[str, Any]) -> Optional[Any]:
    """根据manifest创建agent实例"""
    try:
        entry_point = manifest.get('entryPoint', {})
        module_name = entry_point.get('module')
        class_name = entry_point.get('class')
        
        if not module_name or not class_name:
            logger.error("manifest中缺少entryPoint信息")
            return None
        
        # 动态导入模块
        module = importlib.import_module(module_name)
        agent_class = getattr(module, class_name)
        
        # 创建实例
        agent_instance = agent_class()
        return agent_instance
        
    except Exception as e:
        logger.error(f"创建agent实例失败: {e}")
        return None

def scan_and_register_mcp_agents(mcp_dir: str = 'mcpserver') -> list:
    """扫描并注册MCP agents"""
    registered_agents = []
    
    try:
        mcp_path = Path(mcp_dir)
        if not mcp_path.exists():
            logger.warning(f"MCP目录不存在: {mcp_dir}")
            return registered_agents
        
        # 扫描所有子目录
        for agent_dir in mcp_path.iterdir():
            if not agent_dir.is_dir():
                continue
                
            manifest_path = agent_dir / 'agent-manifest.json'
            if not manifest_path.exists():
                continue
            
            # 加载manifest
            manifest = load_manifest_file(manifest_path)
            if not manifest:
                continue
            
            agent_name = manifest.get('name', agent_dir.name)
            
            # 创建agent实例
            agent_instance = create_agent_instance(manifest)
            if agent_instance:
                MCP_REGISTRY[agent_name] = agent_instance
                registered_agents.append(agent_name)
                logger.info(f"注册MCP Agent: {agent_name}")
            else:
                logger.error(f"创建Agent实例失败: {agent_name}")
    
    except Exception as e:
        logger.error(f"扫描MCP agents失败: {e}")
    
    return registered_agents

def get_service_info(service_name: str) -> Optional[Dict[str, Any]]:
    """获取服务信息"""
    if service_name in MCP_REGISTRY:
        agent = MCP_REGISTRY[service_name]
        return {
            "name": service_name,
            "type": "mcp_agent",
            "instance": agent,
            "has_handoff": hasattr(agent, 'handle_handoff')
        }
    return None

def get_available_tools(service_name: str) -> List[Dict[str, Any]]:
    """获取服务可用工具"""
    if service_name not in MCP_REGISTRY:
        return []
    
    agent = MCP_REGISTRY[service_name]
    tools = []
    
    # 检查是否有handle_handoff方法
    if hasattr(agent, 'handle_handoff'):
        tools.append({
            "name": "handle_handoff",
            "description": "处理handoff调用",
            "type": "handoff"
        })
    
    # 检查其他方法
    for attr_name in dir(agent):
        if not attr_name.startswith('_') and callable(getattr(agent, attr_name)):
            if attr_name != 'handle_handoff':
                tools.append({
                    "name": attr_name,
                    "description": f"调用{attr_name}方法",
                    "type": "method"
                })
    
    return tools

def get_all_services_info() -> Dict[str, Any]:
    """获取所有服务信息"""
    services_info = {}
    for service_name in MCP_REGISTRY.keys():
        services_info[service_name] = get_service_info(service_name)
    return services_info

def query_services_by_capability(capability: str) -> List[str]:
    """根据能力查询服务"""
    matching_services = []
    for service_name, agent in MCP_REGISTRY.items():
        # 检查agent是否有相关能力
        if hasattr(agent, 'instructions'):
            instructions = getattr(agent, 'instructions', '')
            if capability.lower() in instructions.lower():
                matching_services.append(service_name)
    return matching_services

def get_service_statistics() -> Dict[str, Any]:
    """获取服务统计信息"""
    return {
        "total_services": len(MCP_REGISTRY),
        "services": list(MCP_REGISTRY.keys()),
        "service_types": {
            "mcp_agent": len([s for s in MCP_REGISTRY.values() if hasattr(s, 'handle_handoff')])
        }
    }

def auto_register_mcp():
    """自动注册MCP服务"""
    logger.info("开始自动注册MCP服务")
    registered = scan_and_register_mcp_agents()
    logger.info(f"MCP服务注册完成，共注册 {len(registered)} 个服务")
    return registered