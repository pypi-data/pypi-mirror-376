"""
上下文管理器
"""

import json
import logging
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any

from .parser import LogParser
from .manager import LogManager

logger = logging.getLogger(__name__)

class ContextManager:
    """上下文管理器"""
    
    def __init__(self, 
                 log_dir: str = "logs",
                 ai_name: str = "娜杰日达",
                 max_context_days: int = 3,
                 max_messages: int = 20):
        """
        初始化上下文管理器
        
        Args:
            log_dir: 日志目录
            ai_name: AI名称
            max_context_days: 最大上下文天数
            max_messages: 最大消息数量
        """
        self.log_parser = LogParser(log_dir, ai_name)
        self.log_manager = LogManager(log_dir)
        self.max_context_days = max_context_days
        self.max_messages = max_messages
        
        # 内存缓存
        self._context_cache = {}
        self._cache_timestamp = 0
        self._cache_ttl = 300  # 5分钟缓存
        
        logger.info("上下文管理器初始化完成")
    
    def load_persistent_context(self, 
                               session_id: str = None,
                               days: int = None,
                               max_messages: int = None) -> List[Dict]:
        """
        加载持久化上下文
        
        Args:
            session_id: 会话ID，如果提供则只加载该会话的上下文
            days: 加载天数
            max_messages: 最大消息数量
            
        Returns:
            List[Dict]: 上下文消息列表
        """
        days = days or self.max_context_days
        max_messages = max_messages or self.max_messages
        
        # 检查缓存
        cache_key = f"{session_id}_{days}_{max_messages}"
        current_time = time.time()
        
        if (cache_key in self._context_cache and 
            current_time - self._cache_timestamp < self._cache_ttl):
            logger.debug("使用缓存的上下文")
            return self._context_cache[cache_key]
        
        try:
            if session_id:
                # 加载特定会话的上下文
                messages = self._load_session_context(session_id, days, max_messages)
            else:
                # 加载全局上下文
                messages = self.log_parser.load_recent_context(days, max_messages)
            
            # 更新缓存
            self._context_cache[cache_key] = messages
            self._cache_timestamp = current_time
            
            logger.info(f"加载了 {len(messages)} 条上下文消息")
            return messages
            
        except Exception as e:
            logger.error(f"加载持久化上下文失败: {e}")
            return []
    
    def _load_session_context(self, 
                             session_id: str, 
                             days: int, 
                             max_messages: int) -> List[Dict]:
        """加载特定会话的上下文"""
        try:
            # 从日志管理器获取会话日志
            session_logs = self.log_manager.get_logs_by_session(session_id)
            
            # 转换为消息格式
            messages = []
            for log_entry in session_logs:
                if "messages" in log_entry:
                    messages.extend(log_entry["messages"])
            
            # 限制消息数量
            if len(messages) > max_messages:
                messages = messages[-max_messages:]
            
            return messages
            
        except Exception as e:
            logger.error(f"加载会话上下文失败 {session_id}: {e}")
            return []
    
    def save_context(self, 
                    session_id: str,
                    messages: List[Dict],
                    metadata: Optional[Dict[str, Any]] = None):
        """
        保存上下文
        
        Args:
            session_id: 会话ID
            messages: 消息列表
            metadata: 元数据
        """
        try:
            # 保存到日志管理器
            if len(messages) >= 2:
                # 假设最后两条消息是用户和助手的对话
                user_message = messages[-2].get("content", "") if messages[-2].get("role") == "user" else ""
                assistant_message = messages[-1].get("content", "") if messages[-1].get("role") == "assistant" else ""
                
                if user_message and assistant_message:
                    self.log_manager.log_conversation(
                        session_id=session_id,
                        user_message=user_message,
                        assistant_message=assistant_message,
                        metadata=metadata
                    )
            
            # 记录Prompt日志
            self.log_manager.log_prompt(
                session_id=session_id,
                messages=messages,
                metadata=metadata
            )
            
            # 清除相关缓存
            self._clear_context_cache(session_id)
            
            logger.debug(f"上下文已保存: {session_id}")
            
        except Exception as e:
            logger.error(f"保存上下文失败: {e}")
    
    def _clear_context_cache(self, session_id: str = None):
        """清除上下文缓存"""
        if session_id:
            # 清除特定会话的缓存
            keys_to_remove = [key for key in self._context_cache.keys() if session_id in key]
            for key in keys_to_remove:
                del self._context_cache[key]
        else:
            # 清除所有缓存
            self._context_cache.clear()
        
        self._cache_timestamp = 0
    
    def build_conversation_context(self, 
                                  session_id: str,
                                  system_prompt: str,
                                  current_message: str,
                                  include_history: bool = True) -> List[Dict]:
        """
        构建对话上下文
        
        Args:
            session_id: 会话ID
            system_prompt: 系统提示词
            current_message: 当前消息
            include_history: 是否包含历史记录
            
        Returns:
            List[Dict]: 完整的对话消息列表
        """
        messages = []
        
        # 添加系统提示词
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        # 添加历史消息
        if include_history:
            history_messages = self.load_persistent_context(session_id)
            messages.extend(history_messages)
        
        # 添加当前消息
        if current_message:
            messages.append({"role": "user", "content": current_message})
        
        return messages
    
    def get_context_statistics(self, days: int = 7) -> Dict[str, Any]:
        """获取上下文统计信息"""
        try:
            # 获取日志统计
            log_stats = self.log_parser.get_context_statistics(days)
            manager_stats = self.log_manager.get_log_statistics()
            
            # 合并统计信息
            stats = {
                **log_stats,
                **manager_stats,
                "cache_size": len(self._context_cache),
                "cache_timestamp": self._cache_timestamp,
                "max_context_days": self.max_context_days,
                "max_messages": self.max_messages
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"获取上下文统计失败: {e}")
            return {}
    
    def cleanup_old_context(self, days: int = 30):
        """清理旧上下文"""
        try:
            # 清理日志文件
            self.log_manager.cleanup_old_logs(days)
            
            # 清除缓存
            self._clear_context_cache()
            
            logger.info(f"清理了 {days} 天前的旧上下文")
            
        except Exception as e:
            logger.error(f"清理旧上下文失败: {e}")
    
    def export_context(self, 
                      session_id: str = None,
                      output_file: str = None) -> str:
        """
        导出上下文
        
        Args:
            session_id: 会话ID，如果为None则导出所有上下文
            output_file: 输出文件路径
            
        Returns:
            str: 导出文件路径
        """
        try:
            if not output_file:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                output_file = f"context_export_{timestamp}.json"
            
            # 获取上下文数据
            if session_id:
                context_data = {
                    "session_id": session_id,
                    "messages": self.load_persistent_context(session_id),
                    "metadata": self.log_manager.get_session_metadata(session_id)
                }
            else:
                context_data = {
                    "all_sessions": self.log_manager.get_log_statistics(),
                    "recent_context": self.load_persistent_context()
                }
            
            # 保存到文件
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(context_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"上下文已导出到: {output_file}")
            return output_file
            
        except Exception as e:
            logger.error(f"导出上下文失败: {e}")
            return ""
