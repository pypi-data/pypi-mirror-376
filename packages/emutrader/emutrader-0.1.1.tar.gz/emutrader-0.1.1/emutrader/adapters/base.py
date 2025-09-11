# -*- coding: utf-8 -*-
"""
适配器基类

定义所有平台适配器的通用接口
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class BaseAdapter(ABC):
    """
    适配器抽象基类
    
    定义所有平台适配器必须实现的接口
    """
    
    def __init__(self, strategy_name, account_id=0):
        """
        初始化适配器
        
        Args:
            strategy_name (str): 策略名称
            account_id: 账户ID
        """
        self.strategy_name = strategy_name
        self.account_id = account_id
    
    @abstractmethod
    def get_account_info(self):
        """获取账户信息"""
        pass
    
    @abstractmethod
    def get_positions(self):
        """获取持仓信息"""
        pass
    
    @abstractmethod
    def send_order(self, security, amount, price, order_type="limit"):
        """发送订单"""
        pass
    
    @abstractmethod
    def close(self):
        """关闭适配器"""
        pass