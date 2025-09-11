# -*- coding: utf-8 -*-
"""
EmuTrader 主类

提供模拟交易的核心功能，包括策略执行、回测等。
"""

from typing import Dict, Any, Optional, Union
from datetime import datetime, date

from .models import AccountState, Position, Order, Transaction
from ..handlers.factory import AccountHandlerFactory
from ..exceptions import EmuTraderException, ValidationException


class EmuTrader:
    """
    EmuTrader 主类
    
    提供模拟交易环境的核心功能，支持策略回测和实时模拟交易。
    """
    
    def __init__(self, initial_capital=100000, account_type="STOCK", 
                 strategy_name="default_strategy"):
        """
        初始化EmuTrader实例
        
        Args:
            initial_capital (float): 初始资金
            account_type (str): 账户类型 (STOCK/FUTURE/CREDIT)
            strategy_name (str): 策略名称
        """
        self.initial_capital = float(initial_capital)
        self.account_type = account_type
        self.strategy_name = strategy_name
        
        # 创建账户处理器
        self.account_handler = AccountHandlerFactory.create_handler(
            account_type, strategy_name, 0, initial_capital
        )
        
        # 初始化状态
        self._initialize_account()
        
    def _initialize_account(self):
        """初始化账户状态"""
        # 这里需要与账户处理器配合初始化
        pass
    
    def run_backtest(self, strategy, start_date, end_date, **kwargs):
        """
        运行回测
        
        Args:
            strategy: 策略对象
            start_date: 开始日期
            end_date: 结束日期
            **kwargs: 其他参数
        """
        # 回测逻辑实现
        raise NotImplementedError("回测功能待实现")
    
    def get_performance_report(self):
        """
        获取性能报告
        
        Returns:
            dict: 性能统计报告
        """
        # 性能分析实现
        return {
            "total_return": 0.0,
            "sharpe_ratio": 0.0,
            "max_drawdown": 0.0,
            "trades_count": 0
        }
    
    def get_account_info(self):
        """获取账户信息"""
        return self.account_handler.get_account_state()
    
    def order_shares(self, security, amount, price=None, order_type="market"):
        """
        下单买卖股票 (JoinQuant兼容接口)
        
        Args:
            security (str): 证券代码
            amount (int): 股票数量
            price (float, optional): 价格，None表示市价
            order_type (str): 订单类型
            
        Returns:
            str: 订单ID
        """
        return self.account_handler.send_order(security, amount, price, order_type)
    
    def __repr__(self):
        return f"EmuTrader(capital={self.initial_capital}, type={self.account_type})"