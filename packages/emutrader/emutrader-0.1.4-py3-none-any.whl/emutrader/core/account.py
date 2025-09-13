# -*- coding: utf-8 -*-
"""
账户管理类

提供账户状态管理和操作接口。
集成JQ兼容的Context和Portfolio对象。
"""

from typing import Dict, List, Optional, Any
from datetime import datetime

from .models import AccountState, Order, Transaction
from .context import AccountContext
from .portfolio import Portfolio
from .position import Position
from ..handlers.factory import AccountHandlerFactory
from ..exceptions import EmuTraderException, ValidationException


class Account:
    """
    账户管理类
    
    提供账户状态查询、持仓管理、订单管理等功能。
    兼容JoinQuant的账户接口。
    集成了新的Context和Portfolio对象。
    """
    
    def __init__(self, strategy_name=None, initial_cash=100000, account_type="STOCK"):
        """
        初始化账户 - 统一参数顺序（简化API）
        
        Args:
            strategy_name (str): 策略名称
            initial_cash (float): 初始资金
            account_type (str): 账户类型
        """
        self.strategy_name = strategy_name or "default"
        self.initial_cash = float(initial_cash)
        self.account_type = account_type
        
        # 创建新的Context和Portfolio对象
        self._context = AccountContext(
            initial_cash=initial_cash,
            account_type=account_type,
            strategy_name=self.strategy_name
        )
        
        # 创建账户处理器（保持兼容性）
        try:
            self.handler = AccountHandlerFactory.create_handler(
                account_type, self.strategy_name, 0, initial_cash
            )
        except (ImportError, AttributeError, ValueError) as e:
            # 如果处理器创建失败，使用None（使用内置Portfolio）
            self.handler = None
        
        # 账户状态缓存
        self._account_state = None
        self._orders = {}
        self._transactions = []
    
    # === 新增JQ兼容的Context和Portfolio访问接口 ===
    
    @property
    def context(self) -> AccountContext:
        """获取策略上下文对象 - 新增JQ兼容接口"""
        return self._context
    
    @property
    def portfolio(self) -> Portfolio:
        """获取投资组合对象 - 新增JQ兼容接口"""
        return self._context.portfolio
    
    @property
    def subportfolios(self):
        """获取子账户列表 - 新增JQ兼容接口"""
        return self._context.subportfolios
    
    @property
    def current_dt(self):
        """获取当前时间 - 新增JQ兼容接口"""
        return self._context.current_dt
    
    @property
    def run_params(self):
        """获取运行参数 - 新增JQ兼容接口"""
        return self._context.run_params
    
    # === 兼容老版本的接口 ===
    
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
        """总资产 (JoinQuant兼容属性) - 使用新Portfolio"""
        return self._context.portfolio.total_value
    
    @property
    def available_cash(self):
        """可用现金 (JoinQuant兼容属性) - 使用新Portfolio"""
        return self._context.portfolio.available_cash
    
    @property
    def positions_value(self):
        """持仓市值 (JoinQuant兼容属性) - 使用新Portfolio"""
        return self._context.portfolio.market_value
    
    def get_positions(self):
        """
        获取所有持仓 - 使用新Portfolio
        
        Returns:
            Dict[str, Position]: 持仓字典，键为证券代码
        """
        # 优先使用新Portfolio的持仓数据
        return self._context.portfolio.positions
    
    def get_position(self, security):
        """
        获取指定证券的持仓 - 使用新Portfolio
        
        Args:
            security (str): 证券代码
            
        Returns:
            Position: 持仓对象，如果没有持仓返回空Position对象
        """
        return self._context.portfolio.get_position(security)
    
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
    
    # === 新增便利方法 ===
    
    def update_current_time(self, dt: datetime):
        """更新当前时间"""
        self._context.update_current_time(dt)
    
    def add_subportfolio_configs(self, configs):
        """添加子账户配置"""
        from ..api.subportfolio_api import set_subportfolios, set_current_context
        
        # 设置当前上下文
        set_current_context(self._context)
        
        # 设置子账户
        set_subportfolios(configs)
    
    def transfer_cash_between_subportfolios(self, from_index: int, to_index: int, amount: float):
        """子账户间转移资金"""
        return self._context.transfer_cash_between_subportfolios(from_index, to_index, amount)
    
    def get_context_info(self):
        """获取完整上下文信息"""
        return self._context.get_context_info()
    
    def get_portfolio_info(self):
        """获取完整投资组合信息"""
        return self._context.portfolio.get_portfolio_info()
    
    def has_position(self, security: str) -> bool:
        """检查是否有持仓"""
        return self._context.portfolio.has_position(security)
    
    def get_position_count(self) -> int:
        """获取持仓品种数量"""
        return self._context.portfolio.get_position_count()
    
    def __repr__(self):
        return f"Account({self.strategy_name}, {self.account_type}, value={self.total_value:.2f}, subportfolios={len(self.subportfolios)})"
    
    # === 简化的工厂方法 - API简化设计 ===
    
    @classmethod
    def create_stock_account(cls, strategy_name: str, initial_cash: float = 100000):
        """
        快速创建股票账户 - 简化API
        
        Args:
            strategy_name: 策略名称
            initial_cash: 初始资金，默认10万
            
        Returns:
            Account对象
            
        Example:
            >>> account = Account.create_stock_account("my_strategy", 200000)
            >>> print(account.portfolio.total_value)
            200000.0
        """
        return cls(strategy_name=strategy_name, initial_cash=initial_cash, account_type="STOCK")
    
    @classmethod
    def create_future_account(cls, strategy_name: str, initial_cash: float = 100000):
        """
        快速创建期货账户 - 简化API
        
        Args:
            strategy_name: 策略名称
            initial_cash: 初始资金，默认10万
            
        Returns:
            Account对象
        """
        return cls(strategy_name=strategy_name, initial_cash=initial_cash, account_type="FUTURE")
    
    @classmethod
    def create_simple(cls, name: str, cash: float = 100000, type: str = "STOCK"):
        """
        最简化的账户创建方法
        
        Args:
            name: 策略名称（简短参数名）
            cash: 初始资金（简短参数名）
            type: 账户类型（简短参数名）
            
        Returns:
            Account对象
            
        Example:
            >>> account = Account.create_simple("test", 50000)
            >>> account = Account.create_simple("futures_test", 200000, "FUTURE")
        """
        return cls(strategy_name=name, initial_cash=cash, account_type=type)
    
    @classmethod
    def quick_create(cls, name: str, cash: float = 100000):
        """
        最快速的账户创建（默认股票账户）
        
        Args:
            name: 策略名称
            cash: 初始资金
            
        Returns:
            Account对象
            
        Example:
            >>> account = Account.quick_create("demo")  # 默认10万资金
            >>> account = Account.quick_create("big_test", 1000000)  # 100万资金
        """
        return cls.create_stock_account(name, cash)