"""
Integration tests for EmuTrader system.
"""

import pytest
import time
from datetime import datetime
from emutrader.handlers.stock import StockAccountHandler
from emutrader.adapters.mock_adapter import MockAdapter
from emutrader.storage.sqlite import SQLiteStorage
from emutrader.storage.cache import AccountCacheManager
from emutrader.utils.data import DataProvider
from emutrader.core.account import Account
from emutrader.api import get_jq_account
from emutrader.constants import OrderStatus, AccountTypes


@pytest.mark.integration
class TestEndToEndTrading:
    """End-to-end trading integration tests."""
    
    def test_complete_trading_workflow(self, clean_temp_db):
        """Test complete trading workflow from account creation to analysis."""
        # 1. 创建账户
        handler = StockAccountHandler(
            strategy_name="integration_test",
            account_id=1,
            initial_cash=100000,
            db_path=clean_temp_db
        )
        
        # 2. 验证初始状态
        initial_state = handler.get_account_state()
        assert initial_state.total_value == 100000.0
        assert initial_state.available_cash == 100000.0
        assert initial_state.positions_value == 0.0
        
        # 3. 执行完整的交易流程
        trading_plan = [
            # 建仓
            ("000001.XSHE", 1000, 10.0),
            ("000002.XSHE", 500, 15.0),
            ("600000.XSHG", 1000, 8.0),
            
            # 调仓
            ("000001.XSHE", -500, 10.5),  # 减仓
            ("000003.XSHE", 1000, 12.0),  # 新增
            
            # 平仓
            ("000002.XSHE", -500, 15.2),  # 全部卖出
        ]
        
        order_ids = []
        for security, amount, price in trading_plan:
            order_id = handler.send_order(security, amount, price)
            order_ids.append(order_id)
            
            # 验证每笔交易都成功
            order = handler.get_order(order_id)
            assert order.status == OrderStatus.FILLED
        
        # 4. 验证最终状态
        final_state = handler.get_account_state()
        final_positions = handler.get_positions()
        
        # 应该有3个持仓
        expected_securities = {"000001.XSHE", "000003.XSHE", "600000.XSHG"}
        assert set(final_positions.keys()) == expected_securities
        
        # 验证持仓数量
        assert final_positions["000001.XSHE"].total_amount == 500  # 1000 - 500
        assert final_positions["000003.XSHE"].total_amount == 1000
        assert final_positions["600000.XSHG"].total_amount == 1000
        
        # 5. 验证性能统计
        performance = handler.get_performance_summary()
        assert performance['orders_count'] == 6
        assert performance['transactions_count'] == 6
        assert performance['positions_count'] == 3
        
        # 6. 验证交易记录完整性
        transactions = handler.get_transactions()
        assert len(transactions) == 6
        
        # 验证账户数据一致性
        calculated_positions_value = sum(pos.value for pos in final_positions.values())
        assert abs(final_state.positions_value - calculated_positions_value) < 50.0
    
    def test_account_persistence_and_recovery(self, clean_temp_db):
        """Test account data persistence and recovery."""
        strategy_name = "persistence_test"
        account_id = 1
        initial_cash = 100000
        
        # 第一阶段：创建账户并进行交易
        phase1_handler = StockAccountHandler(
            strategy_name=strategy_name,
            account_id=account_id,
            initial_cash=initial_cash,
            db_path=clean_temp_db
        )
        
        # 执行交易
        phase1_handler.send_order("000001.XSHE", 1000, 10.0)
        phase1_handler.send_order("000002.XSHE", 500, 15.0)
        
        # 记录状态
        phase1_state = phase1_handler.get_account_state()
        phase1_positions = phase1_handler.get_positions()
        phase1_performance = phase1_handler.get_performance_summary()
        
        # 第二阶段：重新创建处理器，验证数据恢复
        phase2_handler = StockAccountHandler(
            strategy_name=strategy_name,
            account_id=account_id,
            initial_cash=initial_cash,
            db_path=clean_temp_db
        )
        
        # 验证数据完全恢复
        phase2_state = phase2_handler.get_account_state()
        phase2_positions = phase2_handler.get_positions()
        
        assert len(phase2_positions) == len(phase1_positions)
        for security in phase1_positions:
            assert security in phase2_positions
            assert phase1_positions[security].total_amount == phase2_positions[security].total_amount
        
        # 验证账户状态基本一致（允许价格波动导致的小差异）
        assert abs(phase2_state.available_cash - phase1_state.available_cash) < 1.0
        assert abs(phase2_state.positions_value - phase1_state.positions_value) < 100.0
        
        # 第三阶段：继续交易，验证系统正常工作
        phase2_handler.send_order("600000.XSHG", 1000, 8.0)
        
        final_positions = phase2_handler.get_positions()
        assert len(final_positions) == 3
        assert "600000.XSHG" in final_positions
    
    def test_multi_account_system(self, clean_temp_db):
        """Test multi-account system isolation and management."""
        # 创建3个不同的账户
        accounts_config = [
            ("strategy_a", 1, 100000),
            ("strategy_b", 2, 200000),
            ("strategy_c", 3, 150000),
        ]
        
        handlers = []
        for strategy_name, account_id, initial_cash in accounts_config:
            handler = StockAccountHandler(
                strategy_name=strategy_name,
                account_id=account_id,
                initial_cash=initial_cash,
                db_path=clean_temp_db
            )
            handlers.append(handler)
        
        # 每个账户执行不同的交易策略
        trading_strategies = [
            # 策略A：大盘股
            [("000001.XSHE", 1000, 10.0), ("000002.XSHE", 500, 15.0)],
            # 策略B：中小盘股
            [("000003.XSHE", 1000, 12.0), ("000004.XSHE", 800, 18.0)],
            # 策略C：价值投资
            [("600000.XSHG", 2000, 8.0), ("600036.XSHG", 100, 30.0)],
        ]
        
        # 执行交易
        for handler, strategy in zip(handlers, trading_strategies):
            for security, amount, price in strategy:
                handler.send_order(security, amount, price)
        
        # 验证账户隔离
        positions_sets = []
        for handler in handlers:
            positions = handler.get_positions()
            positions_sets.append(set(positions.keys()))
        
        # 每个账户的持仓应该完全不同
        for i in range(len(positions_sets)):
            for j in range(i+1, len(positions_sets)):
                assert positions_sets[i].isdisjoint(positions_sets[j])
        
        # 验证账户状态独立
        for i, handler in enumerate(handlers):
            state = handler.get_account_state()
            expected_initial = accounts_config[i][2]
            
            # 每个账户的总资产应该接近其初始资金
            assert abs(state.total_value - expected_initial) < expected_initial * 0.5
    
    def test_high_frequency_trading_simulation(self, clean_temp_db):
        """Test high-frequency trading simulation."""
        handler = StockAccountHandler(
            strategy_name="hft_test",
            account_id=1,
            initial_cash=1000000,  # 更大资金支持高频交易
            db_path=clean_temp_db
        )
        
        # 模拟高频交易：快速买卖同一只股票
        security = "000001.XSHE"
        base_price = 10.0
        order_ids = []
        
        # 执行100笔小额交易
        for i in range(50):
            # 买入
            buy_price = base_price + (i % 10) * 0.01
            buy_order_id = handler.send_order(security, 100, buy_price)
            order_ids.append(buy_order_id)
            
            # 卖出
            sell_price = buy_price + 0.01
            sell_order_id = handler.send_order(security, -100, sell_price)
            order_ids.append(sell_order_id)
        
        # 验证所有订单都成功处理
        filled_count = 0
        for order_id in order_ids:
            order = handler.get_order(order_id)
            if order and order.status == OrderStatus.FILLED:
                filled_count += 1
        
        assert filled_count >= len(order_ids) * 0.95  # 95%以上成功率
        
        # 验证最终持仓为0（买卖平衡）
        final_position = handler.get_position(security)
        if final_position:
            assert final_position.total_amount == 0
        
        # 验证交易成本合理
        final_state = handler.get_account_state()
        trading_cost = 1000000 - final_state.total_value
        
        # 交易成本应该主要是手续费和税费
        expected_cost = len(order_ids) * 5  # 每笔至少5元手续费
        assert trading_cost >= expected_cost * 0.8
        assert trading_cost <= expected_cost * 2.0  # 不应超过预期的2倍


@pytest.mark.integration
class TestSystemComponentIntegration:
    """Test integration between system components."""
    
    def test_storage_cache_integration(self, clean_temp_db):
        """Test integration between storage and cache systems."""
        # 创建带缓存的处理器
        handler_with_cache = StockAccountHandler(
            strategy_name="cache_test",
            account_id=1,
            initial_cash=100000,
            db_path=clean_temp_db,
            enable_cache=True
        )
        
        # 创建不带缓存的处理器
        handler_no_cache = StockAccountHandler(
            strategy_name="no_cache_test",
            account_id=2,
            initial_cash=100000,
            db_path=clean_temp_db,
            enable_cache=False
        )
        
        # 在两个处理器上执行相同操作
        operations = [
            ("000001.XSHE", 1000, 10.0),
            ("000002.XSHE", 500, 15.0),
        ]
        
        for security, amount, price in operations:
            handler_with_cache.send_order(security, amount, price)
            handler_no_cache.send_order(security, amount, price)
        
        # 验证功能一致性
        state_cached = handler_with_cache.get_account_state()
        state_no_cache = handler_no_cache.get_account_state()
        
        # 账户状态结构应该相同
        assert abs(state_cached.available_cash - state_no_cache.available_cash) < 100.0
        assert abs(state_cached.positions_value - state_no_cache.positions_value) < 100.0
        
        # 持仓应该相同
        positions_cached = handler_with_cache.get_positions()
        positions_no_cache = handler_no_cache.get_positions()
        
        assert len(positions_cached) == len(positions_no_cache)
        for security in positions_cached:
            if security in positions_no_cache:  # 考虑价格可能略有不同
                cached_pos = positions_cached[security]
                no_cache_pos = positions_no_cache[security]
                assert cached_pos.total_amount == no_cache_pos.total_amount
    
    def test_mock_adapter_integration(self, clean_temp_db):
        """Test integration with MockAdapter."""
        handler = StockAccountHandler(
            strategy_name="mock_integration",
            account_id=1,
            initial_cash=100000,
            db_path=clean_temp_db
        )
        
        # 获取内部Mock适配器统计
        data_provider = handler._data_provider
        if hasattr(data_provider, 'adapter') and data_provider.adapter:
            adapter = data_provider.adapter
            initial_stats = adapter.get_statistics()
            
            # 执行交易
            handler.send_order("000001.XSHE", 1000, 10.0)
            handler.send_order("000002.XSHE", 500, 15.0)
            
            # 检查适配器统计变化
            final_stats = adapter.get_statistics()
            
            # 应该有更多的价格查询和市场数据更新
            assert final_stats['total_securities'] >= initial_stats['total_securities']
            
            # 验证价格获取工作正常
            for security in ["000001.XSHE", "000002.XSHE"]:
                price = data_provider.get_current_price(security)
                assert price > 0
                
                # 验证市场数据
                market_data = data_provider.get_price_info(security)
                assert 'price' in market_data
                assert market_data['source'] == 'mock'
    
    def test_api_integration(self, clean_temp_db):
        """Test integration with JoinQuant compatible API."""
        # 使用JQ兼容API创建账户
        account = get_jq_account(
            strategy_name="api_integration",
            initial_cash=100000,
            account_type="STOCK"
        )
        
        # 测试JQ兼容接口
        assert hasattr(account, 'account_info')
        assert hasattr(account, 'total_value')
        assert hasattr(account, 'available_cash')
        assert hasattr(account, 'positions_value')
        
        # 验证初始状态
        assert account.total_value == 100000.0
        assert account.available_cash == 100000.0
        assert account.positions_value == 0.0
        
        # 使用JQ风格下单
        order_id = account.order_shares("000001.XSHE", 1000)
        assert isinstance(order_id, str)
        
        # 验证下单后状态
        assert account.total_value <= 100000.0  # 考虑手续费
        assert account.available_cash < 100000.0
        assert account.positions_value > 0.0
        
        # 测试按金额下单
        order_id2 = account.order_value("000002.XSHE", 5000, 15.0)
        assert isinstance(order_id2, str)
        
        # 获取持仓
        positions = account.get_positions()
        assert len(positions) >= 1
        assert "000001.XSHE" in positions
        
        # 获取订单
        orders = account.get_orders()
        assert len(orders) >= 2
        
        # 获取交易记录
        transactions = account.get_transactions()
        assert len(transactions) >= 2


@pytest.mark.integration
@pytest.mark.performance
class TestSystemPerformance:
    """Test overall system performance."""
    
    def test_large_scale_trading_performance(self, clean_temp_db):
        """Test performance with large-scale trading."""
        handler = StockAccountHandler(
            strategy_name="large_scale_test",
            account_id=1,
            initial_cash=10000000,  # 1000万资金
            db_path=clean_temp_db
        )
        
        # 生成100只股票的交易列表
        securities = [f"{i:06d}.XSHE" for i in range(1, 101)]
        
        start_time = time.time()
        
        # 每只股票买入1000股
        order_ids = []
        for i, security in enumerate(securities):
            order_id = handler.send_order(security, 1000, 10.0 + i * 0.1)
            order_ids.append(order_id)
        
        end_time = time.time()
        
        # 验证处理时间
        total_time = end_time - start_time
        avg_time_per_order = total_time / len(securities)
        
        assert avg_time_per_order < 0.1  # 每笔订单平均处理时间应小于100ms
        assert total_time < 20.0  # 总处理时间应小于20秒
        
        # 验证所有订单都成功
        success_count = 0
        for order_id in order_ids:
            order = handler.get_order(order_id)
            if order and order.status == OrderStatus.FILLED:
                success_count += 1
        
        assert success_count >= len(order_ids) * 0.95  # 95%以上成功率
        
        # 验证系统状态
        final_state = handler.get_account_state()
        positions = handler.get_positions()
        
        assert len(positions) >= 90  # 至少90个持仓
        assert final_state.positions_value > 500000  # 持仓市值超过50万
    
    def test_concurrent_account_performance(self, clean_temp_db):
        """Test performance with concurrent accounts."""
        import threading
        import queue
        
        results_queue = queue.Queue()
        
        def account_worker(account_id):
            try:
                handler = StockAccountHandler(
                    strategy_name=f"concurrent_test_{account_id}",
                    account_id=account_id,
                    initial_cash=100000,
                    db_path=clean_temp_db
                )
                
                # 每个账户执行10笔交易
                for i in range(10):
                    security = f"00000{account_id}.XSHE"
                    handler.send_order(security, 100, 10.0 + i * 0.1)
                
                final_state = handler.get_account_state()
                results_queue.put(("success", account_id, final_state.total_value))
                
            except Exception as e:
                results_queue.put(("error", account_id, str(e)))
        
        # 启动10个并发账户
        threads = []
        start_time = time.time()
        
        for account_id in range(1, 11):
            thread = threading.Thread(target=account_worker, args=(account_id,))
            threads.append(thread)
            thread.start()
        
        # 等待所有线程完成
        for thread in threads:
            thread.join()
        
        end_time = time.time()
        
        # 收集结果
        results = []
        while not results_queue.empty():
            results.append(results_queue.get())
        
        # 验证性能和正确性
        success_count = len([r for r in results if r[0] == "success"])
        assert success_count >= 8  # 至少80%的账户成功
        
        total_time = end_time - start_time
        assert total_time < 30.0  # 总时间应小于30秒
        
        # 验证每个成功账户的最终状态
        for status, account_id, total_value in results:
            if status == "success":
                assert isinstance(total_value, float)
                assert 80000 <= total_value <= 120000  # 合理的资产范围
    
    def test_database_performance_stress(self, clean_temp_db):
        """Test database performance under stress."""
        handler = StockAccountHandler(
            strategy_name="db_stress_test",
            account_id=1,
            initial_cash=1000000,
            db_path=clean_temp_db
        )
        
        # 执行大量快速交易以测试数据库性能
        securities = [f"00000{i}.XSHE" for i in range(1, 21)]  # 20只股票
        
        start_time = time.time()
        
        # 每只股票执行10轮买卖
        for round_num in range(10):
            for i, security in enumerate(securities):
                # 买入
                handler.send_order(security, 100, 10.0 + i * 0.1)
                # 卖出
                handler.send_order(security, -100, 10.0 + i * 0.1 + 0.01)
        
        end_time = time.time()
        
        # 验证处理时间
        total_orders = len(securities) * 10 * 2  # 20股票 * 10轮 * 2操作
        total_time = end_time - start_time
        avg_time_per_order = total_time / total_orders
        
        assert avg_time_per_order < 0.05  # 每笔订单平均处理时间应小于50ms
        assert total_time < 60.0  # 总时间应小于1分钟
        
        # 验证数据一致性
        final_state = handler.get_account_state()
        transactions = handler.get_transactions()
        
        assert len(transactions) >= total_orders * 0.9  # 90%以上的交易记录
        
        # 最终持仓应该接近0（买卖平衡）
        positions = handler.get_positions()
        total_position_amount = sum(abs(pos.total_amount) for pos in positions.values())
        assert total_position_amount <= len(securities) * 100  # 允许一些不平衡