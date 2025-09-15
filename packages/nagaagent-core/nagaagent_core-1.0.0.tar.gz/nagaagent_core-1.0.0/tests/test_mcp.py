"""
MCP模块测试
"""

import pytest
import asyncio
import json
from unittest.mock import Mock, AsyncMock
from NagaAgent_core.mcp import MCPManager, Handoff, HandoffError, HandoffInputData

class TestHandoffInputData:
    """测试Handoff输入数据"""
    
    def test_create_basic(self):
        """测试基本创建"""
        data = HandoffInputData.create()
        assert data.input_history == ()
        assert data.pre_handoff_items == ()
        assert data.new_items == ()
        assert data.context is None
        assert data.metadata is None
    
    def test_create_with_data(self):
        """测试带数据创建"""
        data = HandoffInputData.create(
            input_history="test_history",
            pre_items=("item1", "item2"),
            new_items=("new1", "new2"),
            context={"key": "value"},
            metadata={"meta": "data"}
        )
        assert data.input_history == "test_history"
        assert data.pre_handoff_items == ("item1", "item2")
        assert data.new_items == ("new1", "new2")
        assert data.context == {"key": "value"}
        assert data.metadata == {"meta": "data"}

class TestHandoff:
    """测试Handoff类"""
    
    @pytest.fixture
    def mock_callback(self):
        """创建模拟回调函数"""
        return AsyncMock(return_value="test_result")
    
    @pytest.fixture
    def handoff(self, mock_callback):
        """创建Handoff实例"""
        return Handoff(
            tool_name="test_tool",
            tool_description="测试工具",
            input_json_schema={"type": "object"},
            agent_name="TestAgent",
            on_invoke_handoff=mock_callback
        )
    
    @pytest.mark.asyncio
    async def test_invoke_without_input(self, handoff):
        """测试无输入调用"""
        result = await handoff.invoke("test_context")
        assert result == "test_result"
        handoff.on_invoke_handoff.assert_called_once_with("test_context", None)
    
    @pytest.mark.asyncio
    async def test_invoke_with_input(self, handoff):
        """测试带输入调用"""
        input_json = '{"param": "value"}'
        result = await handoff.invoke("test_context", input_json)
        assert result == "test_result"
        handoff.on_invoke_handoff.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_invoke_invalid_json(self, handoff):
        """测试无效JSON输入"""
        with pytest.raises(HandoffError):
            await handoff.invoke("test_context", "invalid_json")
    
    @pytest.mark.asyncio
    async def test_invoke_callback_error(self, handoff):
        """测试回调函数错误"""
        handoff.on_invoke_handoff.side_effect = Exception("Callback error")
        
        with pytest.raises(HandoffError):
            await handoff.invoke("test_context")

class TestMCPManager:
    """测试MCP管理器"""
    
    @pytest.fixture
    def manager(self):
        """创建MCP管理器实例"""
        return MCPManager()
    
    def test_register_handoff(self, manager):
        """测试注册handoff服务"""
        manager.register_handoff(
            service_name="test_service",
            tool_name="test_tool",
            tool_description="测试工具",
            input_schema={"type": "object"},
            agent_name="TestAgent"
        )
        
        assert "test_service" in manager.services
        service_info = manager.services["test_service"]
        assert service_info["tool_name"] == "test_tool"
        assert service_info["tool_description"] == "测试工具"
        assert service_info["agent_name"] == "TestAgent"
    
    def test_register_duplicate_service(self, manager):
        """测试注册重复服务"""
        # 第一次注册
        manager.register_handoff(
            service_name="test_service",
            tool_name="test_tool",
            tool_description="测试工具",
            input_schema={"type": "object"},
            agent_name="TestAgent"
        )
        
        # 第二次注册（应该被忽略）
        manager.register_handoff(
            service_name="test_service",
            tool_name="different_tool",
            tool_description="不同工具",
            input_schema={"type": "object"},
            agent_name="DifferentAgent"
        )
        
        # 验证第一次注册的信息保持不变
        service_info = manager.services["test_service"]
        assert service_info["tool_name"] == "test_tool"
        assert service_info["agent_name"] == "TestAgent"
    
    @pytest.mark.asyncio
    async def test_handoff_success(self, manager):
        """测试成功的handoff调用"""
        # 注册服务
        manager.register_handoff(
            service_name="test_service",
            tool_name="test_tool",
            tool_description="测试工具",
            input_schema={"type": "object"},
            agent_name="TestAgent"
        )
        
        # 执行handoff
        result = await manager.handoff("test_service", {"param": "value"})
        assert "Handoff执行完成" in result
    
    @pytest.mark.asyncio
    async def test_handoff_nonexistent_service(self, manager):
        """测试不存在的服务handoff"""
        with pytest.raises(HandoffError):
            await manager.handoff("nonexistent_service", {"param": "value"})
    
    @pytest.mark.asyncio
    async def test_connect_service(self, manager):
        """测试连接服务"""
        result = await manager.connect_service("test_service")
        # 由于是模拟实现，应该返回None
        assert result is None
    
    @pytest.mark.asyncio
    async def test_get_service_tools(self, manager):
        """测试获取服务工具"""
        tools = await manager.get_service_tools("test_service")
        assert isinstance(tools, list)
    
    @pytest.mark.asyncio
    async def test_call_service_tool(self, manager):
        """测试调用服务工具"""
        result = await manager.call_service_tool("test_service", "test_tool", {"param": "value"})
        assert "调用成功" in result
    
    @pytest.mark.asyncio
    async def test_unified_call_handoff(self, manager):
        """测试统一调用handoff服务"""
        # 注册服务
        manager.register_handoff(
            service_name="test_service",
            tool_name="test_tool",
            tool_description="测试工具",
            input_schema={"type": "object"},
            agent_name="TestAgent"
        )
        
        result = await manager.unified_call("test_service", "test_tool", {"param": "value"})
        assert isinstance(result, str)
    
    @pytest.mark.asyncio
    async def test_unified_call_mcp(self, manager):
        """测试统一调用MCP服务"""
        result = await manager.unified_call("mcp_service", "mcp_tool", {"param": "value"})
        assert "调用成功" in result
    
    def test_get_available_services(self, manager):
        """测试获取可用服务"""
        # 注册一些服务
        manager.register_handoff(
            service_name="service1",
            tool_name="tool1",
            tool_description="工具1",
            input_schema={"type": "object"},
            agent_name="Agent1"
        )
        
        manager.register_handoff(
            service_name="service2",
            tool_name="tool2",
            tool_description="工具2",
            input_schema={"type": "object"},
            agent_name="Agent2"
        )
        
        services = manager.get_available_services()
        assert "service1" in services
        assert "service2" in services
        assert len(services) == 2
    
    def test_get_available_services_filtered(self, manager):
        """测试获取过滤后的服务信息"""
        manager.register_handoff(
            service_name="test_service",
            tool_name="test_tool",
            tool_description="测试工具",
            input_schema={"type": "object"},
            agent_name="TestAgent"
        )
        
        filtered_services = manager.get_available_services_filtered()
        assert "test_service" in filtered_services
        service_info = filtered_services["test_service"]
        assert service_info["name"] == "test_tool"
        assert service_info["description"] == "测试工具"
        assert service_info["agent"] == "TestAgent"
    
    def test_query_service_by_name(self, manager):
        """测试按名称查询服务"""
        manager.register_handoff(
            service_name="test_service",
            tool_name="test_tool",
            tool_description="测试工具",
            input_schema={"type": "object"},
            agent_name="TestAgent"
        )
        
        service_info = manager.query_service_by_name("test_service")
        assert service_info is not None
        assert service_info["tool_name"] == "test_tool"
        
        # 查询不存在的服务
        nonexistent = manager.query_service_by_name("nonexistent")
        assert nonexistent is None
    
    def test_query_services_by_capability(self, manager):
        """测试按能力查询服务"""
        manager.register_handoff(
            service_name="search_service",
            tool_name="search",
            tool_description="搜索工具，用于查找信息",
            input_schema={"type": "object"},
            agent_name="SearchAgent"
        )
        
        manager.register_handoff(
            service_name="translate_service",
            tool_name="translate",
            tool_description="翻译工具，用于语言转换",
            input_schema={"type": "object"},
            agent_name="TranslateAgent"
        )
        
        # 查询搜索相关服务
        search_services = manager.query_services_by_capability("搜索")
        assert len(search_services) == 1
        assert search_services[0]["service_name"] == "search_service"
        
        # 查询翻译相关服务
        translate_services = manager.query_services_by_capability("翻译")
        assert len(translate_services) == 1
        assert translate_services[0]["service_name"] == "translate_service"
    
    def test_get_service_statistics(self, manager):
        """测试获取服务统计"""
        # 空管理器
        stats = manager.get_service_statistics()
        assert stats["total_services"] == 0
        assert stats["services"] == []
        
        # 添加服务后
        manager.register_handoff(
            service_name="test_service",
            tool_name="test_tool",
            tool_description="测试工具",
            input_schema={"type": "object"},
            agent_name="TestAgent"
        )
        
        stats = manager.get_service_statistics()
        assert stats["total_services"] == 1
        assert "test_service" in stats["services"]
    
    def test_get_service_tools(self, manager):
        """测试获取服务工具信息"""
        manager.register_handoff(
            service_name="test_service",
            tool_name="test_tool",
            tool_description="测试工具",
            input_schema={"type": "object", "properties": {"param": {"type": "string"}}},
            agent_name="TestAgent"
        )
        
        tools = manager.get_service_tools("test_service")
        assert len(tools) == 1
        tool_info = tools[0]
        assert tool_info["name"] == "test_tool"
        assert tool_info["description"] == "测试工具"
        assert "schema" in tool_info
        
        # 不存在的服务
        nonexistent_tools = manager.get_service_tools("nonexistent")
        assert nonexistent_tools == []
    
    def test_format_available_services(self, manager):
        """测试格式化可用服务信息"""
        # 空管理器
        formatted = manager.format_available_services()
        assert "没有可用的服务" in formatted
        
        # 添加服务后
        manager.register_handoff(
            service_name="test_service",
            tool_name="test_tool",
            tool_description="测试工具",
            input_schema={"type": "object"},
            agent_name="TestAgent"
        )
        
        formatted = manager.format_available_services()
        assert "可用服务列表" in formatted
        assert "test_service" in formatted
        assert "测试工具" in formatted
    
    @pytest.mark.asyncio
    async def test_cleanup(self, manager):
        """测试清理资源"""
        # 应该不抛出异常
        await manager.cleanup()

@pytest.mark.asyncio
async def test_integration():
    """集成测试"""
    manager = MCPManager()
    
    # 注册多个服务
    services = [
        {
            "service_name": "search_service",
            "tool_name": "search",
            "tool_description": "搜索服务",
            "input_schema": {"type": "object", "properties": {"query": {"type": "string"}}},
            "agent_name": "SearchAgent"
        },
        {
            "service_name": "translate_service",
            "tool_name": "translate",
            "tool_description": "翻译服务",
            "input_schema": {"type": "object", "properties": {"text": {"type": "string"}}},
            "agent_name": "TranslateAgent"
        }
    ]
    
    for service_config in services:
        manager.register_handoff(**service_config)
    
    # 验证服务注册
    available_services = manager.get_available_services()
    assert len(available_services) == 2
    assert "search_service" in available_services
    assert "translate_service" in available_services
    
    # 测试服务调用
    search_result = await manager.handoff("search_service", {"query": "Python教程"})
    assert isinstance(search_result, str)
    
    translate_result = await manager.handoff("translate_service", {"text": "Hello"})
    assert isinstance(translate_result, str)
    
    # 测试统计信息
    stats = manager.get_service_statistics()
    assert stats["total_services"] == 2
    
    # 清理资源
    await manager.cleanup()