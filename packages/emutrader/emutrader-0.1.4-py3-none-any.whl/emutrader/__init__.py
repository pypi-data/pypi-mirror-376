"""
EmuTrader - A Python library for quantitative trading simulation and backtesting.

This package provides tools for:
- Simulating trading environments
- Backtesting trading strategies  
- Managing virtual trading accounts and portfolio
- Analyzing trading performance
- 100% JoinQuant API compatibility
"""

# 导入版本信息
from .__version__ import __version__, VERSION_INFO

__author__ = "Your Name"
__email__ = "your.email@example.com"
__license__ = "MIT"

# 导入核心类和函数
from .core.trader import EmuTrader
from .core.strategy import Strategy
from .core.account import Account
from .core.order import Order, OrderType, OrderStatus

# 导入工具模块
from .utils.data import DataProvider
from .utils.performance import PerformanceAnalyzer

# 导入JoinQuant兼容API
from .api import get_jq_account, get_account, order_shares, order_value, order_target_percent
from .api import set_subportfolios, transfer_cash, set_current_context, set_sub_context, set_order_cost, set_slippage

# 导入新的核心对象
from .core.context import AccountContext
from .core.portfolio import Portfolio
from .core.position import Position
from .core.subportfolio import SubPortfolio, SubPortfolioConfig

# 导入交易成本模型
from .core.models import OrderCost

# 导入滑点相关类
from .core.slippage import SlippageBase, FixedSlippage, PriceRelatedSlippage, StepRelatedSlippage, SlippageManager

# 导入处理器工厂
from .handlers.factory import AccountHandlerFactory

# 定义公开API
__all__ = [
    # 核心类
    "EmuTrader",
    "Strategy", 
    "Account",
    "Order",
    "OrderType",
    "OrderStatus",
    
    # 新增JQ兼容核心对象
    "AccountContext",
    "Portfolio",
    "Position",
    "SubPortfolio",
    "SubPortfolioConfig",
    "OrderCost",
    
    # 滑点相关类
    "SlippageBase",
    "FixedSlippage", 
    "PriceRelatedSlippage",
    "StepRelatedSlippage",
    "SlippageManager",
    
    # JQ兼容API
    "get_jq_account",
    "get_account",
    "order_shares",
    "order_value", 
    "order_target_percent",
    "set_subportfolios",
    "transfer_cash",
    "set_current_context",
    "set_sub_context",
    "set_order_cost",
    "set_slippage",
    
    # 工厂类
    "AccountHandlerFactory",
    
    # 工具类
    "DataProvider",
    "PerformanceAnalyzer",
    
    # 版本信息
    "__version__",
    "__author__",
    "__email__",
    "__license__",
]
