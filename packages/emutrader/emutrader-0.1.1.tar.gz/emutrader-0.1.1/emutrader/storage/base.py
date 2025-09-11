# -*- coding: utf-8 -*-
"""
存储基类

定义所有存储后端的通用接口
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List

from ..core.models import AccountState, Position, Order, Transaction


class BaseStorage(ABC):
    """
    存储抽象基类
    
    定义所有存储后端必须实现的接口
    """
    
    @abstractmethod
    def initialize(self):
        """初始化存储"""
        pass
    
    @abstractmethod
    def save_account_state(self, account_id, account_state):
        """保存账户状态"""
        pass
    
    @abstractmethod
    def load_account_state(self, account_id):
        """加载账户状态"""
        pass
    
    @abstractmethod
    def save_position(self, account_id, security, position):
        """保存持仓信息"""
        pass
    
    @abstractmethod
    def load_positions(self, account_id):
        """加载所有持仓"""
        pass
    
    @abstractmethod
    def close(self):
        """关闭存储连接"""
        pass