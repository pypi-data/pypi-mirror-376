"""
日志管理器
"""

import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

class LogManager:
    """日志管理器"""
    
    def __init__(self, log_dir: str = "logs"):
        """
        初始化日志管理器
        
        Args:
            log_dir: 日志目录
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # 创建子目录
        self.sessions_dir = self.log_dir / "sessions"
        self.prompts_dir = self.log_dir / "prompts"
        self.audio_temp_dir = self.log_dir / "audio_temp"
        
        for subdir in [self.sessions_dir, self.prompts_dir, self.audio_temp_dir]:
            subdir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"日志管理器初始化完成，日志目录: {self.log_dir}")
    
    def log_conversation(self, 
                        session_id: str,
                        user_message: str,
                        assistant_message: str,
                        metadata: Optional[Dict[str, Any]] = None):
        """
        记录对话日志
        
        Args:
            session_id: 会话ID
            user_message: 用户消息
            assistant_message: 助手回复
            metadata: 元数据
        """
        try:
            # 获取当前日期
            today = datetime.now().strftime('%Y-%m-%d')
            log_file = self.log_dir / f"{today}.log"
            
            # 获取当前时间
            current_time = datetime.now().strftime('%H:%M:%S')
            
            # 构建日志内容
            log_content = f"""
[{current_time}] 用户: {user_message}

[{current_time}] 娜杰日达: {assistant_message}

{'-' * 50}
"""
            
            # 写入日志文件
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(log_content)
            
            # 记录会话元数据
            if metadata:
                self._save_session_metadata(session_id, metadata)
            
            logger.debug(f"对话日志已记录: {session_id}")
            
        except Exception as e:
            logger.error(f"记录对话日志失败: {e}")
    
    def _save_session_metadata(self, session_id: str, metadata: Dict[str, Any]):
        """保存会话元数据"""
        try:
            metadata_file = self.sessions_dir / f"{session_id}.json"
            
            # 加载现有元数据
            if metadata_file.exists():
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    existing_metadata = json.load(f)
            else:
                existing_metadata = {}
            
            # 更新元数据
            existing_metadata.update(metadata)
            existing_metadata["last_updated"] = time.time()
            
            # 保存元数据
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(existing_metadata, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            logger.error(f"保存会话元数据失败: {e}")
    
    def get_session_metadata(self, session_id: str) -> Optional[Dict[str, Any]]:
        """获取会话元数据"""
        try:
            metadata_file = self.sessions_dir / f"{session_id}.json"
            if metadata_file.exists():
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"获取会话元数据失败: {e}")
        return None
    
    def log_prompt(self, 
                   session_id: str,
                   messages: List[Dict],
                   api_response: Optional[Dict] = None,
                   api_status: str = "unknown"):
        """
        记录Prompt日志
        
        Args:
            session_id: 会话ID
            messages: 消息列表
            api_response: API响应
            api_status: API状态
        """
        try:
            # 获取当前日期
            today = datetime.now().strftime('%Y-%m-%d')
            log_file = self.prompts_dir / f"{today}.json"
            
            # 构建日志条目
            log_entry = {
                "timestamp": time.time(),
                "session_id": session_id,
                "messages": messages,
                "api_response": api_response,
                "api_status": api_status
            }
            
            # 加载现有日志
            existing_logs = []
            if log_file.exists():
                with open(log_file, 'r', encoding='utf-8') as f:
                    existing_logs = json.load(f)
            
            # 添加新日志条目
            existing_logs.append(log_entry)
            
            # 保存日志
            with open(log_file, 'w', encoding='utf-8') as f:
                json.dump(existing_logs, f, ensure_ascii=False, indent=2)
            
            logger.debug(f"Prompt日志已记录: {session_id}")
            
        except Exception as e:
            logger.error(f"记录Prompt日志失败: {e}")
    
    def get_today_logs(self) -> List[Dict]:
        """获取今天的日志"""
        try:
            today = datetime.now().strftime('%Y-%m-%d')
            log_file = self.prompts_dir / f"{today}.json"
            
            if log_file.exists():
                with open(log_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"获取今日日志失败: {e}")
        return []
    
    def get_logs_by_date(self, date_str: str) -> List[Dict]:
        """根据日期获取日志"""
        try:
            log_file = self.prompts_dir / f"{date_str}.json"
            if log_file.exists():
                with open(log_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"获取日期日志失败 {date_str}: {e}")
        return []
    
    def get_logs_by_session(self, session_id: str) -> List[Dict]:
        """根据会话ID获取日志"""
        try:
            logs = []
            # 遍历所有日志文件
            for log_file in self.prompts_dir.glob("*.json"):
                with open(log_file, 'r', encoding='utf-8') as f:
                    daily_logs = json.load(f)
                    # 筛选指定会话的日志
                    session_logs = [log for log in daily_logs if log.get("session_id") == session_id]
                    logs.extend(session_logs)
            return logs
        except Exception as e:
            logger.error(f"获取会话日志失败 {session_id}: {e}")
        return []
    
    def cleanup_old_logs(self, days: int = 30):
        """清理旧日志文件"""
        try:
            cutoff_time = time.time() - (days * 24 * 3600)
            cleaned_count = 0
            
            # 清理会话元数据
            for metadata_file in self.sessions_dir.glob("*.json"):
                if metadata_file.stat().st_mtime < cutoff_time:
                    metadata_file.unlink()
                    cleaned_count += 1
            
            # 清理Prompt日志
            for log_file in self.prompts_dir.glob("*.json"):
                if log_file.stat().st_mtime < cutoff_time:
                    log_file.unlink()
                    cleaned_count += 1
            
            logger.info(f"清理了 {cleaned_count} 个旧日志文件")
            
        except Exception as e:
            logger.error(f"清理旧日志失败: {e}")
    
    def get_log_statistics(self) -> Dict[str, Any]:
        """获取日志统计信息"""
        try:
            stats = {
                "total_sessions": len(list(self.sessions_dir.glob("*.json"))),
                "total_prompt_logs": len(list(self.prompts_dir.glob("*.json"))),
                "log_directory": str(self.log_dir),
                "sessions_directory": str(self.sessions_dir),
                "prompts_directory": str(self.prompts_dir)
            }
            
            # 计算总日志条目数
            total_entries = 0
            for log_file in self.prompts_dir.glob("*.json"):
                with open(log_file, 'r', encoding='utf-8') as f:
                    daily_logs = json.load(f)
                    total_entries += len(daily_logs)
            
            stats["total_prompt_entries"] = total_entries
            return stats
            
        except Exception as e:
            logger.error(f"获取日志统计失败: {e}")
            return {}
