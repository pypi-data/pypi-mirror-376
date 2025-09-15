"""
消息管理器

统一管理对话历史和会话
"""

import uuid
import json
import time
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path

logger = logging.getLogger(__name__)

class MessageManager:
    """统一的消息管理器"""
    
    def __init__(self):
        self.sessions = {}  # 会话存储
        self.persistent_storage = True  # 是否启用持久化存储
        self.storage_dir = Path("logs/sessions")  # 存储目录
        self.max_history_rounds = 10  # 最大历史轮数
        
        # 确保存储目录存在
        if self.persistent_storage:
            self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info("MessageManager初始化完成")
    
    def generate_session_id(self) -> str:
        """生成唯一的会话ID"""
        return str(uuid.uuid4())
    
    def create_session(self, session_id: Optional[str] = None) -> str:
        """创建新会话"""
        if session_id is None:
            session_id = self.generate_session_id()
        
        # 检查会话是否已存在
        if session_id in self.sessions:
            logger.warning(f"会话 {session_id} 已存在")
            return session_id
        
        # 创建新会话
        self.sessions[session_id] = {
            "id": session_id,
            "created_at": time.time(),
            "last_updated": time.time(),
            "messages": [],
            "agent_type": None,
            "metadata": {}
        }
        
        # 尝试加载持久化数据
        self._load_persistent_context_for_session(session_id)
        
        logger.info(f"创建新会话: {session_id}")
        return session_id
    
    def _load_persistent_context_for_session(self, session_id: str):
        """为会话加载持久化上下文"""
        if not self.persistent_storage:
            return
        
        try:
            session_file = self.storage_dir / f"{session_id}.json"
            if session_file.exists():
                with open(session_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if session_id in self.sessions:
                        self.sessions[session_id].update(data)
                        logger.debug(f"加载会话持久化数据: {session_id}")
        except Exception as e:
            logger.error(f"加载会话持久化数据失败 {session_id}: {e}")
    
    def get_session(self, session_id: str) -> Optional[Dict]:
        """获取会话信息"""
        return self.sessions.get(session_id)
    
    def add_message(self, session_id: str, role: str, content: str) -> bool:
        """添加消息到会话"""
        if session_id not in self.sessions:
            logger.error(f"会话 {session_id} 不存在")
            return False
        
        message = {
            "role": role,
            "content": content,
            "timestamp": time.time()
        }
        
        self.sessions[session_id]["messages"].append(message)
        self.sessions[session_id]["last_updated"] = time.time()
        
        # 保存到持久化存储
        self._save_session_to_storage(session_id)
        
        logger.debug(f"添加消息到会话 {session_id}: {role}")
        return True
    
    def get_messages(self, session_id: str) -> List[Dict]:
        """获取会话的所有消息"""
        if session_id not in self.sessions:
            return []
        return self.sessions[session_id]["messages"]
    
    def get_recent_messages(self, session_id: str, count: Optional[int] = None) -> List[Dict]:
        """获取最近的几条消息"""
        messages = self.get_messages(session_id)
        if count is None:
            count = self.max_history_rounds * 2  # 假设每轮对话包含用户和助手消息
        return messages[-count:] if messages else []
    
    def build_conversation_messages(self, session_id: str, system_prompt: str, 
                                  current_message: str, include_history: bool = True) -> List[Dict]:
        """构建完整的对话消息列表"""
        messages = []
        
        # 添加系统提示词
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        # 添加历史消息
        if include_history:
            recent_messages = self.get_recent_messages(session_id)
            messages.extend(recent_messages)
        
        # 添加当前消息
        if current_message:
            messages.append({"role": "user", "content": current_message})
        
        return messages
    
    def build_conversation_messages_from_memory(self, memory_messages: List[Dict], system_prompt: str, 
                                              current_message: str, max_history_rounds: int = None) -> List[Dict]:
        """从内存消息构建对话消息列表"""
        messages = []
        
        # 添加系统提示词
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        # 添加历史消息（限制轮数）
        if max_history_rounds is None:
            max_history_rounds = self.max_history_rounds
        
        # 计算要保留的消息数量（每轮对话包含用户和助手消息）
        max_messages = max_history_rounds * 2
        if memory_messages:
            recent_messages = memory_messages[-max_messages:]
            messages.extend(recent_messages)
        
        # 添加当前消息
        if current_message:
            messages.append({"role": "user", "content": current_message})
        
        return messages
    
    def get_session_info(self, session_id: str) -> Optional[Dict]:
        """获取会话信息"""
        if session_id not in self.sessions:
            return None
        
        session = self.sessions[session_id]
        return {
            "id": session["id"],
            "created_at": session["created_at"],
            "last_updated": session["last_updated"],
            "message_count": len(session["messages"]),
            "agent_type": session.get("agent_type"),
            "metadata": session.get("metadata", {})
        }
    
    def get_all_sessions_info(self) -> Dict[str, Dict]:
        """获取所有会话信息"""
        sessions_info = {}
        for session_id in self.sessions:
            sessions_info[session_id] = self.get_session_info(session_id)
        return sessions_info
    
    def delete_session(self, session_id: str) -> bool:
        """删除会话"""
        if session_id not in self.sessions:
            return False
        
        # 删除内存中的会话
        del self.sessions[session_id]
        
        # 删除持久化文件
        if self.persistent_storage:
            session_file = self.storage_dir / f"{session_id}.json"
            if session_file.exists():
                session_file.unlink()
        
        logger.info(f"删除会话: {session_id}")
        return True
    
    def clear_all_sessions(self) -> int:
        """清空所有会话"""
        count = len(self.sessions)
        self.sessions.clear()
        
        # 清空持久化文件
        if self.persistent_storage and self.storage_dir.exists():
            for file in self.storage_dir.glob("*.json"):
                file.unlink()
        
        logger.info(f"清空所有会话，共 {count} 个")
        return count
    
    def cleanup_old_sessions(self, max_age_hours: int = 24) -> int:
        """清理过期会话"""
        current_time = time.time()
        max_age_seconds = max_age_hours * 3600
        cleaned_count = 0
        
        sessions_to_remove = []
        for session_id, session in self.sessions.items():
            if current_time - session["last_updated"] > max_age_seconds:
                sessions_to_remove.append(session_id)
        
        for session_id in sessions_to_remove:
            self.delete_session(session_id)
            cleaned_count += 1
        
        logger.info(f"清理过期会话，共 {cleaned_count} 个")
        return cleaned_count
    
    def set_agent_type(self, session_id: str, agent_type: str) -> bool:
        """设置会话的代理类型"""
        if session_id not in self.sessions:
            return False
        
        self.sessions[session_id]["agent_type"] = agent_type
        self.sessions[session_id]["last_updated"] = time.time()
        self._save_session_to_storage(session_id)
        return True
    
    def get_agent_type(self, session_id: str) -> Optional[str]:
        """获取会话的代理类型"""
        if session_id not in self.sessions:
            return None
        return self.sessions[session_id].get("agent_type")
    
    def _save_session_to_storage(self, session_id: str):
        """保存会话到持久化存储"""
        if not self.persistent_storage or session_id not in self.sessions:
            return
        
        try:
            session_file = self.storage_dir / f"{session_id}.json"
            with open(session_file, 'w', encoding='utf-8') as f:
                json.dump(self.sessions[session_id], f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存会话到存储失败 {session_id}: {e}")