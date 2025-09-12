"""
子投资组合模块 - 提供JoinQuant兼容的SubPortfolio对象

该模块实现了完整的子投资组合系统，包括：
- SubPortfolio: 子投资组合对象
- SubPortfolioConfig: 子投资组合配置类
- 支持4种账户类型：STOCK, FUTURE, CREDIT, INDEX_FUTURE
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass
from .position import Position


@dataclass
class SubPortfolioConfig:
    """
    子投资组合配置类
    
    用于配置子账户的初始参数
    """
    cash: float                    # 初始资金
    type: str                     # 账户类型: 'stock', 'futures', 'index_futures', 'stock_margin'
    
    def __post_init__(self):
        """验证配置参数"""
        if self.cash < 0:
            raise ValueError("子账户资金不能为负数")
        
        valid_types = ['stock', 'futures', 'index_futures', 'stock_margin']
        if self.type not in valid_types:
            raise ValueError(f"无效的账户类型: {self.type}，支持的类型: {valid_types}")
    
    def to_account_type(self) -> str:
        """转换为标准账户类型"""
        type_mapping = {
            'stock': 'STOCK',
            'futures': 'FUTURE', 
            'index_futures': 'INDEX_FUTURE',
            'stock_margin': 'CREDIT'
        }
        return type_mapping.get(self.type, 'STOCK')


class SubPortfolio:
    """
    子投资组合对象 - JoinQuant兼容
    
    代表一个独立的子账户，有自己的资金和持仓管理。
    支持股票、期货、金融期货、信用账户等类型。
    """
    
    def __init__(self,
                 account_type: str,
                 initial_cash: float = 100000.0,
                 index: int = 0):
        """
        初始化子投资组合
        
        Args:
            account_type: 账户类型 ('STOCK', 'FUTURE', 'CREDIT', 'INDEX_FUTURE')
            initial_cash: 初始资金
            index: 子账户索引
        """
        self._type = account_type
        self._index = index
        self._initial_cash = initial_cash
        
        # 资金相关
        self._available_cash = initial_cash
        self._locked_cash = 0.0
        
        # 持仓相关
        self._positions: Dict[str, Position] = {}
        
        # 损益相关
        self._daily_pnl = 0.0
        self._total_pnl = 0.0
        
        # 时间相关
        self._current_dt = datetime.now()
        self._last_update_time = datetime.now()
        
        # 历史记录
        self._initial_value = initial_cash
        
    @property
    def type(self) -> str:
        """账户类型 - JoinQuant兼容属性"""
        return self._type
    
    @property
    def index(self) -> int:
        """子账户索引"""
        return self._index
    
    @property
    def total_value(self) -> float:
        """子账户总资产 - JoinQuant兼容属性"""
        return self._available_cash + self._locked_cash + self.market_value
    
    @property
    def available_cash(self) -> float:
        """子账户可用资金 - JoinQuant兼容属性"""
        return self._available_cash
    
    @property
    def locked_cash(self) -> float:
        """子账户冻结资金 - JoinQuant兼容属性"""
        return self._locked_cash
    
    @property
    def market_value(self) -> float:
        """子账户持仓市值 - JoinQuant兼容属性"""
        return sum(position.value for position in self._positions.values())
    
    @property
    def positions(self) -> Dict[str, Position]:
        """子账户持仓 - JoinQuant兼容属性"""
        return self._positions.copy()
    
    @property
    def pnl(self) -> float:
        """子账户当日盈亏 - JoinQuant兼容属性"""
        return self._daily_pnl
    
    @property
    def returns(self) -> float:
        """子账户累计收益率 - JoinQuant兼容属性"""
        if self._initial_value <= 0:
            return 0.0
        return (self.total_value - self._initial_value) / self._initial_value
    
    @property
    def initial_cash(self) -> float:
        """初始资金"""
        return self._initial_cash
    
    def update_current_time(self, dt: datetime):
        """
        更新当前时间
        
        Args:
            dt: 新时间
        """
        self._current_dt = dt
    
    def get_position(self, security: str) -> Optional[Position]:
        """
        获取指定证券的持仓
        
        Args:
            security: 证券代码
            
        Returns:
            持仓对象，如果没有持仓则返回空的Position对象
        """
        if security in self._positions:
            return self._positions[security]
        else:
            return Position(security=security)
    
    def update_position_price(self, security: str, price: float):
        """
        更新持仓价格
        
        Args:
            security: 证券代码
            price: 新价格
        """
        if security in self._positions:
            self._positions[security].update_price(price)
    
    def add_position(self, security: str, amount: int, price: float) -> bool:
        """
        增加持仓
        
        Args:
            security: 证券代码
            amount: 数量
            price: 价格
            
        Returns:
            是否成功
        """
        if security not in self._positions:
            self._positions[security] = Position(
                security=security,
                last_price=price
            )
        
        success = self._positions[security].add_position(amount, price)
        if success:
            self._last_update_time = datetime.now()
        
        return success
    
    def reduce_position(self, security: str, amount: int) -> bool:
        """
        减少持仓
        
        Args:
            security: 证券代码
            amount: 减少数量
            
        Returns:
            是否成功
        """
        if security not in self._positions:
            return False
        
        success = self._positions[security].reduce_position(amount)
        
        # 如果持仓为0，移除该持仓
        if success and self._positions[security].total_amount == 0:
            del self._positions[security]
            
        if success:
            self._last_update_time = datetime.now()
        
        return success
    
    def freeze_cash(self, amount: float) -> bool:
        """
        冻结资金
        
        Args:
            amount: 冻结金额
            
        Returns:
            是否成功
        """
        if amount <= 0 or amount > self._available_cash:
            return False
        
        self._available_cash -= amount
        self._locked_cash += amount
        
        return True
    
    def unfreeze_cash(self, amount: float) -> bool:
        """
        解冻资金
        
        Args:
            amount: 解冻金额
            
        Returns:
            是否成功
        """
        if amount <= 0 or amount > self._locked_cash:
            return False
        
        self._locked_cash -= amount
        self._available_cash += amount
        
        return True
    
    def add_cash(self, amount: float):
        """
        增加资金
        
        Args:
            amount: 增加金额
        """
        if amount > 0:
            self._available_cash += amount
    
    def reduce_cash(self, amount: float) -> bool:
        """
        减少资金
        
        Args:
            amount: 减少金额
            
        Returns:
            是否成功
        """
        if amount <= 0 or amount > self._available_cash:
            return False
        
        self._available_cash -= amount
        return True
    
    def transfer_cash_to(self, target_subportfolio: 'SubPortfolio', amount: float) -> bool:
        """
        向另一个子账户转移资金
        
        Args:
            target_subportfolio: 目标子账户
            amount: 转移金额
            
        Returns:
            是否成功
        """
        if amount <= 0 or amount > self._available_cash:
            return False
        
        # 从当前账户减少资金
        if not self.reduce_cash(amount):
            return False
        
        # 向目标账户增加资金
        target_subportfolio.add_cash(amount)
        
        return True
    
    def update_daily_pnl(self):
        """更新当日盈亏"""
        # 计算持仓盈亏
        position_pnl = sum(position.pnl for position in self._positions.values())
        
        # 这里简化处理，实际应该基于昨日收盘价计算
        self._daily_pnl = position_pnl
    
    def reset_daily_pnl(self):
        """重置当日盈亏（通常在每日开始时调用）"""
        self._daily_pnl = 0.0
    
    def get_subportfolio_info(self) -> Dict[str, Any]:
        """
        获取子账户完整信息
        
        Returns:
            包含所有子账户信息的字典
        """
        return {
            'index': self.index,
            'type': self.type,
            'initial_cash': self.initial_cash,
            'total_value': self.total_value,
            'available_cash': self.available_cash,
            'locked_cash': self.locked_cash,
            'market_value': self.market_value,
            'pnl': self.pnl,
            'returns': self.returns,
            'positions_count': len(self._positions),
            'positions': {
                security: position.get_position_info()
                for security, position in self._positions.items()
            },
            'current_dt': self._current_dt,
            'last_update_time': self._last_update_time,
        }
    
    def has_position(self, security: str) -> bool:
        """
        检查是否有持仓
        
        Args:
            security: 证券代码
            
        Returns:
            是否有持仓
        """
        return (security in self._positions and 
                self._positions[security].total_amount > 0)
    
    def get_position_count(self) -> int:
        """
        获取持仓品种数量
        
        Returns:
            持仓品种数
        """
        return len(self._positions)
    
    def is_account_type(self, account_type: str) -> bool:
        """
        检查是否为指定账户类型
        
        Args:
            account_type: 账户类型
            
        Returns:
            是否匹配
        """
        return self._type == account_type
    
    def __repr__(self) -> str:
        """字符串表示"""
        return (f"SubPortfolio("
                f"index={self.index}, "
                f"type={self.type}, "
                f"total_value={self.total_value:.2f}, "
                f"cash={self.available_cash:.2f}, "
                f"market_value={self.market_value:.2f}, "
                f"positions={len(self._positions)}, "
                f"returns={self.returns:.4f})")
    
    def __contains__(self, security: str) -> bool:
        """支持 'in' 操作符"""
        return security in self._positions