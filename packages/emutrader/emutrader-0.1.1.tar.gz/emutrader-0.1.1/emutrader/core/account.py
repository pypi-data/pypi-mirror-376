# -*- coding: utf-8 -*-
"""
账户管理类

提供账户状态管理和操作接口。
"""

from typing import Dict, List, Optional, Any
from datetime import datetime

from .models import AccountState, Position, Order, Transaction
from ..handlers.factory import AccountHandlerFactory
from ..exceptions import EmuTraderException, ValidationException


class Account:
    """
    账户管理类
    
    提供账户状态查询、持仓管理、订单管理等功能。
    兼容JoinQuant的账户接口。
    """
    
    def __init__(self, strategy_name, initial_cash=100000, account_type="STOCK"):
        """
        初始化账户
        
        Args:
            strategy_name (str): 策略名称
            initial_cash (float): 初始资金
            account_type (str): 账户类型
        """
        self.strategy_name = strategy_name
        self.initial_cash = float(initial_cash)
        self.account_type = account_type
        
        # 创建账户处理器
        self.handler = AccountHandlerFactory.create_handler(
            account_type, strategy_name, 0, initial_cash
        )
        
        # 账户状态缓存
        self._account_state = None
        self._positions = {}
        self._orders = {}
        self._transactions = []
        
    @property
    def account_info(self):
        """
        获取账户信息 (JoinQuant兼容属性)
        
        Returns:
            AccountState: 账户状态对象
        """
        return self.get_account_state()
    
    def get_account_state(self):
        """
        获取账户状态
        
        Returns:
            AccountState: 账户状态对象
        """
        # 从处理器获取最新状态
        try:
            self._account_state = self.handler.get_account_state()
            return self._account_state
        except Exception as e:
            # 如果处理器未实现，返回默认状态
            return AccountState(
                total_value=self.initial_cash,
                available_cash=self.initial_cash,
                positions_value=0.0
            )
    
    @property
    def total_value(self):
        """总资产 (JoinQuant兼容属性)"""
        return self.get_account_state().total_value
    
    @property
    def available_cash(self):
        """可用现金 (JoinQuant兼容属性)"""
        return self.get_account_state().available_cash
    
    @property
    def positions_value(self):
        """持仓市值 (JoinQuant兼容属性)"""
        return self.get_account_state().positions_value
    
    def get_positions(self):
        """
        获取所有持仓
        
        Returns:
            Dict[str, Position]: 持仓字典，键为证券代码
        """
        # 从处理器获取持仓数据
        if hasattr(self.handler, 'get_positions'):
            return self.handler.get_positions()
        return self._positions
    
    def get_position(self, security):
        """
        获取指定证券的持仓
        
        Args:
            security (str): 证券代码
            
        Returns:
            Position: 持仓对象，如果没有持仓返回None
        """
        return self._positions.get(security)
    
    def order_shares(self, security, amount, price=None, order_type="market"):
        """
        股票下单 (JoinQuant兼容接口)
        
        Args:
            security (str): 证券代码
            amount (int): 股票数量（正数买入，负数卖出）
            price (float, optional): 价格，None表示市价
            order_type (str): 订单类型
            
        Returns:
            str: 订单ID
        """
        try:
            order_id = self.handler.send_order(security, amount, price, order_type)
            return order_id
        except Exception as e:
            raise EmuTraderException(f"下单失败: {str(e)}")
    
    def order_value(self, security, value, price=None, order_type="market"):
        """
        按金额下单 (JoinQuant兼容接口)
        
        Args:
            security (str): 证券代码
            value (float): 交易金额
            price (float, optional): 价格
            order_type (str): 订单类型
            
        Returns:
            str: 订单ID
        """
        if price is None:
            raise ValidationException("按金额下单必须指定价格")
        
        # 计算股票数量
        amount = int(value / price)
        if value < 0:
            amount = -amount
            
        return self.order_shares(security, amount, price, order_type)
    
    def get_orders(self):
        """
        获取所有订单
        
        Returns:
            Dict[str, Order]: 订单字典
        """
        if hasattr(self.handler, 'get_orders'):
            return self.handler.get_orders()
        return self._orders
    
    def get_order(self, order_id):
        """
        获取指定订单
        
        Args:
            order_id (str): 订单ID
            
        Returns:
            Order: 订单对象
        """
        return self._orders.get(order_id)
    
    def cancel_order(self, order_id):
        """
        取消订单
        
        Args:
            order_id (str): 订单ID
            
        Returns:
            bool: 是否成功取消
        """
        # 这里需要与处理器配合实现
        if order_id in self._orders:
            order = self._orders[order_id]
            order.status = Order.STATUS_CANCELED
            return True
        return False
    
    def get_transactions(self):
        """
        获取所有交易记录
        
        Returns:
            List[Transaction]: 交易记录列表
        """
        if hasattr(self.handler, 'get_transactions'):
            return self.handler.get_transactions()
        return self._transactions.copy()
    
    def to_dict(self):
        """转换为字典格式"""
        account_state = self.get_account_state()
        return {
            "strategy_name": self.strategy_name,
            "account_type": self.account_type,
            "account_state": account_state.to_dict() if account_state else None,
            "positions_count": len(self._positions),
            "orders_count": len(self._orders),
            "transactions_count": len(self._transactions)
        }
    
    def __repr__(self):
        return f"Account({self.strategy_name}, {self.account_type}, value={self.total_value:.2f})"