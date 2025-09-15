"""
流式工具调用提取器

从AI流式响应中提取工具调用并处理
"""

import asyncio
import json
import logging
import re
from typing import Dict, Optional, Callable, Any, List
from .callbacks import CallbackManager

logger = logging.getLogger(__name__)

class StreamingToolCallExtractor:
    """流式工具调用提取器"""
    
    def __init__(self, mcp_manager=None):
        self.mcp_manager = mcp_manager
        self.callback_manager = CallbackManager()
        
        # 状态变量
        self.in_tool_call = False
        self.brace_count = 0
        self.text_buffer = ""
        self.tool_call_buffer = ""
        
        # 工具调用队列
        self.tool_calls_queue = None
        self.tool_call_detected_signal = None
        
        # 语音集成
        self.voice_integration = None
        
        logger.debug("StreamingToolCallExtractor 初始化完成")
    
    def set_callbacks(self, 
                     on_text_chunk: Optional[Callable] = None,
                     on_sentence: Optional[Callable] = None,
                     on_tool_result: Optional[Callable] = None,
                     voice_integration=None,
                     tool_calls_queue=None,
                     tool_call_detected_signal=None):
        """设置回调函数"""
        self.callback_manager.register_callback("on_text_chunk", on_text_chunk)
        self.callback_manager.register_callback("on_sentence", on_sentence)
        self.callback_manager.register_callback("on_tool_result", on_tool_result)
        
        # 设置其他组件
        self.voice_integration = voice_integration
        self.tool_calls_queue = tool_calls_queue
        self.tool_call_detected_signal = tool_call_detected_signal
        
        logger.debug("回调函数设置完成")
    
    async def process_text_chunk(self, text_chunk: str):
        """处理文本块"""
        if not text_chunk:
            return
            
        for char in text_chunk:
            if char == '{':
                if not self.in_tool_call:
                    # 开始工具调用
                    self.in_tool_call = True
                    self.tool_call_buffer = char
                    self.brace_count = 1
                    
                    # 发送缓冲区中的纯文本
                    if self.text_buffer.strip():
                        await self._flush_text_buffer()
                else:
                    # 嵌套大括号
                    self.tool_call_buffer += char
                    self.brace_count += 1
                    
            elif char == '}':
                if self.in_tool_call:
                    self.tool_call_buffer += char
                    self.brace_count -= 1
                    
                    if self.brace_count == 0:
                        # 工具调用结束
                        await self._extract_tool_call(self.tool_call_buffer)
                        self.in_tool_call = False
                        self.tool_call_buffer = ""
                        
            else:
                if self.in_tool_call:
                    self.tool_call_buffer += char
                else:
                    self.text_buffer += char
    
    async def _flush_text_buffer(self):
        """刷新文本缓冲区"""
        if not self.text_buffer:
            return
            
        # 发送文本块
        await self.callback_manager.call_callback("on_text_chunk", self.text_buffer, "chunk")
        
        # 发送到语音集成
        await self._send_to_voice_integration(self.text_buffer)
        
        # 清空缓冲区
        self.text_buffer = ""
    
    async def _send_to_voice_integration(self, text: str):
        """发送文本到语音集成"""
        if self.voice_integration and text.strip():
            try:
                if hasattr(self.voice_integration, 'speak_text'):
                    await self.voice_integration.speak_text(text)
            except Exception as e:
                logger.error(f"语音集成错误: {e}")
    
    async def _extract_tool_call(self, tool_call_text: str):
        """提取工具调用"""
        try:
            # 解析JSON
            tool_call_data = json.loads(tool_call_text)
            
            if not isinstance(tool_call_data, dict):
                return
                
            # 检查是否包含工具调用信息
            if 'tool_name' in tool_call_data or 'function' in tool_call_data:
                logger.info(f"检测到工具调用: {tool_call_data}")
                
                # 发送工具调用回调
                await self.callback_manager.call_callback("on_tool_call", tool_call_text, "tool_call")
                
                # 发送信号
                if self.tool_call_detected_signal:
                    self.tool_call_detected_signal.emit()
                
                # 添加到队列
                if self.tool_calls_queue:
                    self.tool_calls_queue.put(tool_call_data)
                
                # 执行工具调用
                if self.mcp_manager:
                    try:
                        result = await self.mcp_manager.unified_call(
                            tool_call_data.get('service_name', ''),
                            tool_call_data.get('tool_name', ''),
                            tool_call_data
                        )
                        
                        # 发送工具结果回调
                        await self.callback_manager.call_callback("on_tool_result", str(result), "tool_result")
                        
                    except Exception as e:
                        error_msg = f"工具调用执行失败: {str(e)}"
                        logger.error(error_msg)
                        await self.callback_manager.call_callback("on_tool_result", error_msg, "tool_error")
                        
        except json.JSONDecodeError:
            # 不是有效的JSON，可能是普通文本
            logger.debug(f"非JSON内容，作为普通文本处理: {tool_call_text}")
            self.text_buffer += tool_call_text
        except Exception as e:
            logger.error(f"工具调用提取失败: {e}")
            # 出错时作为普通文本处理
            self.text_buffer += tool_call_text
    
    async def finish_processing(self):
        """完成处理"""
        # 刷新剩余的文本缓冲区
        if self.text_buffer.strip():
            await self._flush_text_buffer()
        
        # 如果还在工具调用中，强制结束
        if self.in_tool_call and self.tool_call_buffer:
            logger.warning("强制结束未完成的工具调用")
            self.text_buffer += self.tool_call_buffer
            await self._flush_text_buffer()
            self.in_tool_call = False
            self.tool_call_buffer = ""
        
        logger.debug("流式处理完成")
    
    def reset(self):
        """重置状态"""
        self.in_tool_call = False
        self.brace_count = 0
        self.text_buffer = ""
        self.tool_call_buffer = ""

class StreamingResponseProcessor:
    """流式响应处理器 - 集成工具调用提取和文本处理"""
    
    def __init__(self, mcp_manager=None):
        self.tool_extractor = StreamingToolCallExtractor(mcp_manager)
        self.response_buffer = ""
        self.is_processing = False
        
    async def process_ai_response(self, response_stream, callbacks: Dict[str, Callable]):
        """处理AI流式响应"""
        self.is_processing = True
        self.response_buffer = ""
        
        # 设置回调函数
        self.tool_extractor.set_callbacks(**callbacks)
        
        try:
            async for chunk in response_stream:
                if not self.is_processing:
                    break
                    
                chunk_text = str(chunk)
                self.response_buffer += chunk_text
                
                # 使用工具调用提取器处理
                await self.tool_extractor.process_text_chunk(chunk_text)
                
        except Exception as e:
            logger.error(f"AI流式响应处理错误: {e}")
        finally:
            self.is_processing = False
            # 完成处理
            await self.tool_extractor.finish_processing()
    
    def stop_processing(self):
        """停止处理"""
        self.is_processing = False
    
    def get_response_buffer(self) -> str:
        """获取响应缓冲区内容"""
        return self.response_buffer