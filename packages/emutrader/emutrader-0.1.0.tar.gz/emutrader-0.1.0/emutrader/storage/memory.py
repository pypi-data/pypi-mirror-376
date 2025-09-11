# -*- coding: utf-8 -*-
"""
内存存储实现
"""

from typing import Dict, Any, Optional
from .base import BaseStorage
from ..core.models import AccountState, Position


class MemoryStorage(BaseStorage):
    """内存存储实现，用于测试和临时使用"""
    
    def __init__(self):
        self._account_states = {}
        self._positions = {}
    
    def initialize(self):
        """初始化内存存储"""
        pass  # 内存存储不需要初始化
    
    def save_account_state(self, account_id, account_state):
        """保存账户状态到内存"""
        self._account_states[account_id] = account_state
    
    def load_account_state(self, account_id):
        """从内存加载账户状态"""
        return self._account_states.get(account_id)
    
    def save_position(self, account_id, security, position):
        """保存持仓到内存"""
        if account_id not in self._positions:
            self._positions[account_id] = {}
        self._positions[account_id][security] = position
    
    def load_positions(self, account_id):
        """从内存加载持仓"""
        return self._positions.get(account_id, {})
    
    def close(self):
        """关闭存储（清理内存）"""
        self._account_states.clear()
        self._positions.clear()