"""
NagaAgent_core Agents模块

提供Agent服务的基础框架和管理功能
"""

from .registry import AgentRegistry
from .base import BaseAgent

__all__ = [
    "AgentRegistry",
    "BaseAgent"
]
