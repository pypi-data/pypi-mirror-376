# -*- coding: utf-8 -*-
"""
EmuTrader 滑点管理模块

实现滑点设置和计算功能，支持固定值、百分比和跳数三种滑点模式。
专为模拟交易和策略回测设计，采用简化的规则化滑点模拟。
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
import math


class SlippageBase(ABC):
    """
    滑点基类
    
    所有滑点类型都继承此基类，实现统一的滑点计算接口。
    """
    
    @abstractmethod
    def calculate_slippage(self, price: float, amount: int) -> float:
        """
        计算滑点值
        
        Args:
            price: 预期价格
            amount: 交易数量
            
        Returns:
            float: 滑点值（双边滑点总额）
        """
        pass
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'type': self.__class__.__name__,
            'params': self._get_params()
        }
    
    def _get_params(self) -> Dict[str, Any]:
        """获取参数字典，子类重写"""
        return {}
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self._get_params_str()})"
    
    def _get_params_str(self) -> str:
        """获取参数字符串，子类重写"""
        return ""


class FixedSlippage(SlippageBase):
    """
    固定值滑点
    
    使用固定的价格差值作为滑点，与交易量和价格无关。
    
    Examples:
        FixedSlippage(0.02)  # 固定滑点0.02元
    """
    
    def __init__(self, fixed_value: float):
        """
        初始化固定值滑点
        
        Args:
            fixed_value: 固定滑点值（必须是正数）
        """
        if fixed_value < 0:
            raise ValueError("固定滑点值不能为负数")
        self.fixed_value = float(fixed_value)
    
    def calculate_slippage(self, price: float, amount: int) -> float:
        """计算固定滑点值"""
        return self.fixed_value
    
    def _get_params(self) -> Dict[str, Any]:
        return {'fixed_value': self.fixed_value}
    
    def _get_params_str(self) -> str:
        return f"fixed_value={self.fixed_value}"


class PriceRelatedSlippage(SlippageBase):
    """
    百分比滑点
    
    基于预期价格的百分比计算滑点。
    
    Examples:
        PriceRelatedSlippage(0.002)  # 0.2%的百分比滑点
    """
    
    def __init__(self, percentage: float):
        """
        初始化百分比滑点
        
        Args:
            percentage: 百分比值（例如0.002表示0.2%）
        """
        if percentage < 0:
            raise ValueError("百分比滑点不能为负数")
        self.percentage = float(percentage)
    
    def calculate_slippage(self, price: float, amount: int) -> float:
        """计算百分比滑点值"""
        return price * self.percentage
    
    def _get_params(self) -> Dict[str, Any]:
        return {'percentage': self.percentage}
    
    def _get_params_str(self) -> str:
        return f"percentage={self.percentage}"


class StepRelatedSlippage(SlippageBase):
    """
    跳数滑点（期货专用）
    
    基于合约价格最小变动单位的跳数计算滑点。
    单边滑点 = floor(跳数/2) * 价格步长，双边滑点 = 单边滑点 * 2
    
    Examples:
        StepRelatedSlippage(2)  # 2跳滑点，单边1跳
        StepRelatedSlippage(3, 0.5)  # 3跳滑点，价格步长0.5
    """
    
    def __init__(self, steps: int, price_step: float = 1.0):
        """
        初始化跳数滑点
        
        Args:
            steps: 跳数（必须是正整数）
            price_step: 价格最小变动单位，默认为1.0
        """
        if steps <= 0:
            raise ValueError("跳数必须为正数")
        if price_step <= 0:
            raise ValueError("价格步长必须为正数")
        
        self.steps = int(steps)
        self.price_step = float(price_step)
    
    def calculate_slippage(self, price: float, amount: int) -> float:
        """计算跳数滑点值"""
        # 单边滑点 = floor(跳数/2) * 价格步长
        single_side = math.floor(self.steps / 2) * self.price_step
        # 返回双边滑点总额
        return single_side * 2
    
    def _get_params(self) -> Dict[str, Any]:
        return {'steps': self.steps, 'price_step': self.price_step}
    
    def _get_params_str(self) -> str:
        return f"steps={self.steps}, price_step={self.price_step}"


class SlippageManager:
    """
    滑点管理器
    
    管理滑点配置，提供滑点计算功能。支持三级设置优先级：
    具体标的 > 交易品种 > 全局默认
    """
    
    def __init__(self):
        """初始化滑点管理器"""
        # 默认滑点：PriceRelatedSlippage(0.00246)
        self.default_slippage = PriceRelatedSlippage(0.00246)
        
        # 按交易品种的滑点配置
        self.type_slippage: Dict[str, SlippageBase] = {}
        
        # 按具体标的的滑点配置
        self.specific_slippage: Dict[str, SlippageBase] = {}
        
        # 支持的交易品种类型
        self.supported_types = {
            'stock', 'fund', 'mmf', 'fja', 'fjb', 'fjm',
            'index_futures', 'futures', 'bond_fund', 'stock_fund',
            'QDII_fund', 'mixture_fund', 'money_market_fund'
        }
    
    def set_slippage(self, slippage: SlippageBase, security_type: Optional[str] = None, 
                    ref: Optional[str] = None):
        """
        设置滑点配置
        
        Args:
            slippage: 滑点对象
            security_type: 交易品种类型，为None时全局设置
            ref: 标的代码，为None时按品种设置
            
        Raises:
            ValueError: 参数无效时抛出
        """
        if not isinstance(slippage, SlippageBase):
            raise ValueError("slippage必须是滑点对象")
        
        if ref is not None:
            # 具体标的设置
            if security_type is None:
                raise ValueError("设置具体标的滑点时必须指定type参数")
            if security_type not in self.supported_types:
                raise ValueError(f"不支持的交易品种类型: {security_type}")
            
            self.specific_slippage[ref] = slippage
            
        elif security_type is not None:
            # 品种级别设置
            if security_type not in self.supported_types:
                raise ValueError(f"不支持的交易品种类型: {security_type}")
            
            self.type_slippage[security_type] = slippage
            
        else:
            # 全局设置
            self.default_slippage = slippage
    
    def get_applicable_slippage(self, security: str, security_type: str = 'stock') -> SlippageBase:
        """
        获取适用的滑点配置
        
        优先级：具体标的 > 品种 > 全局默认
        货币基金强制零滑点（最高优先级）
        
        Args:
            security: 证券代码
            security_type: 证券类型
            
        Returns:
            SlippageBase: 适用的滑点配置
        """
        # 货币基金特殊处理：滑点强制为0且不可修改（最高优先级）
        if security_type in ['mmf', 'money_market_fund']:
            return FixedSlippage(0.0)
        
        # 检查具体标的设置
        if security in self.specific_slippage:
            return self.specific_slippage[security]
        
        # 检查品种级别设置
        if security_type in self.type_slippage:
            return self.type_slippage[security_type]
        
        # 返回全局默认滑点
        return self.default_slippage
    
    def calculate_execution_price(self, security: str, expected_price: float, 
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
        if expected_price <= 0:
            raise ValueError("预期价格必须为正数")
        if amount == 0:
            return expected_price
        
        # 获取适用的滑点配置
        slippage = self.get_applicable_slippage(security, security_type)
        
        # 计算滑点值（双边滑点总额）
        slippage_value = slippage.calculate_slippage(expected_price, amount)
        
        # 计算实际成交价格
        if direction == 'open':  # 买入
            # 成交价 = 预期价 + 滑点值/2
            execution_price = expected_price + slippage_value / 2
        else:  # 卖出
            # 成交价 = 预期价 - 滑点值/2
            execution_price = expected_price - slippage_value / 2
        
        # 确保成交价格为正数
        return max(execution_price, 0.01)  # 最低价格0.01元
    
    def get_slippage_info(self, security: str, security_type: str = 'stock') -> Dict[str, Any]:
        """
        获取滑点配置信息
        
        Args:
            security: 证券代码
            security_type: 证券类型
            
        Returns:
            Dict: 滑点配置信息
        """
        slippage = self.get_applicable_slippage(security, security_type)
        return slippage.to_dict()
    
    def clear_slippage(self, security_type: Optional[str] = None, ref: Optional[str] = None):
        """
        清除滑点设置
        
        Args:
            security_type: 交易品种类型，为None时清除所有设置
            ref: 标的代码，为None时按品种清除
        """
        if ref is not None:
            # 清除具体标的设置
            self.specific_slippage.pop(ref, None)
        elif security_type is not None:
            # 清除品种级别设置
            self.type_slippage.pop(security_type, None)
        else:
            # 清除所有自定义设置，恢复默认
            self.type_slippage.clear()
            self.specific_slippage.clear()
            self.default_slippage = PriceRelatedSlippage(0.00246)
    
    def get_all_configurations(self) -> Dict[str, Any]:
        """
        获取所有滑点配置
        
        Returns:
            Dict: 所有配置信息
        """
        return {
            'default': self.default_slippage.to_dict(),
            'type_configs': {k: v.to_dict() for k, v in self.type_slippage.items()},
            'specific_configs': {k: v.to_dict() for k, v in self.specific_slippage.items()}
        }
    
    def __repr__(self) -> str:
        return (f"SlippageManager(default={self.default_slippage}, "
                f"type_count={len(self.type_slippage)}, "
                f"specific_count={len(self.specific_slippage)})")