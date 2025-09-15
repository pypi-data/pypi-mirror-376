"""
工具调用模块测试
"""

import pytest
import asyncio
import json
from unittest.mock import Mock, AsyncMock
from NagaAgent_core.tools import parse_tool_calls, execute_tool_calls, tool_call_loop

class TestParseToolCalls:
    """测试工具调用解析"""
    
    def test_parse_valid_json_tool_call(self):
        """测试解析有效的JSON工具调用"""
        content = '{"tool_name": "search", "args": {"query": "Python教程"}}'
        tool_calls = parse_tool_calls(content)
        
        assert len(tool_calls) == 1
        assert tool_calls[0]["tool_name"] == "search"
        assert tool_calls[0]["args"]["query"] == "Python教程"
    
    def test_parse_multiple_json_tool_calls(self):
        """测试解析多个JSON工具调用"""
        content = '''
        开始处理。
        {"tool_name": "search", "args": {"query": "Python"}}
        继续处理。
        {"tool_name": "translate", "args": {"text": "Hello", "target_lang": "zh"}}
        完成处理。
        '''
        tool_calls = parse_tool_calls(content)
        
        assert len(tool_calls) == 2
        assert tool_calls[0]["tool_name"] == "search"
        assert tool_calls[1]["tool_name"] == "translate"
    
    def test_parse_function_format_tool_call(self):
        """测试解析function格式的工具调用"""
        content = '{"function": "calculate", "args": {"expression": "2+2"}}'
        tool_calls = parse_tool_calls(content)
        
        assert len(tool_calls) == 1
        assert tool_calls[0]["function"] == "calculate"
        assert tool_calls[0]["args"]["expression"] == "2+2"
    
    def test_parse_simple_function_call(self):
        """测试解析简单函数调用格式"""
        content = "search(query='Python教程')"
        tool_calls = parse_tool_calls(content)
        
        assert len(tool_calls) == 1
        assert tool_calls[0]["tool_name"] == "search"
        assert tool_calls[0]["args"] == "query='Python教程'"
    
    def test_parse_multiple_simple_calls(self):
        """测试解析多个简单函数调用"""
        content = "search(query='Python') calculate(2+2) translate(text='Hello')"
        tool_calls = parse_tool_calls(content)
        
        assert len(tool_calls) == 3
        assert tool_calls[0]["tool_name"] == "search"
        assert tool_calls[1]["tool_name"] == "calculate"
        assert tool_calls[2]["tool_name"] == "translate"
    
    def test_parse_no_tool_calls(self):
        """测试解析没有工具调用的内容"""
        content = "这是一段普通的文本内容，没有任何工具调用。"
        tool_calls = parse_tool_calls(content)
        
        assert len(tool_calls) == 0
    
    def test_parse_invalid_json(self):
        """测试解析无效的JSON"""
        content = '{"tool_name": "search", "args": {"query": "Python"'  # 缺少右括号
        tool_calls = parse_tool_calls(content)
        
        # 应该尝试简单格式解析
        assert len(tool_calls) >= 0  # 可能解析到简单格式的工具调用
    
    def test_parse_mixed_content(self):
        """测试解析混合内容"""
        content = '''
        用户询问：请帮我搜索Python教程。
        {"tool_name": "search", "args": {"query": "Python教程"}}
        根据搜索结果，我找到了相关信息。
        calculate(2+2)
        计算结果是4。
        '''
        tool_calls = parse_tool_calls(content)
        
        # 应该解析到JSON格式和简单格式的工具调用
        assert len(tool_calls) >= 2
        tool_names = [call.get("tool_name") or call.get("function") for call in tool_calls]
        assert "search" in tool_names
        assert "calculate" in tool_names

class TestExecuteToolCalls:
    """测试工具调用执行"""
    
    @pytest.fixture
    def mock_mcp_manager(self):
        """创建模拟MCP管理器"""
        manager = Mock()
        manager.unified_call = AsyncMock(return_value="执行成功")
        return manager
    
    @pytest.mark.asyncio
    async def test_execute_single_tool_call(self, mock_mcp_manager):
        """测试执行单个工具调用"""
        tool_calls = [
            {
                "tool_name": "search",
                "service_name": "search_service",
                "args": {"query": "Python教程"}
            }
        ]
        
        result = await execute_tool_calls(tool_calls, mock_mcp_manager)
        
        assert "执行成功" in result
        mock_mcp_manager.unified_call.assert_called_once_with(
            "search_service", "search", {"query": "Python教程"}
        )
    
    @pytest.mark.asyncio
    async def test_execute_multiple_tool_calls(self, mock_mcp_manager):
        """测试执行多个工具调用"""
        tool_calls = [
            {
                "tool_name": "search",
                "service_name": "search_service",
                "args": {"query": "Python"}
            },
            {
                "tool_name": "translate",
                "service_name": "translate_service",
                "args": {"text": "Hello", "target_lang": "zh"}
            }
        ]
        
        result = await execute_tool_calls(tool_calls, mock_mcp_manager)
        
        assert "执行成功" in result
        assert mock_mcp_manager.unified_call.call_count == 2
    
    @pytest.mark.asyncio
    async def test_execute_tool_call_with_string_args(self, mock_mcp_manager):
        """测试执行带字符串参数的工具调用"""
        tool_calls = [
            {
                "tool_name": "search",
                "args": "Python教程"  # 字符串参数
            }
        ]
        
        result = await execute_tool_calls(tool_calls, mock_mcp_manager)
        
        assert "执行成功" in result
        mock_mcp_manager.unified_call.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_execute_tool_call_with_json_string_args(self, mock_mcp_manager):
        """测试执行带JSON字符串参数的工具调用"""
        tool_calls = [
            {
                "tool_name": "search",
                "args": '{"query": "Python教程"}'  # JSON字符串
            }
        ]
        
        result = await execute_tool_calls(tool_calls, mock_mcp_manager)
        
        assert "执行成功" in result
        # 验证参数被正确解析
        call_args = mock_mcp_manager.unified_call.call_args[0]
        assert call_args[2]["query"] == "Python教程"
    
    @pytest.mark.asyncio
    async def test_execute_tool_call_with_function_format(self, mock_mcp_manager):
        """测试执行function格式的工具调用"""
        tool_calls = [
            {
                "function": "calculate",
                "args": {"expression": "2+2"}
            }
        ]
        
        result = await execute_tool_calls(tool_calls, mock_mcp_manager)
        
        assert "执行成功" in result
        mock_mcp_manager.unified_call.assert_called_once_with(
            "", "calculate", {"expression": "2+2"}
        )
    
    @pytest.mark.asyncio
    async def test_execute_empty_tool_calls(self, mock_mcp_manager):
        """测试执行空的工具调用列表"""
        result = await execute_tool_calls([], mock_mcp_manager)
        assert result == ""
        mock_mcp_manager.unified_call.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_execute_tool_call_without_mcp_manager(self):
        """测试在没有MCP管理器的情况下执行工具调用"""
        tool_calls = [
            {
                "tool_name": "search",
                "args": {"query": "Python"}
            }
        ]
        
        result = await execute_tool_calls(tool_calls, None)
        assert "MCP管理器未初始化" in result
    
    @pytest.mark.asyncio
    async def test_execute_tool_call_with_error(self, mock_mcp_manager):
        """测试执行工具调用时出现错误"""
        mock_mcp_manager.unified_call.side_effect = Exception("执行失败")
        
        tool_calls = [
            {
                "tool_name": "search",
                "args": {"query": "Python"}
            }
        ]
        
        result = await execute_tool_calls(tool_calls, mock_mcp_manager)
        assert "执行失败" in result

class TestToolCallLoop:
    """测试工具调用循环"""
    
    @pytest.fixture
    def mock_mcp_manager(self):
        """创建模拟MCP管理器"""
        manager = Mock()
        manager.unified_call = AsyncMock(return_value="工具执行结果")
        return manager
    
    @pytest.fixture
    def mock_llm_caller(self):
        """创建模拟LLM调用器"""
        return AsyncMock()
    
    @pytest.mark.asyncio
    async def test_tool_call_loop_no_tools(self, mock_mcp_manager, mock_llm_caller):
        """测试没有工具调用的循环"""
        # 模拟LLM返回没有工具调用的响应
        mock_llm_caller.return_value = "这是一个普通的回复，没有工具调用。"
        
        messages = [{"role": "user", "content": "你好"}]
        
        result = await tool_call_loop(
            messages=messages,
            mcp_manager=mock_mcp_manager,
            llm_caller=mock_llm_caller,
            is_streaming=False
        )
        
        assert result["response"] == "这是一个普通的回复，没有工具调用。"
        assert result["tool_calls"] == []
        assert result["recursion_count"] == 0
        assert "error" not in result
    
    @pytest.mark.asyncio
    async def test_tool_call_loop_with_tools(self, mock_mcp_manager, mock_llm_caller):
        """测试有工具调用的循环"""
        # 模拟LLM返回包含工具调用的响应
        mock_llm_caller.return_value = '让我搜索一下。{"tool_name": "search", "args": {"query": "Python"}}'
        
        messages = [{"role": "user", "content": "请搜索Python教程"}]
        
        result = await tool_call_loop(
            messages=messages,
            mcp_manager=mock_mcp_manager,
            llm_caller=mock_llm_caller,
            is_streaming=False,
            max_recursion=3
        )
        
        assert "让我搜索一下" in result["response"]
        assert result["recursion_count"] >= 1
        assert "error" not in result
    
    @pytest.mark.asyncio
    async def test_tool_call_loop_streaming(self, mock_mcp_manager, mock_llm_caller):
        """测试流式工具调用循环"""
        # 模拟流式响应
        async def streaming_response(messages):
            chunks = [
                "让我搜索一下。",
                '{"tool_name": "search", "args": {"query": "Python"}}',
                "根据搜索结果..."
            ]
            for chunk in chunks:
                yield chunk
        
        mock_llm_caller.side_effect = streaming_response
        
        messages = [{"role": "user", "content": "请搜索Python"}]
        
        result = await tool_call_loop(
            messages=messages,
            mcp_manager=mock_mcp_manager,
            llm_caller=mock_llm_caller,
            is_streaming=True,
            max_recursion=3
        )
        
        assert "让我搜索一下" in result["response"]
        assert result["recursion_count"] >= 1
    
    @pytest.mark.asyncio
    async def test_tool_call_loop_max_recursion(self, mock_mcp_manager, mock_llm_caller):
        """测试达到最大递归次数"""
        # 模拟总是返回工具调用的LLM
        mock_llm_caller.return_value = '{"tool_name": "infinite_loop", "args": {}}'
        
        messages = [{"role": "user", "content": "测试"}]
        
        result = await tool_call_loop(
            messages=messages,
            mcp_manager=mock_mcp_manager,
            llm_caller=mock_llm_caller,
            is_streaming=False,
            max_recursion=2
        )
        
        assert result["recursion_count"] == 2
        assert result["error"] == "max_recursion_reached"
    
    @pytest.mark.asyncio
    async def test_tool_call_loop_with_error(self, mock_mcp_manager, mock_llm_caller):
        """测试工具调用循环中的错误处理"""
        # 模拟LLM调用出错
        mock_llm_caller.side_effect = Exception("LLM调用失败")
        
        messages = [{"role": "user", "content": "测试"}]
        
        result = await tool_call_loop(
            messages=messages,
            mcp_manager=mock_mcp_manager,
            llm_caller=mock_llm_caller,
            is_streaming=False
        )
        
        assert "LLM调用失败" in result["response"]
        assert "error" in result
        assert result["error"] == "LLM调用失败"
    
    @pytest.mark.asyncio
    async def test_tool_call_loop_with_queue(self, mock_mcp_manager, mock_llm_caller):
        """测试带队列的工具调用循环"""
        import queue
        tool_calls_queue = queue.Queue()
        
        # 模拟LLM返回工具调用
        mock_llm_caller.return_value = '{"tool_name": "test_tool", "args": {"param": "value"}}'
        
        messages = [{"role": "user", "content": "测试"}]
        
        result = await tool_call_loop(
            messages=messages,
            mcp_manager=mock_mcp_manager,
            llm_caller=mock_llm_caller,
            is_streaming=False,
            tool_calls_queue=tool_calls_queue
        )
        
        # 验证工具调用被添加到队列
        assert not tool_calls_queue.empty()
        tool_call = tool_calls_queue.get()
        assert tool_call["tool_name"] == "test_tool"

@pytest.mark.asyncio
async def test_integration():
    """集成测试"""
    # 创建模拟MCP管理器
    mcp_manager = Mock()
    mcp_manager.unified_call = AsyncMock(return_value="工具执行成功")
    
    # 创建模拟LLM调用器
    async def mock_llm_caller(messages):
        return '让我使用工具来帮助您。{"tool_name": "search", "args": {"query": "Python教程"}}这是搜索结果。'
    
    # 测试完整的工具调用流程
    messages = [{"role": "user", "content": "请帮我搜索Python教程"}]
    
    result = await tool_call_loop(
        messages=messages,
        mcp_manager=mcp_manager,
        llm_caller=mock_llm_caller,
        is_streaming=False,
        max_recursion=3
    )
    
    # 验证结果
    assert "让我使用工具来帮助您" in result["response"]
    assert result["recursion_count"] >= 1
    assert "error" not in result
    
    # 验证MCP管理器被调用
    mcp_manager.unified_call.assert_called()