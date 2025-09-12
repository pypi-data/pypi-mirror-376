# -*- coding: utf-8 -*-
"""
EmuTrader 主类

专注账户管理的核心类，为QSM提供账户数据访问和操作接口。
相当于JQ中context.portfolio和context.subportfolios的提供者。
"""

from typing import Dict, Any, Optional, Union, List
from datetime import datetime, date

from .context import AccountContext
from .models import AccountState, Position, Order, Transaction
from ..exceptions import EmuTraderException, ValidationException
from ..constants import AccountTypes


class EmuTrader:
    """
    EmuTrader 主类 - 账户管理器
    
    为QSM策略系统提供账户数据管理服务，包括：
    - Portfolio和SubPortfolio对象的管理
    - 价格更新和实时盈亏计算
    - 交易执行和账户状态更新
    - 数据持久化和恢复
    """
    
    def _normalize_account_type(self, account_type: str) -> str:
        """
        标准化账户类型，支持兼容性映射
        
        Args:
            account_type: 输入的账户类型
            
        Returns:
            标准化后的账户类型
        """
        if not isinstance(account_type, str):
            return str(account_type).upper()
        
        # 使用兼容性映射
        normalized = AccountTypes.LEGACY_MAPPING.get(account_type.upper())
        if normalized:
            return normalized.upper()
        
        # 如果没有找到映射，默认转为大写
        return account_type.upper()
    
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
        # 使用兼容性映射处理账户类型
        self.account_type = self._normalize_account_type(account_type)
        self.strategy_name = strategy_name
        
        # 创建账户上下文
        self._account_context = AccountContext(
            initial_cash=initial_capital,
            account_type=self.account_type,
            strategy_name=strategy_name
        )
        
    
    
    def get_account_info(self):
        """获取账户信息"""
        return self._account_context.get_context_info()
    
    def order_shares(self, security, amount, price=None, order_type="market"):
        """
        下单买卖股票 (JoinQuant兼容接口)
        
        Args:
            security (str): 证券代码
            amount (int): 股票数量
            price (float, optional): 价格，None表示市价
            order_type (str): 订单类型
            
        Returns:
            bool: 是否成功
        """
        if price is None:
            price = 10.0  # 默认价格，实际应由QSM提供
        return self._account_context.execute_trade(security, amount, price)
    
    # ===============================
    # QSM接口：Portfolio和SubPortfolio访问
    # ===============================
    
    def get_portfolio(self):
        """
        获取Portfolio对象（供QSM的context.portfolio使用）
        
        Returns:
            Portfolio: 投资组合对象
        """
        return self._account_context.portfolio
    
    def get_subportfolios(self):
        """
        获取子账户列表（供QSM的context.subportfolios使用）
        
        Returns:
            List[SubPortfolio]: 子账户列表
        """
        return self._account_context.subportfolios
    
    def get_subportfolio(self, index: int):
        """
        获取指定索引的子账户
        
        Args:
            index: 子账户索引
            
        Returns:
            SubPortfolio或None: 子账户对象
        """
        return self._account_context.get_subportfolio(index)
    
    def add_subportfolio(self, subportfolio):
        """
        添加子账户
        
        Args:
            subportfolio: 子账户对象
        """
        self._account_context.add_subportfolio(subportfolio)
    
    # ===============================
    # QSM接口：价格更新
    # ===============================
    
    def update_market_price(self, security: str, price: float, timestamp: Optional[datetime] = None):
        """
        更新市场价格（供QSM推送tick数据使用）
        
        Args:
            security: 证券代码
            price: 最新价格
            timestamp: 价格时间戳
        """
        self._account_context.update_market_price(security, price, timestamp)
    
    def batch_update_prices(self, price_data: Dict[str, float], timestamp: Optional[datetime] = None):
        """
        批量更新市场价格
        
        Args:
            price_data: 证券代码到价格的映射
            timestamp: 价格时间戳
        """
        self._account_context.batch_update_prices(price_data, timestamp)
    
    def get_all_securities(self) -> List[str]:
        """
        获取所有持仓证券代码（供QSM订阅行情使用）
        
        Returns:
            List[str]: 证券代码列表
        """
        return self._account_context.get_all_securities()
    
    # ===============================
    # QSM接口：交易执行
    # ===============================
    
    def execute_trade(self, security: str, amount: int, price: float, 
                     subportfolio_index: Optional[int] = None) -> bool:
        """
        执行交易（供QSM调用）
        
        Args:
            security: 证券代码
            amount: 交易数量（正数买入，负数卖出）
            price: 交易价格
            subportfolio_index: 子账户索引
            
        Returns:
            bool: 是否执行成功
        """
        return self._account_context.execute_trade(security, amount, price, subportfolio_index)
    
    def transfer_cash(self, from_index: int, to_index: int, amount: float) -> bool:
        """
        子账户间资金转移
        
        Args:
            from_index: 源子账户索引
            to_index: 目标子账户索引  
            amount: 转移金额
            
        Returns:
            bool: 是否转移成功
        """
        return self._account_context.transfer_cash_between_subportfolios(from_index, to_index, amount)
    
    # ===============================
    # QSM接口：数据持久化
    # ===============================
    
    def load_from_db(self, db_path: str) -> bool:
        """
        从数据库加载账户状态（供QSM初始化时调用）
        
        Args:
            db_path: 数据库文件路径
            
        Returns:
            bool: 是否加载成功
        """
        return self._account_context.load_from_db(db_path)
    
    def save_to_db(self, db_path: Optional[str] = None) -> bool:
        """
        保存账户状态到数据库（供QSM定期调用）
        
        Args:
            db_path: 数据库文件路径，None表示使用默认路径
            
        Returns:
            bool: 是否保存成功
        """
        return self._account_context.save_to_db(db_path)
    
    # ===============================
    # JQ兼容接口（向后兼容）
    # ===============================
    
    @property
    def portfolio(self):
        """JQ兼容属性：portfolio"""
        return self.get_portfolio()
    
    @property 
    def subportfolios(self):
        """JQ兼容属性：subportfolios"""
        return self.get_subportfolios()
    
    def __repr__(self):
        return f"EmuTrader(capital={self.initial_capital}, type={self.account_type})"