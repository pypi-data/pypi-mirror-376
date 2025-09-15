#!/usr/bin/env python3
"""
日志上下文解析器
用于从现有的日志文件中解析对话内容并重建上下文
"""

import os
import re
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from pathlib import Path

logger = logging.getLogger(__name__)


class LogContextParser:
    """日志上下文解析器"""
    
    def __init__(self, 
                 log_dir: Optional[str] = None,
                 ai_name: str = "娜杰日达",
                 context_load_days: int = 3,
                 config_path: Optional[str] = None):
        """
        初始化日志解析器
        
        Args:
            log_dir: 日志目录路径
            ai_name: AI名称，用于解析日志
            context_load_days: 默认加载天数
            config_path: 配置文件路径，用于读取配置
        """
        self.ai_name = ai_name
        self.context_load_days = context_load_days
        
        # 设置日志目录
        if log_dir is None:
            self.log_dir = Path("logs")
        else:
            self.log_dir = Path(log_dir)
        
        # 确保日志目录存在
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # 尝试从配置文件读取配置
        if config_path:
            self._load_config_from_file(config_path)
        else:
            self._load_config_from_default_locations()
    
    def _load_config_from_file(self, config_path: str):
        """从指定配置文件加载配置"""
        try:
            config_file = Path(config_path)
            if config_file.exists():
                with open(config_file, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                self.ai_name = config_data.get("system", {}).get("ai_name", self.ai_name)
                self.context_load_days = config_data.get("api", {}).get("context_load_days", self.context_load_days)
                logger.debug(f"从配置文件加载: ai_name={self.ai_name}, context_load_days={self.context_load_days}")
        except Exception as e:
            logger.warning(f"从配置文件加载配置失败: {e}")
    
    def _load_config_from_default_locations(self):
        """从默认位置加载配置"""
        # 尝试从当前目录的config.json加载
        config_paths = [
            Path("config.json"),
            Path(__file__).parent.parent.parent / "config.json",  # 项目根目录
            Path.cwd() / "config.json"
        ]
        
        for config_path in config_paths:
            if config_path.exists():
                self._load_config_from_file(str(config_path))
                break
        else:
            # 如果找不到配置文件，尝试从system.config导入（向后兼容）
            try:
                from system.config import config
                self.ai_name = getattr(config.system, 'ai_name', self.ai_name)
                self.context_load_days = getattr(config.api, 'context_load_days', self.context_load_days)
                logger.debug(f"从system.config加载: ai_name={self.ai_name}, context_load_days={self.context_load_days}")
            except ImportError:
                logger.debug(f"使用默认配置: ai_name={self.ai_name}, context_load_days={self.context_load_days}")
    
    def _parse_log_line(self, line: str) -> Optional[tuple]:
        """
        解析单行日志内容
        
        Args:
            line: 日志行内容
            
        Returns:
            tuple: (role, content) 或 None
        """
        line = line.strip()
        if not line:
            return None
        
        # 匹配格式：[时间] 用户: 内容 或 [时间] AI名称: 内容
        pattern = r'^\[(\d{2}:\d{2}:\d{2})\] (用户|' + re.escape(self.ai_name) + r'): (.+)$'
        match = re.match(pattern, line)
        
        if match:
            time_str, speaker, content = match.groups()
            if speaker == "用户":
                role = "user"
            else:
                role = "assistant"
            return (role, content.strip())
        
        return None
    
    def _is_message_start_line(self, line: str) -> bool:
        """
        判断是否为消息开始行
        
        Args:
            line: 日志行内容
            
        Returns:
            bool: 是否为消息开始行
        """
        line = line.strip()
        if not line:
            return False
        
        # 匹配格式：[时间] 用户: 或 [时间] AI名称:
        pattern = r'^\[(\d{2}:\d{2}:\d{2})\] (用户|' + re.escape(self.ai_name) + r'):'
        return bool(re.match(pattern, line))
    
    def parse_log_file(self, log_file_path: str) -> List[Dict]:
        """
        解析单个日志文件，提取对话内容
        按照日志记录代码的格式：每轮对话包含用户消息和AI回复，用50个-分隔
        
        Args:
            log_file_path: 日志文件路径
            
        Returns:
            List[Dict]: 对话消息列表，格式为[{"role": "user/assistant", "content": "内容"}]
        """
        messages = []
        
        try:
            with open(log_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 以50个-分割对话轮次（按照日志记录代码的格式）
            conversation_blocks = content.split('-' * 50)
            
            for block in conversation_blocks:
                block = block.strip()
                if not block:
                    continue
                
                # 解析每个对话块中的消息
                block_messages = self._parse_conversation_block(block)
                messages.extend(block_messages)
                        
        except FileNotFoundError:
            logger.debug(f"日志文件不存在: {log_file_path}")
        except Exception as e:
            logger.error(f"解析日志文件失败 {log_file_path}: {e}")
        
        return messages
    
    def _parse_conversation_block(self, block: str) -> List[Dict]:
        """
        解析单个对话块，提取其中的所有消息
        每块包含用户消息和AI回复，支持多行内容
        
        Args:
            block: 对话块内容
            
        Returns:
            List[Dict]: 消息列表
        """
        messages = []
        lines = block.split('\n')
        current_message = None
        current_content_lines = []
        
        for line in lines:
            line = line.rstrip('\n\r')  # 移除行尾换行符，但保留内容中的换行
            
            # 检查是否为消息开始行
            if self._is_message_start_line(line):
                # 保存前一个消息
                if current_message is not None and current_content_lines:
                    content = '\n'.join(current_content_lines)
                    messages.append({
                        "role": current_message["role"], 
                        "content": content
                    })
                
                # 开始新消息
                result = self._parse_log_line(line)
                if result:
                    role, content = result
                    current_message = {"role": role}
                    current_content_lines = [content] if content else []
                else:
                    current_message = None
                    current_content_lines = []
            
            # 如果当前有活跃消息，且不是消息开始行，则作为内容行处理
            elif current_message is not None:
                # 跳过分隔线和空行
                if line.strip() and not line.strip().startswith('---') and not line.strip().startswith('--'):
                    current_content_lines.append(line)
        
        # 保存最后一个消息
        if current_message is not None and current_content_lines:
            content = '\n'.join(current_content_lines)
            messages.append({
                "role": current_message["role"], 
                "content": content
            })
        
        return messages
    
    def get_log_files_by_date(self, days: int = 3) -> List[str]:
        """
        获取最近几天的日志文件路径
        
        Args:
            days: 要获取的天数
            
        Returns:
            List[str]: 日志文件路径列表，按日期倒序排列
        """
        log_files = []
        today = datetime.now()
        
        for i in range(days):
            date = today - timedelta(days=i)
            date_str = date.strftime('%Y-%m-%d')
            log_file = self.log_dir / f"{date_str}.log"
            
            if log_file.exists():
                log_files.append(str(log_file))
        
        # 按日期倒序排列（最新的在前）
        log_files.reverse()
        return log_files
    
    def load_recent_context(self, days: int = 3, max_messages: int = None) -> List[Dict]:
        """
        加载最近几天的对话上下文
        
        Args:
            days: 要加载的天数
            max_messages: 最大消息数量限制
            
        Returns:
            List[Dict]: 对话消息列表
        """
        all_messages = []
        log_files = self.get_log_files_by_date(days)
        
        logger.info(f"开始加载最近 {days} 天的日志文件: {log_files}")
        
        for log_file in log_files:
            messages = self.parse_log_file(log_file)
            all_messages.extend(messages)
            logger.debug(f"从 {log_file} 加载了 {len(messages)} 条消息")
        
        # 限制消息数量
        if max_messages and len(all_messages) > max_messages:
            all_messages = all_messages[-max_messages:]
            logger.info(f"限制消息数量为 {max_messages} 条")
        
        logger.info(f"总共加载了 {len(all_messages)} 条历史对话")
        return all_messages
    
    def get_context_statistics(self, days: int = 7) -> Dict:
        """
        获取上下文统计信息
        
        Args:
            days: 统计天数
            
        Returns:
            Dict: 统计信息
        """
        log_files = self.get_log_files_by_date(days)
        total_messages = 0
        user_messages = 0
        assistant_messages = 0
        
        for log_file in log_files:
            messages = self.parse_log_file(log_file)
            total_messages += len(messages)
            
            for msg in messages:
                if msg["role"] == "user":
                    user_messages += 1
                else:
                    assistant_messages += 1
        
        return {
            "total_files": len(log_files),
            "total_messages": total_messages,
            "user_messages": user_messages,
            "assistant_messages": assistant_messages,
            "days_covered": days
        }
    
    def load_persistent_context_to_ui(self, 
                                    parent_widget: Any = None, 
                                    max_messages: int = None,
                                    message_renderer_class: Any = None) -> List[tuple]:
        """
        将持久化上下文加载到前端UI
        
        Args:
            parent_widget: 父级容器widget
            max_messages: 最大消息数量限制
            message_renderer_class: 消息渲染器类，用于创建UI组件
            
        Returns:
            List[tuple]: 返回(消息ID, 消息信息, 对话框组件)的元组列表
        """
        try:
            # 计算最大消息数量
            if max_messages is None:
                max_messages = 20  # 默认值
            
            # 加载历史对话
            recent_messages = self.load_recent_context(
                days=self.context_load_days,
                max_messages=max_messages
            )
            
            if not recent_messages:
                logger.info("📝 未找到历史对话记录，跳过前端UI加载")
                return []
            
            # 如果没有提供消息渲染器类，尝试导入
            if message_renderer_class is None:
                try:
                    from ui.message_renderer import MessageRenderer
                    message_renderer_class = MessageRenderer
                except ImportError:
                    logger.warning("⚠️ 消息渲染器模块未找到，无法创建UI组件")
                    return []
            
            # 批量创建历史消息对话框
            if hasattr(message_renderer_class, 'batch_create_history_messages'):
                history_dialogs = message_renderer_class.batch_create_history_messages(
                    recent_messages, parent_widget
                )
            else:
                logger.warning("⚠️ 消息渲染器不支持批量创建历史消息")
                return []
            
            # 构建返回结果
            ui_messages = []
            for i, (msg, dialog) in enumerate(zip(recent_messages, history_dialogs)):
                message_id = f"history_{i}"
                message_info = {
                    'name': msg.get('role', 'user'),
                    'content': msg.get('content', ''),
                    'full_content': msg.get('content', ''),
                    'dialog_widget': dialog
                }
                ui_messages.append((message_id, message_info, dialog))
            
            logger.info(f"✅ 前端UI已加载 {len(ui_messages)} 条历史对话")
            return ui_messages
            
        except Exception as e:
            logger.error(f"❌ 前端加载持久化上下文失败: {e}")
            return []
    
    def set_ai_name(self, ai_name: str):
        """设置AI名称"""
        self.ai_name = ai_name
    
    def set_context_load_days(self, days: int):
        """设置默认加载天数"""
        self.context_load_days = days
    
    def set_log_dir(self, log_dir: str):
        """设置日志目录"""
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)


# 全局实例
_log_parser = None

def get_log_parser(log_dir: Optional[str] = None, 
                   ai_name: str = "娜杰日达",
                   context_load_days: int = 3) -> LogContextParser:
    """获取全局日志解析器实例"""
    global _log_parser
    if _log_parser is None:
        _log_parser = LogContextParser(
            log_dir=log_dir,
            ai_name=ai_name,
            context_load_days=context_load_days
        )
    return _log_parser
