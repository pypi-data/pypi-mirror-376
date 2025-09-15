"""
消息管理模块测试
"""

import pytest
import time
import json
import tempfile
import shutil
from pathlib import Path
from NagaAgent_core.messages import MessageManager

class TestMessageManager:
    """测试消息管理器"""
    
    @pytest.fixture
    def temp_dir(self):
        """创建临时目录"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def manager(self, temp_dir):
        """创建消息管理器实例"""
        manager = MessageManager()
        manager.storage_dir = Path(temp_dir) / "sessions"
        manager.storage_dir.mkdir(parents=True, exist_ok=True)
        return manager
    
    def test_generate_session_id(self, manager):
        """测试生成会话ID"""
        session_id1 = manager.generate_session_id()
        session_id2 = manager.generate_session_id()
        
        assert isinstance(session_id1, str)
        assert isinstance(session_id2, str)
        assert session_id1 != session_id2
        assert len(session_id1) > 0
    
    def test_create_session_with_id(self, manager):
        """测试使用指定ID创建会话"""
        session_id = "test_session_123"
        created_id = manager.create_session(session_id)
        
        assert created_id == session_id
        assert session_id in manager.sessions
        
        session_info = manager.sessions[session_id]
        assert session_info["id"] == session_id
        assert session_info["messages"] == []
        assert session_info["agent_type"] is None
        assert "created_at" in session_info
        assert "last_updated" in session_info
    
    def test_create_session_auto_id(self, manager):
        """测试自动生成ID创建会话"""
        session_id = manager.create_session()
        
        assert isinstance(session_id, str)
        assert session_id in manager.sessions
        assert len(session_id) > 0
    
    def test_create_duplicate_session(self, manager):
        """测试创建重复会话"""
        session_id = "duplicate_test"
        
        # 第一次创建
        created_id1 = manager.create_session(session_id)
        assert created_id1 == session_id
        
        # 第二次创建（应该返回相同ID）
        created_id2 = manager.create_session(session_id)
        assert created_id2 == session_id
        
        # 会话应该只有一个
        assert len(manager.sessions) == 1
    
    def test_get_session(self, manager):
        """测试获取会话"""
        session_id = manager.create_session()
        
        # 获取存在的会话
        session = manager.get_session(session_id)
        assert session is not None
        assert session["id"] == session_id
        
        # 获取不存在的会话
        nonexistent = manager.get_session("nonexistent")
        assert nonexistent is None
    
    def test_add_message(self, manager):
        """测试添加消息"""
        session_id = manager.create_session()
        
        # 添加用户消息
        success = manager.add_message(session_id, "user", "你好")
        assert success
        assert len(manager.sessions[session_id]["messages"]) == 1
        
        # 添加助手消息
        success = manager.add_message(session_id, "assistant", "你好！有什么可以帮助你的吗？")
        assert success
        assert len(manager.sessions[session_id]["messages"]) == 2
        
        # 验证消息内容
        messages = manager.sessions[session_id]["messages"]
        assert messages[0]["role"] == "user"
        assert messages[0]["content"] == "你好"
        assert messages[1]["role"] == "assistant"
        assert messages[1]["content"] == "你好！有什么可以帮助你的吗？"
        assert "timestamp" in messages[0]
        assert "timestamp" in messages[1]
    
    def test_add_message_nonexistent_session(self, manager):
        """测试向不存在的会话添加消息"""
        success = manager.add_message("nonexistent", "user", "测试消息")
        assert not success
    
    def test_get_messages(self, manager):
        """测试获取消息"""
        session_id = manager.create_session()
        
        # 空会话
        messages = manager.get_messages(session_id)
        assert messages == []
        
        # 添加消息后
        manager.add_message(session_id, "user", "消息1")
        manager.add_message(session_id, "assistant", "消息2")
        
        messages = manager.get_messages(session_id)
        assert len(messages) == 2
        assert messages[0]["content"] == "消息1"
        assert messages[1]["content"] == "消息2"
    
    def test_get_recent_messages(self, manager):
        """测试获取最近消息"""
        session_id = manager.create_session()
        
        # 添加多条消息
        for i in range(10):
            manager.add_message(session_id, "user", f"用户消息 {i}")
            manager.add_message(session_id, "assistant", f"助手消息 {i}")
        
        # 获取最近消息（默认数量）
        recent = manager.get_recent_messages(session_id)
        assert len(recent) <= 20  # 最多20条（10轮对话）
        
        # 获取指定数量的最近消息
        recent_5 = manager.get_recent_messages(session_id, 5)
        assert len(recent_5) == 5
        assert recent_5[-1]["content"] == "助手消息 9"  # 最新的消息
    
    def test_build_conversation_messages(self, manager):
        """测试构建对话消息"""
        session_id = manager.create_session()
        
        # 添加历史消息
        manager.add_message(session_id, "user", "历史消息1")
        manager.add_message(session_id, "assistant", "历史回复1")
        manager.add_message(session_id, "user", "历史消息2")
        manager.add_message(session_id, "assistant", "历史回复2")
        
        # 构建对话消息
        conversation = manager.build_conversation_messages(
            session_id=session_id,
            system_prompt="你是一个AI助手",
            current_message="当前消息",
            include_history=True
        )
        
        assert len(conversation) == 6  # 系统提示 + 4条历史 + 1条当前
        assert conversation[0]["role"] == "system"
        assert conversation[0]["content"] == "你是一个AI助手"
        assert conversation[-1]["role"] == "user"
        assert conversation[-1]["content"] == "当前消息"
    
    def test_build_conversation_messages_no_history(self, manager):
        """测试构建对话消息（不包含历史）"""
        session_id = manager.create_session()
        
        # 添加历史消息
        manager.add_message(session_id, "user", "历史消息")
        manager.add_message(session_id, "assistant", "历史回复")
        
        # 构建对话消息（不包含历史）
        conversation = manager.build_conversation_messages(
            session_id=session_id,
            system_prompt="你是一个AI助手",
            current_message="当前消息",
            include_history=False
        )
        
        assert len(conversation) == 2  # 系统提示 + 当前消息
        assert conversation[0]["role"] == "system"
        assert conversation[1]["role"] == "user"
        assert conversation[1]["content"] == "当前消息"
    
    def test_build_conversation_messages_from_memory(self, manager):
        """测试从内存消息构建对话"""
        # 准备内存消息
        memory_messages = [
            {"role": "user", "content": "内存消息1"},
            {"role": "assistant", "content": "内存回复1"},
            {"role": "user", "content": "内存消息2"},
            {"role": "assistant", "content": "内存回复2"},
        ]
        
        # 构建对话消息
        conversation = manager.build_conversation_messages_from_memory(
            memory_messages=memory_messages,
            system_prompt="系统提示",
            current_message="当前消息",
            max_history_rounds=1  # 只保留1轮历史
        )
        
        assert len(conversation) == 4  # 系统提示 + 1轮历史(2条) + 当前消息
        assert conversation[0]["role"] == "system"
        assert conversation[-1]["content"] == "当前消息"
    
    def test_get_session_info(self, manager):
        """测试获取会话信息"""
        session_id = manager.create_session()
        
        # 添加消息
        manager.add_message(session_id, "user", "测试消息")
        manager.add_message(session_id, "assistant", "测试回复")
        
        # 设置代理类型
        manager.set_agent_type(session_id, "test_agent")
        
        # 获取会话信息
        info = manager.get_session_info(session_id)
        
        assert info["id"] == session_id
        assert info["message_count"] == 2
        assert info["agent_type"] == "test_agent"
        assert "created_at" in info
        assert "last_updated" in info
        assert "metadata" in info
    
    def test_get_all_sessions_info(self, manager):
        """测试获取所有会话信息"""
        # 创建多个会话
        session1 = manager.create_session()
        session2 = manager.create_session()
        
        # 添加消息
        manager.add_message(session1, "user", "消息1")
        manager.add_message(session2, "user", "消息2")
        
        # 获取所有会话信息
        all_info = manager.get_all_sessions_info()
        
        assert len(all_info) == 2
        assert session1 in all_info
        assert session2 in all_info
        assert all_info[session1]["message_count"] == 1
        assert all_info[session2]["message_count"] == 1
    
    def test_delete_session(self, manager):
        """测试删除会话"""
        session_id = manager.create_session()
        manager.add_message(session_id, "user", "测试消息")
        
        # 验证会话存在
        assert session_id in manager.sessions
        
        # 删除会话
        success = manager.delete_session(session_id)
        assert success
        assert session_id not in manager.sessions
        
        # 删除不存在的会话
        success = manager.delete_session("nonexistent")
        assert not success
    
    def test_clear_all_sessions(self, manager):
        """测试清空所有会话"""
        # 创建多个会话
        session1 = manager.create_session()
        session2 = manager.create_session()
        manager.add_message(session1, "user", "消息1")
        manager.add_message(session2, "user", "消息2")
        
        # 验证会话存在
        assert len(manager.sessions) == 2
        
        # 清空所有会话
        count = manager.clear_all_sessions()
        assert count == 2
        assert len(manager.sessions) == 0
    
    def test_cleanup_old_sessions(self, manager):
        """测试清理过期会话"""
        # 创建会话
        session_id = manager.create_session()
        manager.add_message(session_id, "user", "测试消息")
        
        # 手动设置过期时间
        manager.sessions[session_id]["last_updated"] = time.time() - 25 * 3600  # 25小时前
        
        # 清理过期会话（24小时）
        cleaned_count = manager.cleanup_old_sessions(max_age_hours=24)
        assert cleaned_count == 1
        assert session_id not in manager.sessions
    
    def test_set_get_agent_type(self, manager):
        """测试设置和获取代理类型"""
        session_id = manager.create_session()
        
        # 设置代理类型
        success = manager.set_agent_type(session_id, "test_agent")
        assert success
        
        # 获取代理类型
        agent_type = manager.get_agent_type(session_id)
        assert agent_type == "test_agent"
        
        # 设置不存在的会话
        success = manager.set_agent_type("nonexistent", "test_agent")
        assert not success
        
        # 获取不存在的会话
        agent_type = manager.get_agent_type("nonexistent")
        assert agent_type is None
    
    def test_persistent_storage(self, manager, temp_dir):
        """测试持久化存储"""
        session_id = manager.create_session()
        manager.add_message(session_id, "user", "持久化测试消息")
        manager.set_agent_type(session_id, "test_agent")
        
        # 验证文件被创建
        session_file = manager.storage_dir / f"{session_id}.json"
        assert session_file.exists()
        
        # 读取文件内容
        with open(session_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        assert data["id"] == session_id
        assert len(data["messages"]) == 1
        assert data["agent_type"] == "test_agent"
    
    def test_load_persistent_context(self, manager, temp_dir):
        """测试加载持久化上下文"""
        session_id = "test_persistent_session"
        
        # 手动创建持久化文件
        session_file = manager.storage_dir / f"{session_id}.json"
        session_data = {
            "id": session_id,
            "created_at": time.time(),
            "last_updated": time.time(),
            "messages": [
                {"role": "user", "content": "持久化消息", "timestamp": time.time()}
            ],
            "agent_type": "persistent_agent",
            "metadata": {"test": "data"}
        }
        
        with open(session_file, 'w', encoding='utf-8') as f:
            json.dump(session_data, f)
        
        # 创建会话（应该加载持久化数据）
        created_id = manager.create_session(session_id)
        assert created_id == session_id
        
        # 验证数据被加载
        session = manager.get_session(session_id)
        assert len(session["messages"]) == 1
        assert session["agent_type"] == "persistent_agent"
        assert session["metadata"]["test"] == "data"

@pytest.mark.asyncio
async def test_integration():
    """集成测试"""
    manager = MessageManager()
    
    # 创建会话
    session_id = manager.create_session()
    
    # 模拟对话
    conversation = [
        ("user", "你好，请介绍一下Python"),
        ("assistant", "Python是一种高级编程语言，具有简洁的语法。"),
        ("user", "Python有哪些主要特点？"),
        ("assistant", "Python的主要特点包括：1. 简洁易读 2. 跨平台 3. 丰富的库"),
        ("user", "请推荐一些Python学习资源")
    ]
    
    # 添加对话消息
    for role, content in conversation:
        manager.add_message(session_id, role, content)
    
    # 验证消息历史
    messages = manager.get_messages(session_id)
    assert len(messages) == len(conversation)
    
    # 构建对话消息
    conversation_messages = manager.build_conversation_messages(
        session_id=session_id,
        system_prompt="你是一个Python专家",
        current_message="请详细解释Python的面向对象编程",
        include_history=True
    )
    
    assert len(conversation_messages) == len(conversation) + 2  # 历史 + 系统提示 + 当前消息
    assert conversation_messages[0]["role"] == "system"
    assert conversation_messages[-1]["content"] == "请详细解释Python的面向对象编程"
    
    # 获取会话摘要
    session_info = manager.get_session_info(session_id)
    assert session_info["message_count"] == len(conversation)
    
    # 清理
    manager.clear_all_sessions()
    assert len(manager.sessions) == 0