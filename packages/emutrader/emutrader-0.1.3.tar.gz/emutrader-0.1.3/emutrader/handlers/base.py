# -*- coding: utf-8 -*-
"""
账户处理器基类

定义所有账户处理器的通用接口和行为
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

from ..core.models import AccountState, Position, Order, Transaction
from ..exceptions import EmuTraderException


class BaseAccountHandler(ABC):
    """
    账户处理器抽象基类
    
    定义所有账户类型处理器必须实现的接口
    """
    
    def __init__(self, strategy_name, account_id):
        """
        初始化账户处理器
        
        Args:
            strategy_name (str): 策略名称
            account_id: 账户ID
        """
        self.strategy_name = strategy_name
        self.account_id = account_id
        self.account_type = self._get_account_type()
    
    @abstractmethod
    def _get_account_type(self):
        """获取账户类型"""
        pass
    
    @abstractmethod
    def get_account_state(self):
        """
        获取账户状态
        
        Returns:
            AccountState: 账户状态对象
        """
        pass
    
    @abstractmethod
    def send_order(self, security, amount, price, order_type="limit"):
        """
        发送订单
        
        Args:
            security (str): 证券代码
            amount (int): 数量（正数买入，负数卖出）
            price (float): 价格
            order_type (str): 订单类型
            
        Returns:
            str: 订单ID
        """
        pass
    
    def __repr__(self):
        return f"{self.__class__.__name__}({self.strategy_name}, {self.account_id})"