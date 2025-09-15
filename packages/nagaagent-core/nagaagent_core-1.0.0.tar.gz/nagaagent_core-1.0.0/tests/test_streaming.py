"""
流式工具调用模块测试
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock
from NagaAgent_core.streaming import StreamingToolCallExtractor, StreamingResponseProcessor, CallbackManager

class TestCallbackManager:
    """测试回调管理器"""
    
    def test_register_callback(self):
        """测试注册回调函数"""
        manager = CallbackManager()
        
        # 测试同步回调
        def sync_callback(text):
            return f"sync: {text}"
        
        manager.register_callback("sync_test", sync_callback)
        assert manager.has_callback("sync_test")
        assert not manager.callback_types["sync_test"]  # 同步回调
        
        # 测试异步回调
        async def async_callback(text):
            return f"async: {text}"
        
        manager.register_callback("async_test", async_callback)
        assert manager.has_callback("async_test")
        assert manager.callback_types["async_test"]  # 异步回调
    
    @pytest.mark.asyncio
    async def test_call_sync_callback(self):
        """测试调用同步回调"""
        manager = CallbackManager()
        
        def sync_callback(text):
            return f"processed: {text}"
        
        manager.register_callback("sync_test", sync_callback)
        result = await manager.call_callback("sync_test", "test_input")
        assert result == "processed: test_input"
    
    @pytest.mark.asyncio
    async def test_call_async_callback(self):
        """测试调用异步回调"""
        manager = CallbackManager()
        
        async def async_callback(text):
            await asyncio.sleep(0.01)  # 模拟异步操作
            return f"async_processed: {text}"
        
        manager.register_callback("async_test", async_callback)
        result = await manager.call_callback("async_test", "test_input")
        assert result == "async_processed: test_input"
    
    @pytest.mark.asyncio
    async def test_call_nonexistent_callback(self):
        """测试调用不存在的回调"""
        manager = CallbackManager()
        result = await manager.call_callback("nonexistent", "test")
        assert result is None
    
    def test_clear_callbacks(self):
        """测试清空回调"""
        manager = CallbackManager()
        
        def test_callback(text):
            return text
        
        manager.register_callback("test", test_callback)
        assert manager.has_callback("test")
        
        manager.clear_callbacks()
        assert not manager.has_callback("test")
        assert len(manager.get_callback_names()) == 0

class TestStreamingToolCallExtractor:
    """测试流式工具调用提取器"""
    
    @pytest.fixture
    def extractor(self):
        """创建提取器实例"""
        return StreamingToolCallExtractor()
    
    @pytest.mark.asyncio
    async def test_process_text_chunk_simple(self, extractor):
        """测试处理简单文本块"""
        text_chunk = "这是一段普通文本"
        await extractor.process_text_chunk(text_chunk)
        assert extractor.text_buffer == text_chunk
    
    @pytest.mark.asyncio
    async def test_process_text_chunk_with_tool_call(self, extractor):
        """测试处理包含工具调用的文本块"""
        # 设置回调
        tool_calls = []
        def on_tool_call(tool_call, tool_type):
            tool_calls.append(tool_call)
        
        extractor.set_callbacks(on_tool_call=on_tool_call)
        
        # 处理包含工具调用的文本
        text_with_tool = '{"tool_name": "search", "args": {"query": "test"}}'
        await extractor.process_text_chunk(text_with_tool)
        
        # 验证工具调用被检测到
        assert len(tool_calls) == 1
        assert "search" in tool_calls[0]
    
    @pytest.mark.asyncio
    async def test_process_text_chunk_mixed(self, extractor):
        """测试处理混合内容"""
        text_chunks = []
        tool_calls = []
        
        def on_text_chunk(text, chunk_type):
            text_chunks.append(text)
        
        def on_tool_call(tool_call, tool_type):
            tool_calls.append(tool_call)
        
        extractor.set_callbacks(
            on_text_chunk=on_text_chunk,
            on_tool_call=on_tool_call
        )
        
        # 处理混合内容
        await extractor.process_text_chunk("开始处理")
        await extractor.process_text_chunk('{"tool_name": "test", "args": {}}')
        await extractor.process_text_chunk("处理完成")
        
        await extractor.finish_processing()
        
        # 验证结果
        assert len(text_chunks) >= 1  # 至少有一个文本块
        assert len(tool_calls) == 1   # 一个工具调用
    
    @pytest.mark.asyncio
    async def test_finish_processing(self, extractor):
        """测试完成处理"""
        text_chunks = []
        
        def on_text_chunk(text, chunk_type):
            text_chunks.append(text)
        
        extractor.set_callbacks(on_text_chunk=on_text_chunk)
        
        # 添加一些文本
        extractor.text_buffer = "未处理的文本"
        
        # 完成处理
        await extractor.finish_processing()
        
        # 验证缓冲区被清空
        assert extractor.text_buffer == ""
        assert len(text_chunks) == 1
        assert text_chunks[0] == "未处理的文本"
    
    def test_reset(self, extractor):
        """测试重置状态"""
        # 设置一些状态
        extractor.in_tool_call = True
        extractor.brace_count = 2
        extractor.text_buffer = "test"
        extractor.tool_call_buffer = "tool"
        
        # 重置
        extractor.reset()
        
        # 验证状态被重置
        assert not extractor.in_tool_call
        assert extractor.brace_count == 0
        assert extractor.text_buffer == ""
        assert extractor.tool_call_buffer == ""

class TestStreamingResponseProcessor:
    """测试流式响应处理器"""
    
    @pytest.fixture
    def processor(self):
        """创建处理器实例"""
        return StreamingResponseProcessor()
    
    @pytest.mark.asyncio
    async def test_process_ai_response(self, processor):
        """测试处理AI响应"""
        # 模拟响应流
        async def mock_stream():
            yield "Hello"
            yield " World"
            yield "!"
        
        # 设置回调
        chunks = []
        def on_text_chunk(text, chunk_type):
            chunks.append(text)
        
        callbacks = {"on_text_chunk": on_text_chunk}
        
        # 处理响应
        await processor.process_ai_response(mock_stream(), callbacks)
        
        # 验证结果
        assert len(chunks) >= 1
        assert "Hello" in processor.get_response_buffer()
    
    def test_stop_processing(self, processor):
        """测试停止处理"""
        processor.is_processing = True
        processor.stop_processing()
        assert not processor.is_processing
    
    def test_get_response_buffer(self, processor):
        """测试获取响应缓冲区"""
        processor.response_buffer = "test response"
        assert processor.get_response_buffer() == "test response"

@pytest.mark.asyncio
async def test_integration():
    """集成测试"""
    # 创建提取器
    extractor = StreamingToolCallExtractor()
    
    # 设置回调
    results = {"text_chunks": [], "tool_calls": []}
    
    def on_text_chunk(text, chunk_type):
        results["text_chunks"].append(text)
    
    def on_tool_call(tool_call, tool_type):
        results["tool_calls"].append(tool_call)
    
    extractor.set_callbacks(
        on_text_chunk=on_text_chunk,
        on_tool_call=on_tool_call
    )
    
    # 模拟复杂的流式响应
    response_parts = [
        "用户询问：",
        "请帮我搜索",
        '{"tool_name": "search", "args": {"query": "Python教程"}}',
        "相关信息。",
        "根据搜索结果，",
        "我找到了以下内容：",
        "Python是一种编程语言。"
    ]
    
    for part in response_parts:
        await extractor.process_text_chunk(part)
    
    await extractor.finish_processing()
    
    # 验证结果
    assert len(results["text_chunks"]) >= 1
    assert len(results["tool_calls"]) == 1
    assert "search" in results["tool_calls"][0]