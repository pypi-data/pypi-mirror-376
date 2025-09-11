# -*- coding: utf-8 -*-
"""
模拟适配器

提供完整的模拟交易环境，支持市场数据模拟、订单处理、价格波动等功能。
用于策略回测和模拟交易测试。
"""

import uuid
import random
import threading
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

from .base import BaseAdapter
from ..core.models import Order, Transaction, Position
from ..constants import OrderStatus, OrderType
from ..exceptions import EmuTraderException, ValidationException


class MockAdapter(BaseAdapter):
    """
    模拟适配器
    
    提供完整的模拟交易功能：
    - 模拟市场数据（价格波动）
    - 订单处理和撮合
    - 滑点和手续费模拟
    - 市场影响模拟
    """
    
    def __init__(self, strategy_name="mock_strategy", account_id=0,
                 enable_price_simulation=True, volatility=0.02, 
                 slippage_rate=0.001, commission_rate=0.0003):
        """
        初始化模拟适配器
        
        Args:
            strategy_name (str): 策略名称
            account_id (int): 账户ID
            enable_price_simulation (bool): 是否启用价格模拟
            volatility (float): 价格波动率（日波动率）
            slippage_rate (float): 滑点率
            commission_rate (float): 佣金费率
        """
        super().__init__(strategy_name, account_id)
        
        # 模拟参数
        self.enable_price_simulation = enable_price_simulation
        self.volatility = volatility
        self.slippage_rate = slippage_rate
        self.commission_rate = commission_rate
        
        # 模拟市场数据
        self._market_prices = {}
        self._base_prices = {
            # 默认股票价格
            '000001.XSHE': 10.0,
            '000002.XSHE': 15.0, 
            '000003.XSHE': 20.0,
            '600000.XSHG': 8.5,
            '600036.XSHG': 35.0,
            '000858.XSHE': 12.5
        }
        
        # 初始化市场价格
        self._initialize_market_data()
        
        # 订单处理
        self._orders = {}
        self._order_queue = []
        self._lock = threading.RLock()
        
        # 启动价格模拟线程（如果启用）
        if self.enable_price_simulation:
            self._start_price_simulation()
    
    def _initialize_market_data(self):
        """初始化市场数据"""
        for security, base_price in self._base_prices.items():
            # 添加随机初始波动
            variation = random.uniform(-0.05, 0.05)
            current_price = base_price * (1 + variation)
            self._market_prices[security] = {
                'price': current_price,
                'last_update': datetime.now(),
                'base_price': base_price,
                'daily_high': current_price,
                'daily_low': current_price,
                'volume': 0
            }
    
    def _start_price_simulation(self):
        """启动价格模拟线程"""
        def update_prices():
            import time
            while self.enable_price_simulation:
                try:
                    self._update_market_prices()
                    time.sleep(1)  # 每秒更新价格
                except:
                    pass
        
        thread = threading.Thread(target=update_prices, daemon=True)
        thread.start()
    
    def _update_market_prices(self):
        """更新市场价格（模拟价格波动）"""
        with self._lock:
            for security, data in self._market_prices.items():
                # 生成随机价格变动
                dt = 1.0 / (365 * 24 * 3600)  # 1秒对应的年化时间
                random_change = random.gauss(0, self.volatility * (dt ** 0.5))
                
                # 更新价格
                old_price = data['price']
                new_price = old_price * (1 + random_change)
                
                # 价格限制（避免异常值）
                base_price = data['base_price']
                min_price = base_price * 0.5
                max_price = base_price * 2.0
                new_price = max(min_price, min(max_price, new_price))
                
                # 更新数据
                data['price'] = new_price
                data['last_update'] = datetime.now()
                data['daily_high'] = max(data['daily_high'], new_price)
                data['daily_low'] = min(data['daily_low'], new_price)
    
    def get_current_price(self, security):
        """
        获取当前价格
        
        Args:
            security (str): 证券代码
            
        Returns:
            float: 当前价格
        """
        if security not in self._market_prices:
            # 为新股票生成随机价格
            base_price = random.uniform(5.0, 50.0)
            self._base_prices[security] = base_price
            self._market_prices[security] = {
                'price': base_price,
                'last_update': datetime.now(),
                'base_price': base_price,
                'daily_high': base_price,
                'daily_low': base_price,
                'volume': 0
            }
        
        return self._market_prices[security]['price']
    
    def get_market_data(self, security):
        """
        获取市场数据
        
        Args:
            security (str): 证券代码
            
        Returns:
            dict: 市场数据
        """
        if security not in self._market_prices:
            self.get_current_price(security)  # 初始化价格
        
        data = self._market_prices[security].copy()
        return data
    
    def validate_security(self, security):
        """
        验证证券代码
        
        Args:
            security (str): 证券代码
            
        Returns:
            bool: 是否有效
        """
        # 简单的格式验证
        if not security or len(security) < 6:
            return False
        
        # 检查格式：6位数字.交易所代码
        parts = security.split('.')
        if len(parts) != 2:
            return False
        
        code, exchange = parts
        if not code.isdigit() or len(code) != 6:
            return False
        
        if exchange not in ['XSHE', 'XSHG']:  # 深交所和上交所
            return False
        
        return True
    
    def send_order(self, security, amount, price=None, order_type="market"):
        """
        发送模拟订单
        
        Args:
            security (str): 证券代码
            amount (int): 订单数量
            price (float, optional): 订单价格
            order_type (str): 订单类型
            
        Returns:
            str: 订单ID
        """
        # 生成订单ID
        order_id = f"MOCK_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"
        
        # 确定成交价格
        if price is None or order_type == "market":
            current_price = self.get_current_price(security)
            # 添加滑点
            if amount > 0:  # 买入滑点向上
                price = current_price * (1 + self.slippage_rate)
            else:  # 卖出滑点向下
                price = current_price * (1 - self.slippage_rate)
        
        # 创建订单对象
        order = Order(
            order_id=order_id,
            security=security,
            amount=amount,
            price=price,
            status=OrderStatus.NEW,
            created_time=datetime.now()
        )
        
        # 保存订单
        with self._lock:
            self._orders[order_id] = order
            self._order_queue.append(order_id)
        
        # 模拟订单处理（延迟执行）
        self._process_order_async(order)
        
        return order_id
    
    def _process_order_async(self, order):
        """异步处理订单"""
        def process():
            import time
            # 模拟订单处理延迟
            delay = random.uniform(0.1, 0.5)  # 100-500ms延迟
            time.sleep(delay)
            
            try:
                with self._lock:
                    if order.order_id in self._orders:
                        # 模拟成交
                        order.status = OrderStatus.FILLED
                        order.filled = order.amount
                        
                        # 更新市场数据
                        if order.security in self._market_prices:
                            self._market_prices[order.security]['volume'] += abs(order.amount)
                        
            except Exception:
                # 订单处理失败
                order.status = OrderStatus.REJECTED
        
        thread = threading.Thread(target=process, daemon=True)
        thread.start()
    
    def get_order(self, order_id):
        """
        获取订单信息
        
        Args:
            order_id (str): 订单ID
            
        Returns:
            Order: 订单对象
        """
        return self._orders.get(order_id)
    
    def get_orders(self, status=None):
        """
        获取订单列表
        
        Args:
            status (str, optional): 订单状态过滤
            
        Returns:
            List[Order]: 订单列表
        """
        with self._lock:
            if status:
                return [order for order in self._orders.values() if order.status == status]
            return list(self._orders.values())
    
    def cancel_order(self, order_id):
        """
        取消订单
        
        Args:
            order_id (str): 订单ID
            
        Returns:
            bool: 是否成功取消
        """
        with self._lock:
            order = self._orders.get(order_id)
            if not order:
                return False
            
            if order.status in [OrderStatus.FILLED, OrderStatus.CANCELLED, OrderStatus.REJECTED]:
                return False
            
            order.status = OrderStatus.CANCELLED
            return True
    
    def get_account_info(self):
        """
        获取模拟账户信息
        
        Returns:
            dict: 账户信息
        """
        return {
            'total_value': 100000.0,
            'available_cash': 100000.0,
            'positions_value': 0.0,
            'frozen_cash': 0.0
        }
    
    def get_positions(self):
        """
        获取模拟持仓
        
        Returns:
            dict: 持仓信息
        """
        return {}
    
    def close(self):
        """
        关闭模拟适配器
        """
        self.enable_price_simulation = False
        with self._lock:
            self._orders.clear()
            self._order_queue.clear()
    
    def get_statistics(self):
        """
        获取模拟适配器统计信息
        
        Returns:
            dict: 统计信息
        """
        with self._lock:
            total_orders = len(self._orders)
            filled_orders = len([o for o in self._orders.values() if o.status == OrderStatus.FILLED])
            
            return {
                'total_securities': len(self._market_prices),
                'total_orders': total_orders,
                'filled_orders': filled_orders,
                'fill_rate': filled_orders / total_orders if total_orders > 0 else 0.0,
                'price_simulation_enabled': self.enable_price_simulation,
                'volatility': self.volatility,
                'slippage_rate': self.slippage_rate,
                'commission_rate': self.commission_rate
            }
    
    def __repr__(self):
        stats = self.get_statistics()
        return f"MockAdapter(securities={stats['total_securities']}, orders={stats['total_orders']})"