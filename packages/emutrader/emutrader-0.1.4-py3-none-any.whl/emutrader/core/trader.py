# -*- coding: utf-8 -*-
"""
EmuTrader 主类

专注账户管理的核心类，为QSM提供账户数据访问和操作接口。
相当于JQ中context.portfolio和context.subportfolios的提供者。
"""

from typing import Dict, Any, Optional, Union, List
from datetime import datetime, date

from .context import AccountContext
from .models import AccountState, Position, Order, Transaction, OrderCost
from .slippage import SlippageManager, SlippageBase
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
        
        # 初始化交易成本管理
        self._order_costs: Dict[str, OrderCost] = {}  # 按type存储的成本配置
        self._specific_order_costs: Dict[str, OrderCost] = {}  # 按ref存储的成本配置
        self._security_type_map: Dict[str, str] = {}  # 证券代码到类型的映射
        
        # 初始化滑点管理器
        self._slippage_manager = SlippageManager()
        
        # 设置默认交易成本（股票标准配置）
        self._default_stock_cost = OrderCost(
            open_tax=0,
            close_tax=0.001,
            open_commission=0.0003,
            close_commission=0.0003,
            close_today_commission=0,
            min_commission=5,
            transfer_fee_rate=0.00001  # A股过户费率：0.001%
        )
        self._order_costs['stock'] = self._default_stock_cost
        
    
    
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
        # 计算交易成本
        direction = 'open' if amount > 0 else 'close'
        total_cost, commission, tax, transfer_fee = self.calculate_trading_cost(
            security, amount, price, direction
        )
        
        # 应用滑点计算实际执行价格
        execution_price = self.calculate_slippage_price(
            security, price, abs(amount), direction
        )
        
        # 调用账户上下文执行交易，传入交易成本和滑点后价格
        return self._account_context.execute_trade(
            security, amount, execution_price, subportfolio_index, 
            total_cost=total_cost, commission=commission, tax=tax, transfer_fee=transfer_fee
        )
    
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
    # 交易成本管理
    # ===============================
    
    def set_order_cost(self, cost: OrderCost, type: str, ref: Optional[str] = None):
        """
        设置交易成本 - JoinQuant兼容方法
        
        Args:
            cost: OrderCost对象
            type: 交易品种类型
            ref: 参考代码（可选）
        """
        if ref is None:
            # 设置品种类型的默认成本
            self._order_costs[type] = cost
        else:
            # 设置特定证券的成本
            self._specific_order_costs[ref] = cost
            # 记录证券代码到类型的映射
            self._security_type_map[ref] = type
    
    def get_order_cost(self, security: str, direction: str = 'open', is_today: bool = False) -> OrderCost:
        """
        获取指定证券的交易成本配置
        
        Args:
            security: 证券代码
            direction: 交易方向 ('open'=买入, 'close'=卖出)
            is_today: 是否平今仓
            
        Returns:
            OrderCost: 交易成本配置
        """
        # 首先检查是否有特定证券的成本配置
        if security in self._specific_order_costs:
            return self._specific_order_costs[security]
        
        # 如果没有特定配置，根据证券类型查找
        security_type = self._security_type_map.get(security, 'stock')  # 默认为股票类型
        
        # 如果没有该类型的配置，使用股票默认配置
        return self._order_costs.get(security_type, self._default_stock_cost)
    
    def calculate_trading_cost(self, security: str, amount: int, price: float, 
                              direction: str = 'open', is_today: bool = False) -> tuple:
        """
        计算交易成本
        
        Args:
            security: 证券代码
            amount: 交易数量
            price: 交易价格
            direction: 交易方向 ('open'=买入, 'close'=卖出)
            is_today: 是否平今仓
            
        Returns:
            tuple: (总成本, 佣金, 印花税)
        """
        cost_config = self.get_order_cost(security, direction, is_today)
        return cost_config.calculate_cost(amount, price, direction, is_today)
    
    # ===============================
    # 滑点管理
    # ===============================
    
    def set_slippage(self, slippage: SlippageBase, security_type: Optional[str] = None, 
                    ref: Optional[str] = None):
        """
        设置滑点配置 - JoinQuant兼容方法
        
        Args:
            slippage: 滑点对象 (FixedSlippage, PriceRelatedSlippage, StepRelatedSlippage)
            security_type: 交易品种类型，为None时全局设置
            ref: 标的代码，为None时按品种设置
            
        Raises:
            ValueError: 参数无效时抛出
        """
        self._slippage_manager.set_slippage(slippage, security_type, ref)
    
    def get_slippage_info(self, security: str, security_type: str = 'stock') -> Dict[str, Any]:
        """
        获取滑点配置信息
        
        Args:
            security: 证券代码
            security_type: 证券类型
            
        Returns:
            Dict: 滑点配置信息
        """
        return self._slippage_manager.get_slippage_info(security, security_type)
    
    def calculate_slippage_price(self, security: str, expected_price: float, 
                                amount: int, direction: str, security_type: str = 'stock') -> float:
        """
        计算滑点后的执行价格
        
        Args:
            security: 证券代码
            expected_price: 预期价格
            amount: 交易数量
            direction: 交易方向 ('open'=买入, 'close'=卖出)
            security_type: 证券类型
            
        Returns:
            float: 滑点后的执行价格
        """
        return self._slippage_manager.calculate_execution_price(
            security, expected_price, amount, direction, security_type
        )
    
    def clear_slippage(self, security_type: Optional[str] = None, ref: Optional[str] = None):
        """
        清除滑点设置
        
        Args:
            security_type: 交易品种类型，为None时清除所有设置
            ref: 标的代码，为None时按品种清除
        """
        self._slippage_manager.clear_slippage(security_type, ref)
    
    def get_all_slippage_configurations(self) -> Dict[str, Any]:
        """
        获取所有滑点配置
        
        Returns:
            Dict: 所有配置信息
        """
        return self._slippage_manager.get_all_configurations()
    
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