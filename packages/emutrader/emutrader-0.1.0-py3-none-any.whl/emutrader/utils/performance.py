# -*- coding: utf-8 -*-
"""
性能分析器

提供账户性能统计和分析功能。
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import math

from ..core.models import AccountState, Transaction


class PerformanceAnalyzer:
    """
    性能分析器
    
    提供账户和策略的性能统计分析功能。
    """
    
    def __init__(self, initial_capital: float):
        """
        初始化性能分析器
        
        Args:
            initial_capital (float): 初始资金
        """
        self.initial_capital = initial_capital
        self.account_states = []  # 账户状态历史
        self.transactions = []    # 交易记录
        
    def add_account_state(self, account_state: AccountState):
        """
        添加账户状态记录
        
        Args:
            account_state (AccountState): 账户状态
        """
        self.account_states.append(account_state)
    
    def add_transaction(self, transaction: Transaction):
        """
        添加交易记录
        
        Args:
            transaction (Transaction): 交易记录
        """
        self.transactions.append(transaction)
    
    def get_total_return(self) -> float:
        """
        计算总收益率
        
        Returns:
            float: 总收益率
        """
        if not self.account_states:
            return 0.0
            
        current_value = self.account_states[-1].total_value
        return (current_value - self.initial_capital) / self.initial_capital
    
    def get_profit_loss(self) -> float:
        """
        计算盈亏金额
        
        Returns:
            float: 盈亏金额
        """
        if not self.account_states:
            return 0.0
            
        current_value = self.account_states[-1].total_value
        return current_value - self.initial_capital
    
    def get_trade_count(self) -> int:
        """
        获取交易次数
        
        Returns:
            int: 交易次数
        """
        return len(self.transactions)
    
    def get_win_rate(self) -> float:
        """
        计算胜率
        
        Returns:
            float: 胜率 (0-1)
        """
        if not self.transactions:
            return 0.0
            
        profitable_trades = sum(1 for t in self.transactions if t.net_value > 0)
        return profitable_trades / len(self.transactions)
    
    def get_max_drawdown(self) -> float:
        """
        计算最大回撤
        
        Returns:
            float: 最大回撤比例
        """
        if len(self.account_states) < 2:
            return 0.0
            
        values = [state.total_value for state in self.account_states]
        peak = values[0]
        max_drawdown = 0.0
        
        for value in values[1:]:
            if value > peak:
                peak = value
            else:
                drawdown = (peak - value) / peak
                max_drawdown = max(max_drawdown, drawdown)
                
        return max_drawdown
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """
        获取性能摘要
        
        Returns:
            Dict[str, Any]: 性能摘要
        """
        return {
            "initial_capital": self.initial_capital,
            "current_value": self.account_states[-1].total_value if self.account_states else self.initial_capital,
            "total_return": self.get_total_return(),
            "profit_loss": self.get_profit_loss(),
            "trade_count": self.get_trade_count(),
            "win_rate": self.get_win_rate(),
            "max_drawdown": self.get_max_drawdown(),
            "start_date": self.account_states[0].timestamp if self.account_states else None,
            "end_date": self.account_states[-1].timestamp if self.account_states else None
        }
    
    def __repr__(self):
        return f"PerformanceAnalyzer(capital={self.initial_capital}, trades={self.get_trade_count()})"