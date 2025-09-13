"""
持仓对象模块 - 提供JoinQuant兼容的Position对象

该模块实现了完整的持仓对象，包括：
- total_amount: 总持仓量
- closeable_amount: 可平仓量
- avg_cost: 平均成本
- value: 持仓价值
- pnl: 持仓盈亏
- side: 持仓方向
"""

from typing import Optional
from datetime import datetime


def financial_round(value: float, decimals: int = 2) -> float:
    """
    金融数据精度处理 - 保留指定小数位
    
    Args:
        value: 原始数值
        decimals: 保留小数位数，默认2位
        
    Returns:
        处理后的数值
    """
    if value == 0:
        return 0.0
    return round(value, decimals)


class Position:
    """
    持仓对象 - JoinQuant兼容
    
    代表某个证券的持仓信息，包括数量、成本、价值和盈亏等。
    """
    
    def __init__(self,
                 security: str,
                 total_amount: int = 0,
                 avg_cost: float = 0.0,
                 side: str = 'long',
                 last_price: float = 0.0):
        """
        初始化持仓对象
        
        Args:
            security: 证券代码
            total_amount: 总持仓量
            avg_cost: 平均成本
            side: 持仓方向 ('long' 或 'short')
            last_price: 最新价格
        """
        self.security = security
        self.total_amount = total_amount
        self.avg_cost = avg_cost
        # 根据数量自动设置side
        if total_amount < 0:
            self.side = 'short'
        else:
            self.side = side
        self.acc_avg_cost = avg_cost  # 累计持仓成本
        self.hold_cost = last_price  # 当日持仓成本
        self.last_price = last_price
        self.locked_amount = 0  # 冻结数量
        self._last_update_time = datetime.now()
        self.init_time = datetime.now()  # 建仓时间
        self.transact_time = datetime.now()  # 最后交易时间
        self.today_amount = 0  # 今天开的仓位
        self.pindex = 0  # 仓位索引
        
    @property
    def closeable_amount(self) -> int:
        """可平仓量 - JoinQuant兼容属性"""
        return max(0, self.total_amount - self.locked_amount)
    
        
    @property
    def value(self) -> float:
        """持仓价值 - JoinQuant兼容属性"""
        if self.last_price <= 0:
            return 0.0
        return financial_round(abs(self.total_amount) * self.last_price)
    
    @property
    def pnl(self) -> float:
        """持仓盈亏 - JoinQuant兼容属性"""
        if self.total_amount == 0 or self.avg_cost <= 0 or self.last_price <= 0:
            return 0.0
        
        if self.side == 'long':
            return financial_round(self.total_amount * (self.last_price - self.avg_cost))
        else:  # short
            return financial_round(self.total_amount * (self.avg_cost - self.last_price))
    
    def update_price(self, price: float):
        """
        更新最新价格
        
        Args:
            price: 新价格
        """
        if price > 0:
            self.last_price = price
            self._last_update_time = datetime.now()
    
    def add_position(self, amount: int, cost: float) -> bool:
        """
        增加持仓
        
        Args:
            amount: 增加的数量 (正数)
            cost: 成交价格
            
        Returns:
            是否成功
        """
        if amount <= 0 or cost <= 0:
            return False
            
        # 计算新的平均成本
        old_value = self.total_amount * self.avg_cost
        new_value = amount * cost
        total_amount = self.total_amount + amount
        
        if total_amount > 0:
            self.avg_cost = financial_round((old_value + new_value) / total_amount)
            
        self.total_amount = total_amount
        self._last_update_time = datetime.now()
        
        return True
    
    def reduce_position(self, amount: int) -> bool:
        """
        减少持仓
        
        Args:
            amount: 减少的数量 (正数)
            
        Returns:
            是否成功
        """
        if amount <= 0 or amount > self.closeable_amount:
            return False
            
        self.total_amount -= amount
        
        # 如果持仓为0，重置平均成本
        if self.total_amount == 0:
            self.avg_cost = 0.0
            
        self._last_update_time = datetime.now()
        
        return True
    
    def lock_position(self, amount: int) -> bool:
        """
        冻结持仓
        
        Args:
            amount: 冻结数量
            
        Returns:
            是否成功
        """
        if amount <= 0 or amount > (self.total_amount - self.locked_amount):
            return False
            
        self.locked_amount += amount
        return True
    
    def unlock_position(self, amount: int) -> bool:
        """
        解冻持仓
        
        Args:
            amount: 解冻数量
            
        Returns:
            是否成功
        """
        if amount <= 0 or amount > self.locked_amount:
            return False
            
        self.locked_amount -= amount
        return True
    
    def get_position_info(self) -> dict:
        """
        获取持仓完整信息
        
        Returns:
            包含所有持仓信息的字典
        """
        return {
            'security': self.security,
            'total_amount': self.total_amount,
            'closeable_amount': self.closeable_amount,
            'locked_amount': self.locked_amount,
            'avg_cost': self.avg_cost,
            'last_price': self.last_price,
            'value': self.value,
            'pnl': self.pnl,
            'pnl_ratio': self.pnl / (self.avg_cost * abs(self.total_amount)) if self.avg_cost > 0 and self.total_amount != 0 else 0.0,
            'side': self.side,
            'last_update_time': self._last_update_time,
        }
    
    def __repr__(self) -> str:
        """字符串表示"""
        return (f"Position({self.security}, "
                f"amount={self.total_amount}, "
                f"cost={self.avg_cost:.4f}, "
                f"value={self.value:.2f}, "
                f"pnl={self.pnl:.2f})")
    
    def __bool__(self) -> bool:
        """布尔值表示 - 有持仓时为True"""
        return self.total_amount != 0