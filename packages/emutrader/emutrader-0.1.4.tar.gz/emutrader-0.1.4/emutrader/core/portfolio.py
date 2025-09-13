"""
投资组合模块 - 提供JoinQuant兼容的Portfolio对象

该模块实现了完整的投资组合对象，包括：
- total_value: 总资产
- available_cash: 可用资金
- locked_cash: 冻结资金
- market_value: 持仓市值
- positions: 持仓字典
- pnl: 当日盈亏
- returns: 累计收益率
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
from .position import Position, financial_round
from .subportfolio import SubPortfolio


class Portfolio:
    """
    投资组合对象 - JoinQuant兼容
    
    管理账户的资金和持仓信息，提供标准的聚宽兼容接口。
    """
    
    def __init__(self,
                 initial_cash: float = 100000.0,
                 account_type: str = "STOCK",
                 strategy_name: str = "default"):
        """
        初始化投资组合
        
        Args:
            initial_cash: 初始资金
            account_type: 账户类型
            strategy_name: 策略名称
        """
        self._initial_cash = initial_cash
        self._account_type = account_type.upper() if isinstance(account_type, str) else account_type
        self._strategy_name = strategy_name
        
        # 资金相关
        self._available_cash = float(initial_cash)
        self._locked_cash = 0.0
        
        # 持仓相关
        self._positions: Dict[str, Position] = {}
        
        # 损益相关
        self._daily_pnl = 0.0  # 当日盈亏
        self._total_pnl = 0.0  # 累计盈亏
        
        # 时间相关
        self._current_dt = datetime.now()
        self._last_update_time = datetime.now()
        
        # 历史记录
        self._initial_value = initial_cash
        
        # 子账户相关
        self._subportfolios: List[SubPortfolio] = []
        
    @property
    def total_value(self) -> float:
        """总资产 - JoinQuant兼容属性"""
        return financial_round(self._available_cash + self._locked_cash + self.market_value)
    
    @property
    def available_cash(self) -> float:
        """可用资金 - JoinQuant兼容属性"""
        return self._available_cash
    
    @available_cash.setter
    def available_cash(self, value: float):
        """设置可用资金 - 用于测试和调试"""
        self._available_cash = float(value)
    
    @property
    def locked_cash(self) -> float:
        """冻结资金 - JoinQuant兼容属性"""
        return self._locked_cash
    
    @locked_cash.setter
    def locked_cash(self, value: float):
        """设置冻结资金 - 用于测试和调试"""
        self._locked_cash = float(value)
    
    @property
    def market_value(self) -> float:
        """持仓市值 - JoinQuant兼容属性"""
        # 如果有_manual_market_value，使用手动设置的值（用于测试）
        if hasattr(self, '_manual_market_value') and self._manual_market_value is not None:
            return float(self._manual_market_value)
        return float(sum(position.value for position in self._positions.values()))
    
    @market_value.setter
    def market_value(self, value: float):
        """设置持仓市值 - 仅用于测试，实际业务中通过持仓计算"""
        self._manual_market_value = float(value)
    
    @property
    def positions(self) -> Dict[str, Position]:
        """持仓字典 - JoinQuant兼容属性"""
        return self._positions.copy()  # 返回副本，避免外部修改
    
    @property
    def pnl(self) -> float:
        """当日盈亏 - JoinQuant兼容属性"""
        return financial_round(float(self._daily_pnl))
    
    @property
    def returns(self) -> float:
        """累计收益率 - JoinQuant兼容属性"""
        # 官方定义：前一日总权益的累计收益；（前一交易日total_value / inout_cash）
        if self.inout_cash <= 0:
            return 0.0
        # 简化实现，实际需要保存前一日收盘价数据
        return float((self.total_value - self.inout_cash) / self.inout_cash)
    
    @property
    def positions_value(self) -> float:
        """持仓总价值（别名）"""
        return self.market_value
    
    @property
    def initial_cash(self) -> float:
        """初始资金"""
        return self._initial_cash
    
    @property
    def account_type(self) -> str:
        """账户类型"""
        return self._account_type
    
    @property
    def strategy_name(self) -> str:
        """策略名称"""
        return self._strategy_name
    
    @property
    def subportfolios(self) -> List[SubPortfolio]:
        """子账户列表 - JoinQuant兼容属性"""
        return self._subportfolios.copy()
    
    @property
    def long_positions(self) -> Dict[str, Position]:
        """多单仓位 - JoinQuant兼容属性"""
        long_positions = {}
        for subportfolio in self._subportfolios:
            long_positions.update(subportfolio.long_positions)
        return long_positions
    
    @property
    def short_positions(self) -> Dict[str, Position]:
        """空单仓位 - JoinQuant兼容属性"""
        short_positions = {}
        for subportfolio in self._subportfolios:
            short_positions.update(subportfolio.short_positions)
        return short_positions
    
    @property
    def inout_cash(self) -> float:
        """累计出入金 - JoinQuant兼容属性"""
        if not self._subportfolios:
            return self._initial_cash
        return sum(subportfolio.inout_cash for subportfolio in self._subportfolios)
    
    @property
    def transferable_cash(self) -> float:
        """可取资金 - JoinQuant兼容属性"""
        if not self._subportfolios:
            return self.available_cash
        return sum(subportfolio.transferable_cash for subportfolio in self._subportfolios)
    
    @property
    def starting_cash(self) -> float:
        """初始资金 - JoinQuant兼容属性"""
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
            # 返回空的持仓对象，符合JQ行为
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
            # 更新盈亏计算
            self.update_daily_pnl()
    
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
    
    def update_daily_pnl(self):
        """更新当日盈亏"""
        # 计算持仓盈亏
        position_pnl = sum(position.pnl for position in self._positions.values())
        
        # 这里简化处理，实际应该基于昨日收盘价计算
        self._daily_pnl = position_pnl
    
    def reset_daily_pnl(self):
        """重置当日盈亏（通常在每日开始时调用）"""
        self._daily_pnl = 0.0
    
    def get_portfolio_info(self) -> Dict[str, Any]:
        """
        获取投资组合完整信息
        
        Returns:
            包含所有组合信息的字典
        """
        # 计算比例
        total_cash = self.available_cash + self.locked_cash
        total_value = self.total_value
        cash_ratio = total_cash / total_value if total_value > 0 else 0.0
        position_ratio = self.market_value / total_value if total_value > 0 else 0.0
        
        return {
            'strategy_name': self.strategy_name,
            'account_type': self.account_type,
            'initial_cash': self.initial_cash,
            'total_value': self.total_value,
            'available_cash': self.available_cash,
            'locked_cash': self.locked_cash,
            'market_value': self.market_value,
            'pnl': self.pnl,
            'returns': self.returns,
            'positions_count': len(self._positions),
            'cash_ratio': float(cash_ratio),
            'position_ratio': float(position_ratio),
            'positions': {
                security: position.get_position_info()
                for security, position in self._positions.items()
            },
            'current_dt': self._current_dt,
            'last_update_time': self._last_update_time,
        }
    
    def get_positions_list(self) -> List[Dict[str, Any]]:
        """
        获取持仓列表
        
        Returns:
            持仓信息列表
        """
        return [
            position.get_position_info() 
            for position in self._positions.values()
        ]
    
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
    
    def __repr__(self) -> str:
        """字符串表示"""
        return (f"Portfolio("
                f"strategy={self.strategy_name}, "
                f"total_value={self.total_value:.2f}, "
                f"cash={self.available_cash:.2f}, "
                f"market_value={self.market_value:.2f}, "
                f"positions={len(self._positions)}, "
                f"returns={self.returns:.4f})")
    
    def __contains__(self, security: str) -> bool:
        """支持 'in' 操作符"""
        return security in self._positions
    
    def add_subportfolio(self, subportfolio: SubPortfolio):
        """
        添加子账户
        
        Args:
            subportfolio: 子账户对象
        """
        self._subportfolios.append(subportfolio)
    
    def remove_subportfolio(self, index: int) -> bool:
        """
        移除子账户
        
        Args:
            index: 子账户索引
            
        Returns:
            是否成功
        """
        if 0 <= index < len(self._subportfolios):
            self._subportfolios.pop(index)
            return True
        return False
    
    def get_subportfolio(self, index: int) -> Optional[SubPortfolio]:
        """
        获取指定索引的子账户
        
        Args:
            index: 子账户索引
            
        Returns:
            子账户对象，如果不存在则返回None
        """
        if 0 <= index < len(self._subportfolios):
            return self._subportfolios[index]
        return None