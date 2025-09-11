"""
EmuTrader 数据模型

定义账户系统中使用的核心数据结构。
兼容 Python 3.6+，不使用 dataclass 等新特性。
"""

import time
from datetime import datetime
from typing import Dict, List, Optional, Any, Union

from ..exceptions import ValidationException


class AccountState(object):
    """
    账户状态数据模型
    
    代表某一时刻的账户状态快照。
    """
    
    def __init__(self, total_value, available_cash, positions_value, 
                 frozen_cash=0.0, transferable_cash=None, timestamp=None, 
                 version="1.0"):
        """
        初始化账户状态
        
        Args:
            total_value (float): 总资产
            available_cash (float): 可用现金
            positions_value (float): 持仓市值
            frozen_cash (float): 冻结资金
            transferable_cash (float, optional): 可转移资金，默认等于可用现金
            timestamp (datetime, optional): 时间戳
            version (str): 数据版本
        """
        self.total_value = float(total_value)
        self.available_cash = float(available_cash)
        self.positions_value = float(positions_value)
        self.frozen_cash = float(frozen_cash)
        self.transferable_cash = float(transferable_cash if transferable_cash is not None else available_cash)
        self.timestamp = timestamp or datetime.now()
        self.version = version
        
        # 数据一致性验证
        self._validate()
    
    def _validate(self):
        """验证数据一致性"""
        # 基本数值验证
        if self.total_value < 0:
            raise ValidationException("总资产不能为负数")
        if self.available_cash < 0:
            raise ValidationException("可用现金不能为负数")
        if self.positions_value < 0:
            raise ValidationException("持仓市值不能为负数")
        if self.frozen_cash < 0:
            raise ValidationException("冻结资金不能为负数")
            
        # 逻辑一致性验证
        calculated_total = self.available_cash + self.positions_value + self.frozen_cash
        if abs(calculated_total - self.total_value) > 0.01:  # 允许1分钱误差
            raise ValidationException(
                "账户数据不一致：总资产({:.2f}) != 现金({:.2f}) + 持仓({:.2f}) + 冻结({:.2f})".format(
                    self.total_value, self.available_cash, self.positions_value, self.frozen_cash))
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            "total_value": self.total_value,
            "available_cash": self.available_cash,
            "positions_value": self.positions_value,
            "frozen_cash": self.frozen_cash,
            "transferable_cash": self.transferable_cash,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "version": self.version
        }
    
    @classmethod
    def from_dict(cls, data):
        """从字典创建实例"""
        timestamp = None
        if data.get("timestamp"):
            if isinstance(data["timestamp"], str):
                timestamp = datetime.fromisoformat(data["timestamp"])
            else:
                timestamp = data["timestamp"]
        
        return cls(
            total_value=data["total_value"],
            available_cash=data["available_cash"],
            positions_value=data["positions_value"],
            frozen_cash=data.get("frozen_cash", 0.0),
            transferable_cash=data.get("transferable_cash"),
            timestamp=timestamp,
            version=data.get("version", "1.0")
        )
    
    def __repr__(self):
        return "AccountState(total={:.2f}, cash={:.2f}, positions={:.2f})".format(
            self.total_value, self.available_cash, self.positions_value)


class Position(object):
    """
    持仓数据模型
    
    代表单个标的的持仓信息。
    """
    
    def __init__(self, security, total_amount, avg_cost, current_price=None, 
                 closeable_amount=None, acc_avg_cost=None, hold_cost=None,
                 init_time=None, transact_time=None, version="1.0"):
        """
        初始化持仓
        
        Args:
            security (str): 标的代码
            total_amount (int): 总持仓数量
            avg_cost (float): 平均成本价
            current_price (float, optional): 当前价格
            closeable_amount (int, optional): 可平仓数量，默认等于总量
            acc_avg_cost (float, optional): 累计平均成本
            hold_cost (float, optional): 持仓成本
            init_time (datetime, optional): 建仓时间
            transact_time (datetime, optional): 最后交易时间
            version (str): 数据版本
        """
        self.security = security
        self.total_amount = int(total_amount)
        self.avg_cost = float(avg_cost)
        self.current_price = float(current_price) if current_price is not None else avg_cost
        self.closeable_amount = int(closeable_amount if closeable_amount is not None else total_amount)
        self.acc_avg_cost = float(acc_avg_cost if acc_avg_cost is not None else avg_cost)
        self.hold_cost = float(hold_cost if hold_cost is not None else avg_cost)
        self.init_time = init_time or datetime.now()
        self.transact_time = transact_time
        self.version = version
        
        # 验证数据
        self._validate()
    
    def _validate(self):
        """验证数据一致性"""
        if not self.security:
            raise ValidationException("证券代码不能为空")
        if self.total_amount < 0:
            raise ValidationException("持仓数量不能为负数")
        if self.avg_cost < 0:
            raise ValidationException("平均成本不能为负数")
        if self.current_price < 0:
            raise ValidationException("当前价格不能为负数")
        if self.closeable_amount > self.total_amount:
            raise ValidationException("可平仓数量不能超过总持仓数量")
    
    @property
    def value(self):
        """当前市值"""
        return self.total_amount * self.current_price
    
    @property
    def cost_value(self):
        """持仓成本"""
        return self.total_amount * self.avg_cost
    
    @property
    def pnl(self):
        """未实现盈亏"""
        return self.value - self.cost_value
    
    @property
    def pnl_ratio(self):
        """盈亏比例"""
        if self.cost_value == 0:
            return 0.0
        return self.pnl / self.cost_value
    
    def update_price(self, new_price):
        """更新当前价格"""
        self.current_price = float(new_price)
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            "security": self.security,
            "total_amount": self.total_amount,
            "avg_cost": self.avg_cost,
            "current_price": self.current_price,
            "closeable_amount": self.closeable_amount,
            "acc_avg_cost": self.acc_avg_cost,
            "hold_cost": self.hold_cost,
            "value": self.value,
            "pnl": self.pnl,
            "pnl_ratio": self.pnl_ratio,
            "init_time": self.init_time.isoformat() if self.init_time else None,
            "transact_time": self.transact_time.isoformat() if self.transact_time else None,
            "version": self.version
        }
    
    @classmethod
    def from_dict(cls, data):
        """从字典创建实例"""
        init_time = None
        transact_time = None
        
        if data.get("init_time"):
            if isinstance(data["init_time"], str):
                init_time = datetime.fromisoformat(data["init_time"])
            else:
                init_time = data["init_time"]
        
        if data.get("transact_time"):
            if isinstance(data["transact_time"], str):
                transact_time = datetime.fromisoformat(data["transact_time"])
            else:
                transact_time = data["transact_time"]
        
        return cls(
            security=data["security"],
            total_amount=data["total_amount"],
            avg_cost=data["avg_cost"],
            current_price=data.get("current_price"),
            closeable_amount=data.get("closeable_amount"),
            acc_avg_cost=data.get("acc_avg_cost"),
            hold_cost=data.get("hold_cost"),
            init_time=init_time,
            transact_time=transact_time,
            version=data.get("version", "1.0")
        )
    
    def __repr__(self):
        return "Position({}, amount={}, price={:.3f}, value={:.2f})".format(
            self.security, self.total_amount, self.current_price, self.value)


class Order(object):
    """
    订单数据模型 - JoinQuant兼容
    
    记录订单的完整生命周期，包括待处理、已成交、已取消等状态。
    完全兼容JoinQuant平台的Order对象。
    """
    
    # JoinQuant标准订单状态
    STATUS_NEW = 'new'              # 未报
    STATUS_OPEN = 'open'            # 已报未成交
    STATUS_FILLED = 'filled'        # 完全成交
    STATUS_CANCELED = 'canceled'    # 已撤单
    STATUS_REJECTED = 'rejected'    # 拒单
    STATUS_HELD = 'held'           # 挂起（部分成交后暂停）
    
    def __init__(self, order_id, security, amount, price=None, 
                 style=None, status=STATUS_NEW, filled=0, 
                 commission=0.0, tax=0.0, created_time=None, 
                 action='open_long', version="1.0"):
        """
        初始化订单对象
        
        Args:
            order_id (str): 订单ID
            security (str): 证券代码
            amount (int): 订单数量（正数买入，负数卖出）
            price (float, optional): 订单价格，None表示市价单
            style (str, optional): 订单类型，暂未使用
            status (str): 订单状态
            filled (int): 已成交数量
            commission (float): 佣金费用
            tax (float): 税费
            created_time (datetime, optional): 创建时间
            action (str): 订单动作类型
            version (str): 数据版本
        """
        self.order_id = order_id
        self.security = security
        self.amount = int(amount)
        self.price = float(price) if price is not None else None
        self.style = style
        self.status = status
        self.filled = int(filled)
        self.commission = float(commission)
        self.tax = float(tax)
        self.created_time = created_time or datetime.now()
        self.action = action
        self.version = version
        
        # 验证数据
        self._validate()
    
    def _validate(self):
        """验证数据一致性"""
        if not self.order_id:
            raise ValidationException("订单ID不能为空")
        if not self.security:
            raise ValidationException("证券代码不能为空")
        if self.amount == 0:
            raise ValidationException("订单数量不能为零")
        if self.price is not None and self.price <= 0:
            raise ValidationException("订单价格必须大于零")
        if self.filled < 0:
            raise ValidationException("已成交数量不能为负数")
        if abs(self.filled) > abs(self.amount):
            raise ValidationException("已成交数量不能超过订单数量")
        if self.commission < 0:
            raise ValidationException("佣金不能为负数")
        if self.tax < 0:
            raise ValidationException("税费不能为负数")
    
    @property
    def is_buy(self):
        """是否为买单"""
        return self.amount > 0
    
    @property 
    def is_sell(self):
        """是否为卖单"""
        return self.amount < 0
    
    @property
    def unfilled(self):
        """未成交数量"""
        return self.amount - self.filled
    
    @property
    def is_finished(self):
        """是否已完成（成交或取消）"""
        return self.status in [self.STATUS_FILLED, self.STATUS_CANCELED, self.STATUS_REJECTED]
    
    @property
    def avg_cost(self):
        """平均成交价格"""
        if self.filled == 0 or self.price is None:
            return 0.0
        return self.price
    
    @property 
    def order_type(self):
        """订单类型（兼容老版本）"""
        return 'buy' if self.is_buy else 'sell'
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            "order_id": self.order_id,
            "security": self.security,
            "amount": self.amount,
            "price": self.price,
            "style": self.style,
            "status": self.status,
            "filled": self.filled,
            "commission": self.commission,
            "tax": self.tax,
            "created_time": self.created_time.isoformat() if self.created_time else None,
            "action": self.action,
            "version": self.version
        }
    
    @classmethod
    def from_dict(cls, data):
        """从字典创建实例"""
        created_time = None
        if data.get("created_time"):
            if isinstance(data["created_time"], str):
                created_time = datetime.fromisoformat(data["created_time"])
            else:
                created_time = data["created_time"]
        
        return cls(
            order_id=data["order_id"],
            security=data["security"],
            amount=data["amount"],
            price=data.get("price"),
            style=data.get("style"),
            status=data.get("status", cls.STATUS_NEW),
            filled=data.get("filled", 0),
            commission=data.get("commission", 0.0),
            tax=data.get("tax", 0.0),
            created_time=created_time,
            action=data.get("action", "open_long"),
            version=data.get("version", "1.0")
        )
    
    def __repr__(self):
        return "Order({}, {}, {}@{:.2f}, {})".format(
            self.order_id[:8], self.security, self.amount, 
            self.price or 0, self.status)


class Transaction(object):
    """
    交易记录数据模型
    
    记录已成交的交易详细信息。
    """
    
    def __init__(self, order_id, security, amount, price, order_type, 
                 commission=0.0, tax=0.0, status="filled", 
                 created_at=None, filled_at=None, version="1.0"):
        """
        初始化交易记录
        
        Args:
            order_id (str): 订单ID
            security (str): 证券代码
            amount (int): 交易数量（正数买入，负数卖出）
            price (float): 成交价格
            order_type (str): 订单类型 ('buy', 'sell')
            commission (float): 佣金费用
            tax (float): 税费
            status (str): 订单状态
            created_at (datetime, optional): 创建时间
            filled_at (datetime, optional): 成交时间
            version (str): 数据版本
        """
        self.order_id = order_id
        self.security = security
        self.amount = int(amount)
        self.price = float(price)
        self.order_type = order_type
        self.commission = float(commission)
        self.tax = float(tax)
        self.status = status
        self.created_at = created_at or datetime.now()
        self.filled_at = filled_at
        self.version = version
        
        # 验证数据
        self._validate()
    
    def _validate(self):
        """验证数据一致性"""
        if not self.order_id:
            raise ValidationException("订单ID不能为空")
        if not self.security:
            raise ValidationException("证券代码不能为空")
        if self.amount == 0:
            raise ValidationException("交易数量不能为零")
        if self.price <= 0:
            raise ValidationException("成交价格必须大于零")
        if self.order_type not in ['buy', 'sell']:
            raise ValidationException("订单类型必须为 'buy' 或 'sell'")
        if self.commission < 0:
            raise ValidationException("佣金不能为负数")
        if self.tax < 0:
            raise ValidationException("税费不能为负数")
    
    @property
    def total_value(self):
        """交易总金额（包含费用）"""
        base_value = abs(self.amount) * self.price
        return base_value + self.commission + self.tax
    
    @property
    def net_value(self):
        """净交易金额"""
        base_value = self.amount * self.price
        if self.amount > 0:  # 买入
            return -(base_value + self.commission + self.tax)
        else:  # 卖出
            return abs(base_value) - self.commission - self.tax
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            "order_id": self.order_id,
            "security": self.security,
            "amount": self.amount,
            "price": self.price,
            "order_type": self.order_type,
            "commission": self.commission,
            "tax": self.tax,
            "status": self.status,
            "total_value": self.total_value,
            "net_value": self.net_value,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "filled_at": self.filled_at.isoformat() if self.filled_at else None,
            "version": self.version
        }
    
    @classmethod
    def from_dict(cls, data):
        """从字典创建实例"""
        created_at = None
        filled_at = None
        
        if data.get("created_at"):
            if isinstance(data["created_at"], str):
                created_at = datetime.fromisoformat(data["created_at"])
            else:
                created_at = data["created_at"]
        
        if data.get("filled_at"):
            if isinstance(data["filled_at"], str):
                filled_at = datetime.fromisoformat(data["filled_at"])
            else:
                filled_at = data["filled_at"]
        
        return cls(
            order_id=data["order_id"],
            security=data["security"],
            amount=data["amount"],
            price=data["price"],
            order_type=data["order_type"],
            commission=data.get("commission", 0.0),
            tax=data.get("tax", 0.0),
            status=data.get("status", "filled"),
            created_at=created_at,
            filled_at=filled_at,
            version=data.get("version", "1.0")
        )
    
    def __repr__(self):
        return "Transaction({}, {}, amount={}, price={:.3f})".format(
            self.order_id, self.security, self.amount, self.price)


# 配置相关的数据类
class StorageConfig(object):
    """存储配置"""
    
    def __init__(self, storage_type="sqlite", path=None, **kwargs):
        self.type = storage_type
        self.path = path
        self.options = kwargs


class CacheConfig(object):
    """缓存配置"""
    
    def __init__(self, update_interval=5, batch_size=100, max_size=10000, **kwargs):
        self.update_interval = update_interval  # 批量更新间隔（秒）
        self.batch_size = batch_size            # 批量操作大小
        self.max_size = max_size                # 最大缓存条目数
        self.options = kwargs