# -*- coding: utf-8 -*-
"""
Mock数据提供模块

提供Mock价格数据、交易数据等测试用数据。
"""

import random
import time
from typing import Dict, List, Optional, Union, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass


@dataclass
class MockPriceData:
    """Mock价格数据"""
    security: str
    price: float
    timestamp: datetime
    volume: int = 1000000
    
    
class MockPriceProvider:
    """Mock价格数据提供者"""
    
    def __init__(self, seed: Optional[int] = None):
        """
        初始化Mock价格提供者
        
        Args:
            seed: 随机种子，用于生成可重现的测试数据
        """
        self.seed = seed or int(time.time())
        self._random = random.Random(self.seed)
        self._base_prices = {}  # 基础价格缓存
        self._price_history = {}  # 价格历史
        
        # 预设一些常用股票的基础价格
        self._default_base_prices = {
            '000001.SZ': 12.50,  # 平安银行
            '000002.SZ': 25.80,  # 万科A
            '600519.SH': 1800.0, # 贵州茅台
            '000858.SZ': 45.60,  # 五粮液
            '002415.SZ': 88.90,  # 海康威视
            '000063.SZ': 18.20,  # 中兴通讯
            '300750.SZ': 96.50,  # 宁德时代
            '000876.SZ': 31.40,  # 新希望
            '600000.SH': 8.90,   # 浦发银行
            '600036.SH': 35.80,  # 招商银行
        }
    
    def get_price(self, security: str, timestamp: Optional[datetime] = None) -> float:
        """
        获取指定证券的Mock价格
        
        Args:
            security: 证券代码
            timestamp: 时间戳（可选）
            
        Returns:
            价格
        """
        # 获取基础价格
        if security not in self._base_prices:
            if security in self._default_base_prices:
                base_price = self._default_base_prices[security]
            else:
                # 生成随机基础价格
                base_price = self._random.uniform(5.0, 100.0)
            self._base_prices[security] = base_price
        else:
            base_price = self._base_prices[security]
        
        # 生成价格波动（正态分布，标准差为基础价格的2%）
        volatility = 0.02
        price_change = self._random.gauss(0, base_price * volatility)
        current_price = max(0.01, base_price + price_change)  # 确保价格为正
        
        # 更新基础价格（模拟价格趋势）
        self._base_prices[security] = current_price
        
        # 记录价格历史
        if security not in self._price_history:
            self._price_history[security] = []
        
        timestamp = timestamp or datetime.now()
        self._price_history[security].append(MockPriceData(security, current_price, timestamp))
        
        return round(current_price, 2)
    
    def get_price_series(self, security: str, count: int = 10) -> List[MockPriceData]:
        """
        获取价格序列
        
        Args:
            security: 证券代码
            count: 数据点数量
            
        Returns:
            价格数据列表
        """
        prices = []
        base_time = datetime.now() - timedelta(days=count)
        
        for i in range(count):
            timestamp = base_time + timedelta(days=i)
            price = self.get_price(security, timestamp)
            prices.append(MockPriceData(security, price, timestamp))
        
        return prices
    
    def get_multiple_prices(self, securities: List[str]) -> Dict[str, float]:
        """
        获取多个证券的价格
        
        Args:
            securities: 证券代码列表
            
        Returns:
            证券代码到价格的映射
        """
        return {security: self.get_price(security) for security in securities}
    
    def set_fixed_price(self, security: str, price: float):
        """
        设置固定价格（测试用）
        
        Args:
            security: 证券代码
            price: 固定价格
        """
        self._base_prices[security] = price
    
    def reset_prices(self):
        """重置所有价格数据"""
        self._base_prices.clear()
        self._price_history.clear()
        
    def get_price_history(self, security: str) -> List[MockPriceData]:
        """获取价格历史"""
        return self._price_history.get(security, [])


class MockDataProvider:
    """综合Mock数据提供者"""
    
    def __init__(self, seed: Optional[int] = None):
        """
        初始化Mock数据提供者
        
        Args:
            seed: 随机种子
        """
        self.seed = seed or int(time.time())
        self._random = random.Random(self.seed)
        self.price_provider = MockPriceProvider(seed)
    
    def get_price(self, security: str) -> float:
        """获取价格（委托给价格提供者）"""
        return self.price_provider.get_price(security)
    
    def generate_test_securities(self, count: int = 10) -> List[str]:
        """
        生成测试用证券代码
        
        Args:
            count: 生成数量
            
        Returns:
            证券代码列表
        """
        securities = []
        for i in range(count):
            # 生成深圳和上海的股票代码
            if i % 2 == 0:
                # 深圳股票 (000xxx.SZ, 002xxx.SZ, 300xxx.SZ)
                if i < count // 3:
                    code = f"{i+1:06d}.SZ"
                elif i < 2 * count // 3:
                    code = f"002{i:03d}.SZ"
                else:
                    code = f"300{i:03d}.SZ"
            else:
                # 上海股票 (600xxx.SH, 688xxx.SH)
                if i < 2 * count // 3:
                    code = f"600{i:03d}.SH"
                else:
                    code = f"688{i:03d}.SH"
            securities.append(code)
        
        return securities
    
    def create_random_portfolio_data(self, securities_count: int = 5) -> Dict[str, Dict[str, Union[int, float]]]:
        """
        创建随机投资组合数据
        
        Args:
            securities_count: 证券数量
            
        Returns:
            投资组合数据
        """
        securities = self.generate_test_securities(securities_count)
        portfolio_data = {}
        
        for security in securities:
            portfolio_data[security] = {
                'amount': self._random.randint(100, 5000),  # 持仓数量
                'avg_cost': self._random.uniform(5.0, 100.0),  # 平均成本
                'current_price': self.get_price(security),  # 当前价格
            }
        
        return portfolio_data
    
    def create_test_orders(self, count: int = 5) -> List[Dict[str, Union[str, int, float]]]:
        """
        创建测试订单数据
        
        Args:
            count: 订单数量
            
        Returns:
            订单数据列表
        """
        securities = self.generate_test_securities(count)
        orders = []
        
        for i, security in enumerate(securities):
            order_data = {
                'order_id': f"test_order_{i+1:03d}",
                'security': security,
                'amount': self._random.choice([-2000, -1000, -500, 500, 1000, 2000]),
                'price': self.get_price(security),
                'status': self._random.choice(['new', 'open', 'filled', 'canceled']),
                'created_time': datetime.now() - timedelta(minutes=self._random.randint(1, 1440))
            }
            orders.append(order_data)
        
        return orders
    
    def create_market_simulation_data(self, days: int = 30) -> Dict[str, List[MockPriceData]]:
        """
        创建市场模拟数据
        
        Args:
            days: 天数
            
        Returns:
            市场数据
        """
        securities = ['000001.SZ', '000002.SZ', '600519.SH', '000858.SZ', '002415.SZ']
        market_data = {}
        
        for security in securities:
            market_data[security] = self.price_provider.get_price_series(security, days)
        
        return market_data
    
    def reset_all_data(self):
        """重置所有Mock数据"""
        self.price_provider.reset_prices()
        
    def create_stress_test_data(self, securities_count: int = 100) -> Dict[str, List[MockPriceData]]:
        """
        创建压力测试数据
        
        Args:
            securities_count: 证券数量
            
        Returns:
            大量测试数据
        """
        securities = self.generate_test_securities(securities_count)
        stress_data = {}
        
        for security in securities:
            # 每个证券生成1-10天的数据
            days = self._random.randint(1, 10)
            stress_data[security] = self.price_provider.get_price_series(security, days)
        
        return stress_data


# 全局Mock数据提供者实例
_global_mock_provider: Optional[MockDataProvider] = None


def get_mock_provider() -> MockDataProvider:
    """获取全局Mock数据提供者"""
    global _global_mock_provider
    if _global_mock_provider is None:
        from .test_mode import get_test_config
        seed = get_test_config('mock_data_seed')
        _global_mock_provider = MockDataProvider(seed)
    return _global_mock_provider


def reset_mock_provider():
    """重置全局Mock数据提供者"""
    global _global_mock_provider
    _global_mock_provider = None


def get_mock_price(security: str) -> float:
    """获取Mock价格 - 便利函数"""
    return get_mock_provider().get_price(security)


def create_mock_portfolio(securities_count: int = 5) -> Dict[str, Dict[str, Union[int, float]]]:
    """创建Mock投资组合 - 便利函数"""
    return get_mock_provider().create_random_portfolio_data(securities_count)


def create_mock_orders(count: int = 5) -> List[Dict[str, Union[str, int, float]]]:
    """创建Mock订单 - 便利函数"""
    return get_mock_provider().create_test_orders(count)