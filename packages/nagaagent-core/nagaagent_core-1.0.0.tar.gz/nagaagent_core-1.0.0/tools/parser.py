"""
工具调用解析器

解析和执行工具调用
"""

import json
import re
import asyncio
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

def parse_tool_calls(content: str) -> list:
    """解析工具调用"""
    tool_calls = []
    
    # 匹配JSON格式的工具调用
    json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
    matches = re.findall(json_pattern, content)
    
    for match in matches:
        try:
            # 尝试解析JSON
            tool_call = json.loads(match)
            if isinstance(tool_call, dict) and ('tool_name' in tool_call or 'function' in tool_call):
                tool_calls.append(tool_call)
        except json.JSONDecodeError:
            continue
    
    # 如果没有找到JSON格式，尝试其他格式
    if not tool_calls:
        # 匹配简单的工具调用格式
        simple_pattern = r'(\w+)\s*\(([^)]*)\)'
        simple_matches = re.findall(simple_pattern, content)
        
        for func_name, args_str in simple_matches:
            tool_call = {
                "tool_name": func_name,
                "args": args_str.strip()
            }
            tool_calls.append(tool_call)
    
    return tool_calls

async def execute_tool_calls(tool_calls: list, mcp_manager) -> str:
    """执行工具调用"""
    if not tool_calls:
        return ""
    
    results = []
    
    for tool_call in tool_calls:
        try:
            # 提取工具信息
            tool_name = tool_call.get('tool_name') or tool_call.get('function', '')
            service_name = tool_call.get('service_name', '')
            args = tool_call.get('args', {})
            
            if isinstance(args, str):
                try:
                    args = json.loads(args)
                except json.JSONDecodeError:
                    args = {"input": args}
            
            # 执行工具调用
            if mcp_manager:
                result = await mcp_manager.unified_call(service_name, tool_name, args)
                results.append(f"工具 {tool_name} 执行结果: {result}")
            else:
                results.append(f"工具 {tool_name} 调用失败: MCP管理器未初始化")
                
        except Exception as e:
            error_msg = f"工具调用执行失败: {str(e)}"
            logger.error(error_msg)
            results.append(error_msg)
    
    return "\n".join(results)

async def tool_call_loop(messages: List[Dict], mcp_manager, llm_caller, is_streaming: bool = False, max_recursion: int = None, tool_calls_queue=None) -> Dict:
    """工具调用循环"""
    if max_recursion is None:
        max_recursion = 5
    
    current_messages = messages.copy()
    recursion_count = 0
    
    while recursion_count < max_recursion:
        try:
            # 调用LLM
            if is_streaming:
                # 流式调用
                response = ""
                async for chunk in llm_caller(current_messages):
                    response += chunk
            else:
                # 非流式调用
                response = await llm_caller(current_messages)
            
            # 解析工具调用
            tool_calls = parse_tool_calls(response)
            
            if not tool_calls:
                # 没有工具调用，返回最终响应
                return {
                    "response": response,
                    "tool_calls": [],
                    "recursion_count": recursion_count
                }
            
            # 执行工具调用
            tool_results = await execute_tool_calls(tool_calls, mcp_manager)
            
            # 添加到消息历史
            current_messages.append({
                "role": "assistant",
                "content": response
            })
            
            current_messages.append({
                "role": "tool",
                "content": tool_results
            })
            
            # 如果设置了工具调用队列，添加到队列
            if tool_calls_queue:
                for tool_call in tool_calls:
                    tool_calls_queue.put(tool_call)
            
            recursion_count += 1
            
        except Exception as e:
            logger.error(f"工具调用循环错误: {e}")
            return {
                "response": f"工具调用循环错误: {str(e)}",
                "tool_calls": [],
                "recursion_count": recursion_count,
                "error": str(e)
            }
    
    # 达到最大递归次数
    return {
        "response": "达到最大工具调用递归次数",
        "tool_calls": [],
        "recursion_count": recursion_count,
        "error": "max_recursion_reached"
    }