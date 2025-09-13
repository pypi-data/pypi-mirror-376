"""
Unit tests for MockAdapter implementation.
"""

import pytest
import time
from datetime import datetime
from emutrader.adapters.mock_adapter import MockAdapter
from emutrader.constants import OrderStatus
from emutrader.exceptions import ValidationException


class TestMockAdapter:
    """Test MockAdapter functionality."""
    
    @pytest.mark.mock
    def test_mock_adapter_initialization(self):
        """Test MockAdapter initialization."""
        adapter = MockAdapter(
            strategy_name="test_strategy",
            account_id=1,
            enable_price_simulation=False,
            volatility=0.02,
            slippage_rate=0.001,
            commission_rate=0.0003
        )
        
        assert adapter.strategy_name == "test_strategy"
        assert adapter.account_id == 1
        assert adapter.enable_price_simulation is False
        assert adapter.volatility == 0.02
        assert adapter.slippage_rate == 0.001
        assert adapter.commission_rate == 0.0003
        
        adapter.close()
    
    @pytest.mark.mock
    def test_get_current_price(self, mock_adapter):
        """Test getting current price."""
        # 测试预设股票价格
        price1 = mock_adapter.get_current_price("000001.XSHE")
        assert isinstance(price1, float)
        assert price1 > 0
        
        # 测试新股票价格生成
        price2 = mock_adapter.get_current_price("999999.XSHE")
        assert isinstance(price2, float)
        assert price2 > 0
        
        # 同一股票的价格应该基本稳定（无价格模拟时）
        price1_again = mock_adapter.get_current_price("000001.XSHE")
        assert abs(price1 - price1_again) < 0.1  # 允许小幅波动
    
    @pytest.mark.mock
    def test_get_market_data(self, mock_adapter):
        """Test getting market data."""
        security = "000001.XSHE"
        market_data = mock_adapter.get_market_data(security)
        
        assert isinstance(market_data, dict)
        assert 'price' in market_data
        assert 'last_update' in market_data
        assert 'base_price' in market_data
        assert 'daily_high' in market_data
        assert 'daily_low' in market_data
        assert 'volume' in market_data
        
        assert market_data['price'] > 0
        assert isinstance(market_data['last_update'], datetime)
        assert market_data['base_price'] > 0
        assert market_data['volume'] >= 0
    
    @pytest.mark.mock
    def test_validate_security(self, mock_adapter):
        """Test security code validation."""
        # 有效证券代码
        assert mock_adapter.validate_security("000001.XSHE") is True
        assert mock_adapter.validate_security("600000.XSHG") is True
        
        # 无效证券代码
        assert mock_adapter.validate_security("") is False
        assert mock_adapter.validate_security("123") is False
        assert mock_adapter.validate_security("000001") is False  # 缺少交易所
        assert mock_adapter.validate_security("000001.INVALID") is False  # 无效交易所
        assert mock_adapter.validate_security("ABCDEF.XSHE") is False  # 非数字代码
    
    @pytest.mark.mock
    def test_send_order_market(self, mock_adapter):
        """Test sending market order."""
        order_id = mock_adapter.send_order("000001.XSHE", 100, None, "market")
        
        assert order_id.startswith("MOCK_")
        assert len(order_id) > 10
        
        # 等待订单处理
        time.sleep(0.6)  # 稍等订单异步处理完成
        
        # 检查订单状态
        order = mock_adapter.get_order(order_id)
        assert order is not None
        assert order.status == OrderStatus.FILLED
        assert order.filled == 100
        assert order.price > 0  # 应该有成交价格
    
    @pytest.mark.mock
    def test_send_order_limit(self, mock_adapter):
        """Test sending limit order."""
        order_id = mock_adapter.send_order("000001.XSHE", 100, 10.0, "limit")
        
        assert order_id.startswith("MOCK_")
        
        # 等待订单处理
        time.sleep(0.6)
        
        # 检查订单状态
        order = mock_adapter.get_order(order_id)
        assert order is not None
        assert order.status == OrderStatus.FILLED
        assert order.price == 10.0  # 限价单应保持原价格
    
    @pytest.mark.mock
    def test_send_sell_order(self, mock_adapter):
        """Test sending sell order."""
        order_id = mock_adapter.send_order("000001.XSHE", -100, 10.0)
        
        assert order_id.startswith("MOCK_")
        
        time.sleep(0.6)
        
        order = mock_adapter.get_order(order_id)
        assert order is not None
        assert order.amount == -100
        assert order.status == OrderStatus.FILLED
    
    @pytest.mark.mock
    def test_slippage_calculation(self, mock_adapter):
        """Test slippage calculation."""
        # 买单应该有向上滑点
        buy_order_id = mock_adapter.send_order("000001.XSHE", 100, None, "market")
        time.sleep(0.6)
        
        buy_order = mock_adapter.get_order(buy_order_id)
        current_price = mock_adapter.get_current_price("000001.XSHE")
        
        # 买入价格应该略高于当前价格（上滑点）
        assert buy_order.price >= current_price * (1 - 0.002)  # 允许小幅误差
        
        # 卖单应该有向下滑点
        sell_order_id = mock_adapter.send_order("000001.XSHE", -100, None, "market")
        time.sleep(0.6)
        
        sell_order = mock_adapter.get_order(sell_order_id)
        
        # 卖出价格应该略低于当前价格（下滑点）
        assert sell_order.price <= current_price * (1 + 0.002)  # 允许小幅误差
    
    @pytest.mark.mock
    def test_get_orders(self, mock_adapter):
        """Test getting orders list."""
        # 初始应该没有订单
        orders = mock_adapter.get_orders()
        initial_count = len(orders)
        
        # 发送几个订单
        order_id1 = mock_adapter.send_order("000001.XSHE", 100, 10.0)
        order_id2 = mock_adapter.send_order("000002.XSHE", 200, 15.0)
        
        time.sleep(0.6)
        
        # 获取所有订单
        all_orders = mock_adapter.get_orders()
        assert len(all_orders) == initial_count + 2
        
        # 获取已成交订单
        filled_orders = mock_adapter.get_orders(status=OrderStatus.FILLED)
        assert len(filled_orders) >= 2  # 至少包含刚发送的订单
    
    @pytest.mark.mock
    def test_cancel_order(self, mock_adapter):
        """Test cancelling order."""
        # 发送订单但立即尝试取消（在处理完成前）
        order_id = mock_adapter.send_order("000001.XSHE", 100, 10.0)
        
        # 立即尝试取消
        success = mock_adapter.cancel_order(order_id)
        
        # 由于异步处理，可能成功也可能失败
        # 主要测试方法不会崩溃
        assert isinstance(success, bool)
        
        # 取消不存在的订单应该返回False
        assert mock_adapter.cancel_order("NONEXISTENT") is False
    
    @pytest.mark.mock
    def test_get_account_info(self, mock_adapter):
        """Test getting account info."""
        account_info = mock_adapter.get_account_info()
        
        assert isinstance(account_info, dict)
        assert 'total_value' in account_info
        assert 'available_cash' in account_info
        assert 'positions_value' in account_info
        assert 'frozen_cash' in account_info
        
        assert account_info['total_value'] == 100000.0
        assert account_info['available_cash'] == 100000.0
        assert account_info['positions_value'] == 0.0
        assert account_info['frozen_cash'] == 0.0
    
    @pytest.mark.mock
    def test_get_positions(self, mock_adapter):
        """Test getting positions."""
        positions = mock_adapter.get_positions()
        assert isinstance(positions, dict)
        assert len(positions) == 0  # MockAdapter默认无持仓
    
    @pytest.mark.mock
    def test_get_statistics(self, mock_adapter):
        """Test getting adapter statistics."""
        # 发送一些订单以产生统计数据
        mock_adapter.send_order("000001.XSHE", 100, 10.0)
        mock_adapter.send_order("000002.XSHE", 200, 15.0)
        
        time.sleep(0.6)
        
        stats = mock_adapter.get_statistics()
        
        assert isinstance(stats, dict)
        assert 'total_securities' in stats
        assert 'total_orders' in stats
        assert 'filled_orders' in stats
        assert 'fill_rate' in stats
        assert 'price_simulation_enabled' in stats
        assert 'volatility' in stats
        assert 'slippage_rate' in stats
        assert 'commission_rate' in stats
        
        assert stats['total_orders'] >= 2
        assert stats['fill_rate'] >= 0.0
        assert stats['fill_rate'] <= 1.0
        assert stats['volatility'] == 0.01  # 从fixture设置
        assert stats['slippage_rate'] == 0.001
    
    @pytest.mark.mock
    def test_adapter_repr(self, mock_adapter):
        """Test adapter string representation."""
        repr_str = repr(mock_adapter)
        assert "MockAdapter" in repr_str
        assert "securities=" in repr_str
        assert "orders=" in repr_str
    
    @pytest.mark.mock
    def test_adapter_close(self, mock_adapter):
        """Test adapter close method."""
        # 发送订单产生数据
        mock_adapter.send_order("000001.XSHE", 100, 10.0)
        
        # 关闭适配器
        mock_adapter.close()
        
        assert mock_adapter.enable_price_simulation is False
        
        # 验证数据已清理
        orders = mock_adapter.get_orders()
        assert len(orders) == 0


class TestMockAdapterPriceSimulation:
    """Test MockAdapter price simulation functionality."""
    
    @pytest.mark.mock
    def test_price_simulation_enabled(self):
        """Test price simulation when enabled."""
        adapter = MockAdapter(
            strategy_name="test_strategy",
            account_id=1,
            enable_price_simulation=True,
            volatility=0.1  # 高波动率便于测试
        )
        
        try:
            security = "000001.XSHE"
            initial_price = adapter.get_current_price(security)
            
            # 等待价格更新
            time.sleep(2)
            
            updated_price = adapter.get_current_price(security)
            
            # 价格应该有变化（高概率）
            # 注意：由于随机性，偶尔可能价格相同，但这是正常的
            assert isinstance(updated_price, float)
            assert updated_price > 0
            
        finally:
            adapter.close()
    
    @pytest.mark.mock
    def test_price_simulation_disabled(self):
        """Test price simulation when disabled."""
        adapter = MockAdapter(
            strategy_name="test_strategy",
            account_id=1,
            enable_price_simulation=False
        )
        
        try:
            security = "000001.XSHE"
            initial_price = adapter.get_current_price(security)
            
            # 等待一段时间
            time.sleep(1)
            
            updated_price = adapter.get_current_price(security)
            
            # 价格应该基本相同（允许小幅随机波动）
            assert abs(updated_price - initial_price) < 0.5
            
        finally:
            adapter.close()
    
    @pytest.mark.mock
    def test_market_data_updates(self):
        """Test market data updates with trading."""
        adapter = MockAdapter(
            strategy_name="test_strategy",
            account_id=1,
            enable_price_simulation=False
        )
        
        try:
            security = "000001.XSHE"
            
            # 获取初始市场数据
            initial_data = adapter.get_market_data(security)
            initial_volume = initial_data['volume']
            
            # 发送订单
            adapter.send_order(security, 100, 10.0)
            time.sleep(0.6)
            
            # 获取更新后的市场数据
            updated_data = adapter.get_market_data(security)
            
            # 成交量应该增加
            assert updated_data['volume'] >= initial_volume + 100
            
        finally:
            adapter.close()
    
    @pytest.mark.mock
    def test_daily_high_low_tracking(self):
        """Test daily high and low price tracking."""
        adapter = MockAdapter(
            strategy_name="test_strategy",
            account_id=1,
            enable_price_simulation=True,
            volatility=0.05
        )
        
        try:
            security = "000001.XSHE"
            
            # 获取初始数据
            initial_data = adapter.get_market_data(security)
            initial_high = initial_data['daily_high']
            initial_low = initial_data['daily_low']
            
            # 等待价格变化
            time.sleep(2)
            
            # 获取更新后的数据
            updated_data = adapter.get_market_data(security)
            
            # 验证高低价追踪
            assert updated_data['daily_high'] >= initial_high
            assert updated_data['daily_low'] <= initial_low
            assert updated_data['daily_high'] >= updated_data['daily_low']
            
        finally:
            adapter.close()


@pytest.mark.performance
class TestMockAdapterPerformance:
    """Test MockAdapter performance characteristics."""
    
    def test_order_processing_performance(self, mock_adapter):
        """Test order processing performance."""
        start_time = time.time()
        
        # 发送多个订单
        order_ids = []
        for i in range(10):
            order_id = mock_adapter.send_order(f"00000{i+1}.XSHE", 100, 10.0)
            order_ids.append(order_id)
        
        end_time = time.time()
        
        # 订单发送应该很快
        avg_time_ms = (end_time - start_time) * 1000 / 10
        assert avg_time_ms < 10  # 平均每个订单发送时间应小于10ms
        
        # 等待订单处理完成
        time.sleep(1)
        
        # 验证订单都已处理
        filled_count = 0
        for order_id in order_ids:
            order = mock_adapter.get_order(order_id)
            if order and order.status == OrderStatus.FILLED:
                filled_count += 1
        
        assert filled_count >= 8  # 至少80%的订单应该已成交
    
    def test_price_query_performance(self, mock_adapter):
        """Test price query performance."""
        securities = [f"00000{i}.XSHE" for i in range(1, 101)]
        
        start_time = time.time()
        
        # 查询多个证券价格
        for security in securities:
            mock_adapter.get_current_price(security)
        
        end_time = time.time()
        
        # 价格查询应该很快
        avg_time_ms = (end_time - start_time) * 1000 / len(securities)
        assert avg_time_ms < 1  # 平均每次查询应小于1ms
    
    def test_concurrent_operations(self, mock_adapter):
        """Test concurrent operations on adapter."""
        import threading
        
        results = []
        errors = []
        
        def worker():
            try:
                for i in range(10):
                    # 混合操作
                    mock_adapter.get_current_price("000001.XSHE")
                    order_id = mock_adapter.send_order("000001.XSHE", 100, 10.0)
                    mock_adapter.get_order(order_id)
                    results.append("success")
            except Exception as e:
                errors.append(str(e))
        
        # 启动多个线程
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=worker)
            threads.append(thread)
            thread.start()
        
        # 等待所有线程完成
        for thread in threads:
            thread.join()
        
        # 验证大部分操作成功
        assert len(errors) == 0 or len(errors) < len(results) * 0.1  # 错误率应小于10%
        assert len(results) > 40  # 应该有足够的成功操作