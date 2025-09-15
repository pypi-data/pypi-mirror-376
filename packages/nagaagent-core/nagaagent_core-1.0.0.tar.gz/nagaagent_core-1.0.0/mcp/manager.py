"""
MCP服务管理器

负责管理所有MCP服务的连接和调用
"""

import asyncio
import logging
import inspect
from typing import Dict, Optional, List, Any, Callable, Awaitable, Generic, TypeVar, Union, cast
from contextlib import AsyncExitStack
import sys
from pydantic import BaseModel, TypeAdapter
from dataclasses import dataclass
import json
from datetime import datetime

logger = logging.getLogger("MCPManager")

TContext = TypeVar("TContext")
THandoffInput = TypeVar("THandoffInput")

class HandoffError(Exception):
    """Handoff基础异常类"""
    pass

class ModelBehaviorError(HandoffError):
    """模型行为异常"""
    pass

class HandoffValidationError(HandoffError):
    """Handoff数据验证异常"""
    pass

class HandoffConnectionError(HandoffError):
    """Handoff连接异常"""
    pass

@dataclass
class HandoffInputData:
    """Handoff输入数据结构"""
    input_history: Union[str, tuple[Any, ...]] #历史输入
    pre_handoff_items: tuple[Any, ...] #handoff前的items
    new_items: tuple[Any, ...] #当前turn生成的items
    context: Optional[Dict[str, Any]] = None #上下文数据
    metadata: Optional[Dict[str, Any]] = None #元数据

    @classmethod
    def create(cls, 
        input_history: Any = None,
        pre_items: Any = None,
        new_items: Any = None,
        context: Dict[str, Any] = None,
        metadata: Dict[str, Any] = None
    ) -> 'HandoffInputData':
        """创建HandoffInputData实例"""
        return cls(
            input_history=input_history if input_history is not None else (),
            pre_handoff_items=pre_items if pre_items is not None else (),
            new_items=new_items if new_items is not None else (),
            context=context,
            metadata=metadata
        )

def remove_tools_filter(messages: list) -> list:
    """移除工具调用的过滤器"""
    return [msg for msg in messages if not (isinstance(msg, dict) and msg.get('role') == 'tool')]

@dataclass
class Handoff(Generic[TContext]):
    """Handoff配置类"""
    tool_name: str
    tool_description: str
    input_json_schema: dict[str, Any]
    agent_name: str
    on_invoke_handoff: Callable[[Any, str], Awaitable[Any]]
    strict_json_schema: bool = True
    
    async def invoke(self, ctx: Any, input_json: Optional[str] = None) -> Any:
        """执行handoff调用"""
        if self.input_json_schema and not input_json:
            raise ModelBehaviorError("Handoff需要输入但未提供")
            
        try:
            if input_json:
                # 验证输入
                type_adapter = TypeAdapter(dict[str, Any])
                validated_input = type_adapter.validate_json(
                    input_json,
                    strict=self.strict_json_schema
                )
            else:
                validated_input = None
                
            # 验证回调函数签名
            sig = inspect.signature(self.on_invoke_handoff)
            if len(sig.parameters) != 2:
                raise HandoffValidationError(
                    "Handoff回调函数必须接受两个参数(context, input)"
                )
                
            return await self.on_invoke_handoff(ctx, validated_input)
        except Exception as e:
            if isinstance(e, HandoffError):
                raise
            raise HandoffError(f"Handoff执行失败: {str(e)}")

class MCPManager:
    """MCP服务管理器，负责管理所有MCP服务的连接和调用"""
    
    def __init__(self):
        """初始化MCP管理器"""
        self.services = {}
        self.tools_cache = {}
        self.exit_stack = AsyncExitStack()
        self.handoffs = {} # 服务对应的handoff对象
        self.handoff_filters = {} # 服务对应的handoff过滤器
        self.handoff_callbacks = {} # 服务对应的handoff回调
        self.logger = logging.getLogger("MCPManager")
        logger.info("MCPManager初始化完成")
        
    def register_handoff(
        self,
        service_name: str,
        tool_name: str,
        tool_description: str,
        input_schema: dict,
        agent_name: str,
        filters=None,
        strict_schema=False
    ):
        """注册handoff服务"""
        if service_name in self.services:
            logger.warning(f"服务{service_name}已注册，跳过重复注册")
            return
            
        self.services[service_name] = {
            "tool_name": tool_name,
            "tool_description": tool_description,
            "input_schema": input_schema,
            "agent_name": agent_name,
            "filter_fn": remove_tools_filter,  # 使用函数而不是类实例
            "strict_schema": strict_schema
        }
        
        logger.info(f"注册handoff服务: {service_name}")
        
    async def _default_handoff_callback(
        self,
        ctx: Any,
        input_json: Optional[str]
    ) -> Any:
        """默认的handoff回调处理"""
        return None
            
    async def handoff(
        self,
        service_name: str,
        task: dict,
        input_history: Any = None,
        pre_items: Any = None,
        new_items: Any = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """执行handoff调用"""
        try:
            if service_name not in self.services:
                raise HandoffConnectionError(f"服务 {service_name} 未注册")
            
            service_info = self.services[service_name]
            
            # 创建handoff输入数据
            handoff_data = HandoffInputData.create(
                input_history=input_history,
                pre_items=pre_items,
                new_items=new_items,
                metadata=metadata
            )
            
            # 获取handoff对象
            handoff_key = f"{service_name}_{service_info['tool_name']}"
            if handoff_key in self.handoffs:
                handoff = self.handoffs[handoff_key]
                result = await handoff.invoke(handoff_data, json.dumps(task))
                return str(result)
            else:
                # 使用默认回调
                result = await self._default_handoff_callback(handoff_data, json.dumps(task))
                return str(result) if result is not None else "Handoff执行完成"
                
        except Exception as e:
            error_msg = f"Handoff执行失败: {str(e)}"
            logger.error(error_msg)
            return error_msg
    
    async def connect_service(self, service_name: str) -> Optional[Any]:
        """连接MCP服务"""
        try:
            # 这里应该实现实际的MCP服务连接逻辑
            # 由于原代码中使用了具体的MCP客户端，这里提供一个简化版本
            logger.info(f"连接MCP服务: {service_name}")
            return None
        except Exception as e:
            logger.error(f"连接服务 {service_name} 失败: {e}")
            return None
    
    async def get_service_tools(self, service_name: str) -> list:
        """获取服务工具列表"""
        try:
            if service_name in self.tools_cache:
                return self.tools_cache[service_name]
            
            # 这里应该实现获取工具列表的逻辑
            tools = []
            self.tools_cache[service_name] = tools
            return tools
            
        except Exception as e:
            logger.error(f"获取服务 {service_name} 工具列表失败: {e}")
            return []
    
    async def call_service_tool(self, service_name: str, tool_name: str, args: dict):
        """调用服务工具"""
        try:
            logger.info(f"调用服务工具: {service_name}.{tool_name}")
            # 这里应该实现实际的工具调用逻辑
            return f"工具 {service_name}.{tool_name} 调用成功"
        except Exception as e:
            logger.error(f"调用工具 {service_name}.{tool_name} 失败: {e}")
            return None

    async def unified_call(self, service_name: str, tool_name: str, args: dict):
        """统一调用接口，支持MCP服务和Agent服务"""
        try:
            # 首先尝试作为handoff服务调用
            if service_name in self.services:
                return await self.handoff(service_name, args)
            
            # 然后尝试作为MCP服务调用
            return await self.call_service_tool(service_name, tool_name, args)
            
        except Exception as e:
            logger.error(f"统一调用失败 {service_name}.{tool_name}: {str(e)}")
            return f"调用失败: {str(e)}"
            
    def get_available_services(self) -> list:
        """获取可用服务列表"""
        return list(self.services.keys())
    
    def get_available_services_filtered(self) -> dict:
        """获取过滤后的可用服务信息"""
        filtered_services = {}
        for service_name, service_info in self.services.items():
            filtered_services[service_name] = {
                "name": service_info["tool_name"],
                "description": service_info["tool_description"],
                "agent": service_info["agent_name"]
            }
        return filtered_services
    
    def query_service_by_name(self, service_name: str) -> Optional[Dict[str, Any]]:
        """根据名称查询服务"""
        if service_name in self.services:
            return self.services[service_name]
        return None
    
    def query_services_by_capability(self, capability: str) -> List[Dict[str, Any]]:
        """根据能力查询服务"""
        matching_services = []
        for service_name, service_info in self.services.items():
            if capability.lower() in service_info["tool_description"].lower():
                matching_services.append({
                    "service_name": service_name,
                    **service_info
                })
        return matching_services
    
    def get_service_statistics(self) -> Dict[str, Any]:
        """获取服务统计信息"""
        return {
            "total_services": len(self.services),
            "services": list(self.services.keys()),
            "timestamp": datetime.now().isoformat()
        }
    
    def get_service_tools(self, service_name: str) -> List[Dict[str, Any]]:
        """获取服务工具信息"""
        if service_name in self.services:
            service_info = self.services[service_name]
            return [{
                "name": service_info["tool_name"],
                "description": service_info["tool_description"],
                "schema": service_info["input_schema"]
            }]
        return []
    
    def format_available_services(self) -> str:
        """格式化可用服务信息为字符串"""
        if not self.services:
            return "当前没有可用的服务"
        
        result = "可用服务列表:\n"
        for service_name, service_info in self.services.items():
            result += f"- {service_name}: {service_info['tool_description']}\n"
        
        return result
    
    def auto_register_services(self):
        """自动注册所有MCP服务"""
        try:
            from .registry import scan_and_register_mcp_agents
            scan_and_register_mcp_agents()
            logger.info("MCP服务自动注册完成")
        except Exception as e:
            logger.error(f"MCP服务自动注册失败: {e}")
    
    async def cleanup(self):
        """清理资源"""
        try:
            await self.exit_stack.aclose()
            logger.info("MCPManager资源清理完成")
        except Exception as e:
            logger.error(f"资源清理失败: {e}")

def get_mcp_manager():
    """获取MCP管理器实例"""
    return MCPManager()