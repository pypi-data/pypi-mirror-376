# -*- coding: utf-8 -*-
"""
股票账户处理器

实现股票账户的完整业务逻辑，包括账户状态管理、订单处理、持仓管理等。
"""

import uuid
import threading
from datetime import datetime
from typing import Dict, List, Optional, Any

from .base import BaseAccountHandler
from ..core.models import AccountState, Position, Order, Transaction
from ..constants import AccountTypes, OrderStatus, OrderType, Direction
from ..exceptions import EmuTraderException, ValidationException
from ..utils.data import DataProvider
from ..storage.sqlite import SQLiteStorage
from ..storage.cache import AccountCacheManager


class StockAccountHandler(BaseAccountHandler):
    """
    股票账户处理器
    
    提供完整的股票账户管理功能，包括：
    - 账户状态管理
    - 订单生命周期管理
    - 持仓计算和更新
    - 资金变动处理
    - 风险控制
    """
    
    def __init__(self, strategy_name, account_id, initial_cash=100000, 
                 db_path=None, enable_cache=True):
        """
        初始化股票账户处理器
        
        Args:
            strategy_name (str): 策略名称
            account_id: 账户ID
            initial_cash (float): 初始资金
            db_path (str, optional): 数据库路径，None使用默认路径
            enable_cache (bool): 是否启用缓存
        """
        super().__init__(strategy_name, account_id)
        
        # 账户基础信息
        self.initial_cash = float(initial_cash)
        
        # 存储和缓存系统
        if db_path is None:
            db_path = f"data/emutrader_account_{account_id}.db"
        
        self._storage = SQLiteStorage(db_path)
        self._cache = AccountCacheManager() if enable_cache else None
        
        # 数据提供者（集成Mock适配器）
        from ..adapters.mock_adapter import MockAdapter
        mock_adapter = MockAdapter(
            strategy_name=strategy_name,
            account_id=account_id,
            enable_price_simulation=True,
            volatility=0.01,  # 1%日波动率
            slippage_rate=0.0005  # 0.05%滑点
        )
        self._data_provider = DataProvider(source="mock", adapter=mock_adapter)
        
        # 线程安全锁
        self._lock = threading.RLock()
        
        # 风险控制参数
        self._max_position_ratio = 0.95  # 最大仓位比例
        self._min_cash_ratio = 0.05      # 最小现金比例
        
        # 初始化账户数据（从存储加载或创建新账户）
        self._load_or_initialize_account()
        
    def _load_or_initialize_account(self):
        """加载或初始化账户数据"""
        try:
            # 先尝试从缓存加载
            if self._cache:
                cached_state = self._cache.get_cached_account_state(
                    self.strategy_name, self.account_id
                )
                cached_positions = self._cache.get_cached_positions(
                    self.strategy_name, self.account_id
                )
                
                if cached_state and cached_positions is not None:
                    self._available_cash = cached_state.available_cash
                    self._frozen_cash = cached_state.frozen_cash
                    self._positions = cached_positions
                    self._orders = {}  # 订单不缓存，从存储加载
                    self._transactions = []
                    print(f"从缓存加载账户 {self.strategy_name}:{self.account_id}")
                    return
            
            # 从存储加载
            account_state = self._storage.load_account_state(
                self.strategy_name, self.account_id
            )
            positions = self._storage.load_positions(
                self.strategy_name, self.account_id
            )
            
            if account_state:
                self._available_cash = account_state.available_cash
                self._frozen_cash = account_state.frozen_cash
                self._positions = positions or {}
                self._orders = {}
                self._transactions = []
                print(f"从存储加载账户 {self.strategy_name}:{self.account_id}")
            else:
                # 创建新账户
                self._available_cash = self.initial_cash
                self._frozen_cash = 0.0
                self._positions = {}
                self._orders = {}
                self._transactions = []
                
                # 保存初始状态
                initial_state = AccountState(
                    total_value=self.initial_cash,
                    available_cash=self.initial_cash,
                    positions_value=0.0,
                    frozen_cash=0.0
                )
                self._storage.save_account_state(
                    self.strategy_name, self.account_id, initial_state, AccountTypes.STOCK
                )
                print(f"创建新账户 {self.strategy_name}:{self.account_id}")
                
        except Exception as e:
            print(f"加载账户数据失败: {e}, 使用默认值")
            # fallback到默认值
            self._available_cash = self.initial_cash
            self._frozen_cash = 0.0
            self._positions = {}
            self._orders = {}
            self._transactions = []
    
    def _save_account_state(self):
        """保存账户状态到存储和缓存"""
        try:
            account_state = self.get_account_state()
            
            # 保存到存储
            self._storage.save_account_state(
                self.strategy_name, self.account_id, account_state, AccountTypes.STOCK
            )
            
            # 保存到缓存
            if self._cache:
                self._cache.cache_account_state(
                    self.strategy_name, self.account_id, account_state
                )
                self._cache.cache_positions(
                    self.strategy_name, self.account_id, self._positions
                )
                
        except Exception as e:
            print(f"保存账户状态失败: {e}")
    
    def _get_account_type(self):
        """获取账户类型"""
        return AccountTypes.STOCK
    
    def get_account_state(self):
        """
        获取股票账户状态
        
        Returns:
            AccountState: 当前账户状态快照
        """
        with self._lock:
            # 更新持仓市值
            positions_value = self._calculate_positions_value()
            total_value = self._available_cash + self._frozen_cash + positions_value
            
            return AccountState(
                total_value=total_value,
                available_cash=self._available_cash,
                positions_value=positions_value,
                frozen_cash=self._frozen_cash,
                timestamp=datetime.now()
            )
    
    def _calculate_positions_value(self):
        """
        计算持仓总市值
        
        Returns:
            float: 持仓总市值
        """
        total_value = 0.0
        for security, position in self._positions.items():
            if position.total_amount > 0:
                # 更新当前价格
                current_price = self._data_provider.get_current_price(security)
                position.update_price(current_price)
                total_value += position.value
        return total_value
    
    def get_positions(self):
        """
        获取所有持仓
        
        Returns:
            Dict[str, Position]: 持仓字典
        """
        with self._lock:
            # 更新所有持仓的当前价格
            for security, position in self._positions.items():
                if position.total_amount > 0:
                    current_price = self._data_provider.get_current_price(security)
                    position.update_price(current_price)
            return self._positions.copy()
    
    def get_position(self, security):
        """
        获取指定证券的持仓
        
        Args:
            security (str): 证券代码
            
        Returns:
            Position: 持仓对象，如果没有持仓返回None
        """
        position = self._positions.get(security)
        if position and position.total_amount > 0:
            # 更新当前价格
            current_price = self._data_provider.get_current_price(security)
            position.update_price(current_price)
            return position
        return None
    
    def send_order(self, security, amount, price=None, order_type="market"):
        """
        发送股票订单
        
        Args:
            security (str): 证券代码
            amount (int): 股票数量（正数买入，负数卖出）
            price (float, optional): 价格，None表示市价单
            order_type (str): 订单类型
            
        Returns:
            str: 订单ID
            
        Raises:
            ValidationException: 参数验证失败
            EmuTraderException: 下单失败
        """
        with self._lock:
            # 参数验证
            self._validate_order_params(security, amount, price, order_type)
            
            # 风险检查
            self._check_order_risk(security, amount, price)
            
            # 生成订单ID
            order_id = f"STK_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"
            
            # 确定成交价格
            if price is None:  # 市价单
                price = self._data_provider.get_current_price(security)
            
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
            self._orders[order_id] = order
            
            # 冻结资金（买单）或持仓（卖单）
            if amount > 0:  # 买单
                required_cash = amount * price * 1.001  # 包含手续费
                self._freeze_cash(required_cash)
            else:  # 卖单
                required_shares = abs(amount)
                self._freeze_position(security, required_shares)
            
            # 模拟订单处理（实际应该异步处理）
            self._process_order(order)
            
            return order_id
    
    def _validate_order_params(self, security, amount, price, order_type):
        """验证订单参数"""
        if not security:
            raise ValidationException("证券代码不能为空")
        
        if not self._data_provider.validate_security(security):
            raise ValidationException(f"无效的证券代码: {security}")
        
        if amount == 0:
            raise ValidationException("订单数量不能为零")
        
        if abs(amount) < 100:
            raise ValidationException("股票交易最小单位为100股")
        
        if abs(amount) % 100 != 0:
            raise ValidationException("股票交易数量必须为100股的整数倍")
        
        if price is not None and price <= 0:
            raise ValidationException("订单价格必须大于零")
        
        if order_type not in [OrderType.MARKET, OrderType.LIMIT]:
            raise ValidationException(f"不支持的订单类型: {order_type}")
    
    def _check_order_risk(self, security, amount, price):
        """检查订单风险"""
        if amount > 0:  # 买单风险检查
            required_cash = amount * price * 1.001  # 包含手续费
            if required_cash > self._available_cash:
                raise EmuTraderException(
                    f"可用资金不足: 需要{required_cash:.2f}，可用{self._available_cash:.2f}"
                )
                
            # 检查单只股票最大持仓比例
            account_state = self.get_account_state()
            position_value = required_cash
            if security in self._positions:
                position_value += self._positions[security].value
                
            if position_value / account_state.total_value > 0.3:  # 单只股票不超过30%
                raise EmuTraderException("单只股票持仓不能超过总资产的30%")
                
        else:  # 卖单风险检查
            required_shares = abs(amount)
            position = self._positions.get(security)
            if not position or position.closeable_amount < required_shares:
                available_shares = position.closeable_amount if position else 0
                raise EmuTraderException(
                    f"可卖持仓不足: 需要{required_shares}股，可用{available_shares}股"
                )
    
    def _freeze_cash(self, amount):
        """冻结资金"""
        if amount > self._available_cash:
            raise EmuTraderException(f"可用资金不足，无法冻结{amount:.2f}元")
        
        self._available_cash -= amount
        self._frozen_cash += amount
    
    def _unfreeze_cash(self, amount):
        """解冻资金"""
        unfrozen = min(amount, self._frozen_cash)
        self._frozen_cash -= unfrozen
        self._available_cash += unfrozen
        return unfrozen
    
    def _freeze_position(self, security, shares):
        """冻结持仓"""
        position = self._positions.get(security)
        if not position or position.closeable_amount < shares:
            raise EmuTraderException(f"可卖持仓不足: {security}")
        
        # 减少可卖数量（简化实现，实际应该有专门的冻结字段）
        position.closeable_amount -= shares
    
    def _process_order(self, order):
        """
        处理订单（模拟成交）
        
        Args:
            order (Order): 订单对象
        """
        try:
            # 模拟订单成交
            order.status = OrderStatus.FILLED
            order.filled = order.amount
            
            # 创建交易记录
            transaction = Transaction(
                order_id=order.order_id,
                security=order.security,
                amount=order.amount,
                price=order.price,
                order_type="buy" if order.amount > 0 else "sell",
                commission=self._calculate_commission(order),
                tax=self._calculate_tax(order),
                filled_at=datetime.now()
            )
            
            self._transactions.append(transaction)
            
            # 保存订单到存储
            self._storage.save_order(self.strategy_name, self.account_id, order)
            
            # 保存交易记录到存储
            self._storage.save_transaction(self.strategy_name, self.account_id, transaction)
            
            # 更新持仓和资金
            if order.amount > 0:  # 买入
                self._update_position_buy(order, transaction)
            else:  # 卖出
                self._update_position_sell(order, transaction)
            
            # 保存持仓到存储
            self._storage.save_positions(self.strategy_name, self.account_id, self._positions)
            
            # 保存账户状态
            self._save_account_state()
                
        except Exception as e:
            # 订单失败，恢复冻结的资金/持仓
            order.status = OrderStatus.REJECTED
            self._handle_order_failure(order)
            raise EmuTraderException(f"订单处理失败: {str(e)}")
    
    def _calculate_commission(self, order):
        """计算佣金"""
        # 简化的佣金计算：万分之三，最低5元
        commission = abs(order.amount) * order.price * 0.0003
        return max(commission, 5.0)
    
    def _calculate_tax(self, order):
        """计算印花税"""
        # 股票印花税：卖出时收取千分之一
        if order.amount < 0:  # 卖出
            return abs(order.amount) * order.price * 0.001
        return 0.0
    
    def _update_position_buy(self, order, transaction):
        """更新买入后的持仓"""
        security = order.security
        shares = order.amount
        cost_price = order.price
        
        if security in self._positions:
            # 已有持仓，计算新的平均成本
            position = self._positions[security]
            total_cost = position.total_amount * position.avg_cost + shares * cost_price
            total_shares = position.total_amount + shares
            new_avg_cost = total_cost / total_shares
            
            position.total_amount = total_shares
            position.closeable_amount = total_shares  # 简化：T+0交易
            position.avg_cost = new_avg_cost
            position.transact_time = datetime.now()
        else:
            # 新建持仓
            position = Position(
                security=security,
                total_amount=shares,
                avg_cost=cost_price,
                current_price=cost_price,
                closeable_amount=shares,  # 简化：T+0交易
                init_time=datetime.now(),
                transact_time=datetime.now()
            )
            self._positions[security] = position
        
        # 解冻资金，扣除实际成本
        total_cost = shares * cost_price + transaction.commission + transaction.tax
        self._unfreeze_cash(shares * cost_price * 1.001)  # 解冻之前冻结的金额
        # 扣除实际成本
        self._available_cash -= total_cost
    
    def _update_position_sell(self, order, transaction):
        """更新卖出后的持仓"""
        security = order.security
        shares = abs(order.amount)
        
        if security in self._positions:
            position = self._positions[security]
            position.total_amount -= shares
            position.transact_time = datetime.now()
            
            # 增加可用资金
            net_proceeds = shares * order.price - transaction.commission - transaction.tax
            self._available_cash += net_proceeds
            
            # 如果持仓清零，从字典中移除
            if position.total_amount == 0:
                del self._positions[security]
    
    def _handle_order_failure(self, order):
        """处理订单失败，恢复冻结资源"""
        if order.amount > 0:  # 买单失败，解冻资金
            frozen_amount = order.amount * order.price * 1.001
            self._unfreeze_cash(frozen_amount)
        else:  # 卖单失败，恢复持仓
            shares = abs(order.amount)
            position = self._positions.get(order.security)
            if position:
                position.closeable_amount += shares
    
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
                return False  # 已完成的订单无法取消
            
            # 取消订单
            order.status = OrderStatus.CANCELLED
            
            # 恢复冻结资源
            self._handle_order_failure(order)
            
            # 更新订单状态到存储
            self._storage.save_order(self.strategy_name, self.account_id, order)
            
            # 保存账户状态
            self._save_account_state()
            
            return True
    
    def get_orders(self):
        """获取所有订单"""
        with self._lock:
            return self._orders.copy()
    
    def get_order(self, order_id):
        """获取指定订单"""
        return self._orders.get(order_id)
    
    def get_transactions(self):
        """获取所有交易记录"""
        with self._lock:
            return self._transactions.copy()
    
    def get_performance_summary(self):
        """获取账户性能摘要"""
        account_state = self.get_account_state()
        total_return = (account_state.total_value - self.initial_cash) / self.initial_cash
        
        return {
            "initial_cash": self.initial_cash,
            "current_value": account_state.total_value,
            "total_return": total_return,
            "positions_count": len([p for p in self._positions.values() if p.total_amount > 0]),
            "orders_count": len(self._orders),
            "transactions_count": len(self._transactions)
        }
    
    def __repr__(self):
        return f"StockAccountHandler({self.strategy_name}, value={self.get_account_state().total_value:.2f})"