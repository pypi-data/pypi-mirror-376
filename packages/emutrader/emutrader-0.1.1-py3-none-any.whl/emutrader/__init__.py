"""
EmuTrader - A Python library for quantitative trading simulation and backtesting.

This package provides tools for:
- Simulating trading environments
- Backtesting trading strategies  
- Managing virtual trading accounts
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
from .api import get_jq_account

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
    
    # JQ兼容API
    "get_jq_account",
    
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
