"""
Unit tests for StockAccountHandler.
"""

import pytest
import time
import threading
from datetime import datetime
from emutrader.handlers.stock import StockAccountHandler
from emutrader.constants import OrderStatus, AccountTypes
from emutrader.exceptions import EmuTraderException, ValidationException


class TestStockAccountHandler:
    """Test StockAccountHandler functionality."""
    
    @pytest.mark.handlers
    def test_handler_initialization(self, stock_handler):
        """Test handler initialization."""
        assert stock_handler.strategy_name == "test_strategy"
        assert stock_handler.account_id == 1
        assert stock_handler.initial_cash == 100000
        assert hasattr(stock_handler, '_storage')
        assert hasattr(stock_handler, '_data_provider')
        assert hasattr(stock_handler, '_lock')
    
    @pytest.mark.handlers
    def test_get_account_type(self, stock_handler):
        """Test getting account type."""
        account_type = stock_handler._get_account_type()
        assert account_type == AccountTypes.STOCK
    
    @pytest.mark.handlers
    def test_initial_account_state(self, stock_handler, assert_account_state_valid):
        """Test initial account state."""
        account_state = stock_handler.get_account_state()
        
        assert_account_state_valid(account_state)
        assert account_state.total_value == 100000.0
        assert account_state.available_cash == 100000.0
        assert account_state.positions_value == 0.0
        assert account_state.frozen_cash == 0.0
    
    @pytest.mark.handlers
    def test_initial_positions_empty(self, stock_handler):
        """Test initial positions are empty."""
        positions = stock_handler.get_positions()
        assert isinstance(positions, dict)
        assert len(positions) == 0
    
    @pytest.mark.handlers
    def test_initial_orders_empty(self, stock_handler):
        """Test initial orders are empty."""
        orders = stock_handler.get_orders()
        assert isinstance(orders, dict)
        assert len(orders) == 0
    
    @pytest.mark.handlers
    def test_initial_transactions_empty(self, stock_handler):
        """Test initial transactions are empty."""
        transactions = stock_handler.get_transactions()
        assert isinstance(transactions, list)
        assert len(transactions) == 0


class TestStockTrading:
    """Test stock trading functionality."""
    
    @pytest.mark.handlers
    def test_send_buy_order(self, stock_handler, assert_account_state_valid):
        """Test sending buy order."""
        security = "000001.XSHE"
        amount = 1000
        price = 10.0
        
        # 发送买单
        order_id = stock_handler.send_order(security, amount, price)
        
        assert isinstance(order_id, str)
        assert order_id.startswith("STK_")
        
        # 检查订单状态
        order = stock_handler.get_order(order_id)
        assert order is not None
        assert order.security == security
        assert order.amount == amount
        assert order.price == price
        assert order.status == OrderStatus.FILLED
        
        # 检查账户状态变化
        account_state = stock_handler.get_account_state()
        assert_account_state_valid(account_state)
        assert account_state.available_cash < 100000.0  # 现金减少
        assert account_state.positions_value > 0.0       # 有持仓
        
        # 检查持仓
        positions = stock_handler.get_positions()
        assert security in positions
        position = positions[security]
        assert position.total_amount == amount
        assert position.avg_cost == price
        
        # 检查交易记录
        transactions = stock_handler.get_transactions()
        assert len(transactions) == 1
    
    @pytest.mark.handlers
    def test_send_sell_order(self, stock_handler):
        """Test sending sell order."""
        security = "000001.XSHE"
        buy_amount = 1000
        sell_amount = -500
        price = 10.0
        
        # 先买入建立持仓
        stock_handler.send_order(security, buy_amount, price)
        
        # 记录卖出前状态
        account_state_before = stock_handler.get_account_state()
        position_before = stock_handler.get_position(security)
        
        # 卖出部分持仓
        sell_order_id = stock_handler.send_order(security, sell_amount, price)
        
        # 检查卖出订单
        sell_order = stock_handler.get_order(sell_order_id)
        assert sell_order.amount == sell_amount
        assert sell_order.status == OrderStatus.FILLED
        
        # 检查持仓变化
        position_after = stock_handler.get_position(security)
        assert position_after.total_amount == buy_amount + sell_amount  # 1000 + (-500) = 500
        
        # 检查现金增加
        account_state_after = stock_handler.get_account_state()
        assert account_state_after.available_cash > account_state_before.available_cash
    
    @pytest.mark.handlers
    def test_send_market_order(self, stock_handler):
        """Test sending market order."""
        security = "000001.XSHE"
        amount = 1000
        
        # 发送市价单（price=None）
        order_id = stock_handler.send_order(security, amount, None, "market")
        
        order = stock_handler.get_order(order_id)
        assert order is not None
        assert order.price > 0  # 应该有成交价格
        assert order.status == OrderStatus.FILLED
    
    @pytest.mark.handlers
    def test_multiple_orders(self, stock_handler):
        """Test sending multiple orders."""
        orders_data = [
            ("000001.XSHE", 1000, 10.0),
            ("000002.XSHE", 500, 15.0),
            ("600000.XSHG", 2000, 8.0)
        ]
        
        order_ids = []
        for security, amount, price in orders_data:
            order_id = stock_handler.send_order(security, amount, price)
            order_ids.append(order_id)
        
        # 检查所有订单都已成交
        for order_id in order_ids:
            order = stock_handler.get_order(order_id)
            assert order.status == OrderStatus.FILLED
        
        # 检查持仓数量
        positions = stock_handler.get_positions()
        assert len(positions) == 3
        
        # 检查总持仓价值
        account_state = stock_handler.get_account_state()
        expected_positions_value = 1000*10.0 + 500*15.0 + 2000*8.0  # 基础计算
        # 实际值可能因为价格更新而略有不同
        assert account_state.positions_value > expected_positions_value * 0.9
    
    @pytest.mark.handlers
    def test_position_averaging(self, stock_handler):
        """Test position cost averaging."""
        security = "000001.XSHE"
        
        # 第一次买入
        stock_handler.send_order(security, 1000, 10.0)
        position1 = stock_handler.get_position(security)
        assert position1.avg_cost == 10.0
        
        # 第二次买入不同价格
        stock_handler.send_order(security, 1000, 12.0)
        position2 = stock_handler.get_position(security)
        
        # 平均成本应该是 (1000*10 + 1000*12) / 2000 = 11.0
        assert position2.total_amount == 2000
        assert abs(position2.avg_cost - 11.0) < 0.01


class TestStockTradingValidation:
    """Test trading validation and error handling."""
    
    @pytest.mark.handlers
    def test_invalid_security_code(self, stock_handler):
        """Test validation for invalid security codes."""
        invalid_codes = ["", "123", "000001", "INVALID", "000001.INVALID"]
        
        for code in invalid_codes:
            with pytest.raises(ValidationException, match="无效的证券代码"):
                stock_handler.send_order(code, 1000, 10.0)
    
    @pytest.mark.handlers
    def test_invalid_order_amount(self, stock_handler):
        """Test validation for invalid order amounts."""
        security = "000001.XSHE"
        
        # 零数量
        with pytest.raises(ValidationException, match="订单数量不能为零"):
            stock_handler.send_order(security, 0, 10.0)
        
        # 小于100股
        with pytest.raises(ValidationException, match="股票交易最小单位为100股"):
            stock_handler.send_order(security, 50, 10.0)
        
        # 非100整数倍
        with pytest.raises(ValidationException, match="股票交易数量必须为100股的整数倍"):
            stock_handler.send_order(security, 150, 10.0)
    
    @pytest.mark.handlers
    def test_invalid_order_price(self, stock_handler):
        """Test validation for invalid order prices."""
        security = "000001.XSHE"
        amount = 1000
        
        # 负价格
        with pytest.raises(ValidationException, match="订单价格必须大于零"):
            stock_handler.send_order(security, amount, -10.0)
        
        # 零价格
        with pytest.raises(ValidationException, match="订单价格必须大于零"):
            stock_handler.send_order(security, amount, 0.0)
    
    @pytest.mark.handlers
    def test_insufficient_cash(self, stock_handler):
        """Test insufficient cash validation."""
        security = "000001.XSHE"
        amount = 100000  # 需要1,000,000元，超过初始资金
        price = 10.0
        
        with pytest.raises(EmuTraderException, match="可用资金不足"):
            stock_handler.send_order(security, amount, price)
    
    @pytest.mark.handlers
    def test_insufficient_position_for_sell(self, stock_handler):
        """Test insufficient position for sell order."""
        security = "000001.XSHE"
        
        # 没有持仓就卖出
        with pytest.raises(EmuTraderException, match="可卖持仓不足"):
            stock_handler.send_order(security, -1000, 10.0)
        
        # 买入1000股
        stock_handler.send_order(security, 1000, 10.0)
        
        # 尝试卖出超过持仓数量
        with pytest.raises(EmuTraderException, match="可卖持仓不足"):
            stock_handler.send_order(security, -1500, 10.0)
    
    @pytest.mark.handlers
    def test_single_stock_position_limit(self, stock_handler):
        """Test single stock position limit."""
        security = "000001.XSHE"
        # 尝试购买超过30%总资产的单只股票
        amount = 5000  # 需要50,000元，超过30%限制
        price = 10.0
        
        with pytest.raises(EmuTraderException, match="单只股票持仓不能超过总资产的30%"):
            stock_handler.send_order(security, amount, price)


class TestOrderManagement:
    """Test order management functionality."""
    
    @pytest.mark.handlers
    def test_get_orders(self, stock_handler):
        """Test getting orders."""
        # 发送几个订单
        order_ids = []
        for i in range(3):
            order_id = stock_handler.send_order(f"00000{i+1}.XSHE", 1000, 10.0)
            order_ids.append(order_id)
        
        # 获取所有订单
        orders = stock_handler.get_orders()
        assert len(orders) >= 3
        
        # 检查订单ID都在其中
        order_id_set = set(orders.keys())
        for order_id in order_ids:
            assert order_id in order_id_set
    
    @pytest.mark.handlers
    def test_get_specific_order(self, stock_handler):
        """Test getting specific order."""
        security = "000001.XSHE"
        amount = 1000
        price = 10.0
        
        order_id = stock_handler.send_order(security, amount, price)
        order = stock_handler.get_order(order_id)
        
        assert order is not None
        assert order.order_id == order_id
        assert order.security == security
        assert order.amount == amount
        assert order.price == price
    
    @pytest.mark.handlers
    def test_get_nonexistent_order(self, stock_handler):
        """Test getting non-existent order."""
        order = stock_handler.get_order("NONEXISTENT_ORDER_ID")
        assert order is None
    
    @pytest.mark.handlers
    def test_cancel_order(self, stock_handler):
        """Test cancelling order."""
        # 注意：由于订单立即成交，这个测试主要验证cancel_order方法不会崩溃
        security = "000001.XSHE"
        order_id = stock_handler.send_order(security, 1000, 10.0)
        
        # 尝试取消（可能失败，因为订单可能已成交）
        result = stock_handler.cancel_order(order_id)
        assert isinstance(result, bool)
        
        # 取消不存在的订单
        result = stock_handler.cancel_order("NONEXISTENT")
        assert result is False


class TestPerformanceTracking:
    """Test performance tracking functionality."""
    
    @pytest.mark.handlers
    def test_performance_summary(self, stock_handler):
        """Test performance summary calculation."""
        # 执行一些交易
        stock_handler.send_order("000001.XSHE", 1000, 10.0)
        stock_handler.send_order("000002.XSHE", 500, 15.0)
        
        summary = stock_handler.get_performance_summary()
        
        assert isinstance(summary, dict)
        assert 'initial_cash' in summary
        assert 'current_value' in summary
        assert 'total_return' in summary
        assert 'positions_count' in summary
        assert 'orders_count' in summary
        assert 'transactions_count' in summary
        
        assert summary['initial_cash'] == 100000.0
        assert summary['positions_count'] >= 2
        assert summary['orders_count'] >= 2
        assert summary['transactions_count'] >= 2
        
        # 总收益率应该在合理范围内
        assert -1.0 < summary['total_return'] < 1.0
    
    @pytest.mark.handlers
    def test_account_state_consistency(self, stock_handler, assert_account_state_valid):
        """Test account state consistency after multiple operations."""
        # 执行多种操作
        operations = [
            ("000001.XSHE", 1000, 10.0),   # 买入
            ("000002.XSHE", 500, 15.0),    # 买入
            ("000001.XSHE", -500, 10.5),   # 卖出部分
            ("600000.XSHG", 1000, 8.0),    # 买入新股票
        ]
        
        for security, amount, price in operations:
            stock_handler.send_order(security, amount, price)
        
        # 验证最终状态一致性
        account_state = stock_handler.get_account_state()
        assert_account_state_valid(account_state)


@pytest.mark.integration
class TestStockHandlerIntegration:
    """Integration tests for StockAccountHandler."""
    
    def test_persistence_across_sessions(self, clean_temp_db):
        """Test data persistence across handler sessions."""
        strategy_name = "test_strategy"
        account_id = 1
        initial_cash = 100000
        
        # 第一个会话：创建账户并交易
        handler1 = StockAccountHandler(
            strategy_name=strategy_name,
            account_id=account_id,
            initial_cash=initial_cash,
            db_path=clean_temp_db
        )
        
        # 执行交易
        order_id = handler1.send_order("000001.XSHE", 1000, 10.0)
        account_state1 = handler1.get_account_state()
        positions1 = handler1.get_positions()
        
        # 验证交易成功
        assert len(positions1) == 1
        assert account_state1.positions_value > 0
        
        # 第二个会话：重新加载相同账户
        handler2 = StockAccountHandler(
            strategy_name=strategy_name,
            account_id=account_id,
            initial_cash=initial_cash,
            db_path=clean_temp_db
        )
        
        # 验证数据已恢复
        account_state2 = handler2.get_account_state()
        positions2 = handler2.get_positions()
        
        assert len(positions2) == 1
        assert "000001.XSHE" in positions2
        assert abs(account_state2.available_cash - account_state1.available_cash) < 1.0
        assert abs(account_state2.positions_value - account_state1.positions_value) < 100.0
    
    def test_multiple_accounts_isolation(self, clean_temp_db):
        """Test isolation between multiple accounts."""
        # 创建两个不同的账户
        handler1 = StockAccountHandler("strategy1", 1, 100000, clean_temp_db)
        handler2 = StockAccountHandler("strategy2", 2, 200000, clean_temp_db)
        
        # 在不同账户执行不同操作
        handler1.send_order("000001.XSHE", 1000, 10.0)
        handler2.send_order("000002.XSHE", 1000, 15.0)
        
        # 验证账户隔离
        positions1 = handler1.get_positions()
        positions2 = handler2.get_positions()
        
        assert "000001.XSHE" in positions1
        assert "000001.XSHE" not in positions2
        assert "000002.XSHE" in positions2
        assert "000002.XSHE" not in positions1
        
        # 验证账户状态独立
        state1 = handler1.get_account_state()
        state2 = handler2.get_account_state()
        
        assert abs(state1.total_value - 100000) < abs(state2.total_value - 200000)


@pytest.mark.performance
class TestStockHandlerPerformance:
    """Performance tests for StockAccountHandler."""
    
    def test_order_processing_speed(self, stock_handler):
        """Test order processing speed."""
        securities = [f"00000{i}.XSHE" for i in range(1, 11)]
        
        start_time = time.time()
        
        # 发送10个订单
        for i, security in enumerate(securities):
            stock_handler.send_order(security, 100, 10.0 + i)
        
        end_time = time.time()
        
        # 平均每个订单应在100ms内处理完成
        avg_time_ms = (end_time - start_time) * 1000 / len(securities)
        assert avg_time_ms < 100
    
    def test_account_state_query_speed(self, stock_handler):
        """Test account state query performance."""
        # 先创建一些数据
        for i in range(5):
            stock_handler.send_order(f"00000{i+1}.XSHE", 100, 10.0)
        
        # 测试查询速度
        start_time = time.time()
        
        for _ in range(100):
            stock_handler.get_account_state()
        
        end_time = time.time()
        
        # 平均查询时间应小于10ms
        avg_time_ms = (end_time - start_time) * 1000 / 100
        assert avg_time_ms < 10
    
    def test_concurrent_access(self, stock_handler):
        """Test concurrent access to handler."""
        results = []
        errors = []
        
        def worker(worker_id):
            try:
                for i in range(5):
                    security = f"00000{worker_id}.XSHE"
                    stock_handler.send_order(security, 100, 10.0)
                    stock_handler.get_account_state()
                    results.append(f"worker_{worker_id}_success")
            except Exception as e:
                errors.append(f"worker_{worker_id}_error: {str(e)}")
        
        # 启动多个线程
        threads = []
        for i in range(3):
            thread = threading.Thread(target=worker, args=(i+1,))
            threads.append(thread)
            thread.start()
        
        # 等待完成
        for thread in threads:
            thread.join()
        
        # 验证大部分操作成功
        assert len(results) >= 12  # 3个线程 × 5次操作 = 15，允许少数失败
        assert len(errors) < len(results) * 0.2  # 错误率应小于20%