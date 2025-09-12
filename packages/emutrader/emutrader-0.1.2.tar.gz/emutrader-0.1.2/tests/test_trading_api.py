"""
全局交易API测试
测试order_shares, order_value, order_target_percent等JQ兼容交易函数
"""

import pytest
from emutrader import (
    get_jq_account, order_shares, order_value, order_target_percent,
    Order
)
from emutrader.api import set_current_context, get_current_context


class TestTradingAPISetup:
    """测试交易API设置和上下文管理"""
    
    @pytest.mark.trading_api
    def test_set_current_context(self):
        """测试设置当前上下文"""
        context = get_jq_account("context_test", 100000)
        
        # 设置上下文
        set_current_context(context)
        
        # 验证上下文设置成功
        current_context = get_current_context()
        assert current_context is context
        assert current_context.run_params['strategy_name'] == "context_test"
    
    @pytest.mark.trading_api
    def test_context_isolation(self):
        """测试多个上下文的隔离"""
        context1 = get_jq_account("strategy1", 100000)
        context2 = get_jq_account("strategy2", 200000)
        
        # 设置第一个上下文并交易
        set_current_context(context1)
        order_shares('000001.SZ', 1000)
        
        # 切换到第二个上下文并交易
        set_current_context(context2)
        order_shares('000002.SZ', 500)
        
        # 验证两个上下文数据独立
        assert context1.portfolio.total_value != context2.portfolio.total_value
        assert '000001.SZ' in context1.portfolio.positions
        assert '000001.SZ' not in context2.portfolio.positions
        assert '000002.SZ' not in context1.portfolio.positions
        assert '000002.SZ' in context2.portfolio.positions


class TestOrderShares:
    """测试order_shares函数"""
    
    @pytest.mark.trading_api
    def test_order_shares_basic_buy(self):
        """测试基本买入功能"""
        context = get_jq_account("buy_test", 100000)
        set_current_context(context)
        
        # 执行买入订单
        order = order_shares('000001.SZ', 1000)
        
        # 验证订单对象
        assert isinstance(order, Order)
        assert order.security == '000001.SZ'
        assert order.amount == 1000
        assert order.status in ['filled', 'pending', 'submitted']
        
        # 验证账户状态变化
        portfolio = context.portfolio
        assert portfolio.available_cash < 100000.0  # 现金减少
        assert portfolio.market_value > 0  # 有市值
        assert portfolio.has_position('000001.SZ')  # 有持仓
    
    @pytest.mark.trading_api
    def test_order_shares_basic_sell(self):
        """测试基本卖出功能"""
        context = get_jq_account("sell_test", 100000)
        set_current_context(context)
        
        # 先买入建立持仓
        order_shares('000001.SZ', 1000)
        initial_cash = context.portfolio.available_cash
        
        # 卖出部分持仓
        sell_order = order_shares('000001.SZ', -500)
        
        # 验证卖出订单
        assert isinstance(sell_order, Order)
        assert sell_order.security == '000001.SZ'
        assert sell_order.amount == -500
        
        # 验证卖出后状态
        portfolio = context.portfolio
        assert portfolio.available_cash > initial_cash  # 现金增加
        
        position = portfolio.get_position('000001.SZ')
        assert position.total_amount == 500  # 持仓减少
    
    @pytest.mark.trading_api
    def test_order_shares_with_price(self):
        """测试带价格的订单"""
        context = get_jq_account("price_test", 100000)
        set_current_context(context)
        
        # 指定价格下单
        order = order_shares('000001.SZ', 1000, 12.50)
        
        # 验证订单价格
        assert isinstance(order, Order)
        assert order.price == 12.50
        
        # 验证成交价格合理
        position = context.portfolio.get_position('000001.SZ')
        assert position.avg_cost > 0
    
    @pytest.mark.trading_api
    def test_order_shares_multiple_stocks(self):
        """测试多只股票交易"""
        context = get_jq_account("multi_test", 200000)
        set_current_context(context)
        
        # 买入多只股票
        stocks = ['000001.SZ', '000002.SZ', '600519.SH', '000858.SZ']
        orders = []
        
        for stock in stocks:
            order = order_shares(stock, 500)
            orders.append(order)
        
        # 验证所有订单
        assert len(orders) == 4
        assert all(isinstance(order, Order) for order in orders)
        
        # 验证持仓
        portfolio = context.portfolio
        for stock in stocks:
            assert portfolio.has_position(stock)
            position = portfolio.get_position(stock)
            assert position.total_amount == 500
    
    @pytest.mark.trading_api
    def test_order_shares_edge_cases(self):
        """测试边界情况"""
        context = get_jq_account("edge_test", 100000)
        set_current_context(context)
        
        # 测试最小交易单位
        order = order_shares('000001.SZ', 100)
        assert isinstance(order, Order)
        assert order.amount == 100
        
        # 测试大额交易
        large_order = order_shares('000002.SZ', 5000, 10.0)
        assert isinstance(large_order, Order)
        
        # 验证持仓正确创建
        position1 = context.portfolio.get_position('000001.SZ')
        position2 = context.portfolio.get_position('000002.SZ')
        assert position1.total_amount == 100
        assert position2.total_amount == 5000


class TestOrderValue:
    """测试order_value函数"""
    
    @pytest.mark.trading_api
    def test_order_value_basic_buy(self):
        """测试按金额买入"""
        context = get_jq_account("value_buy_test", 100000)
        set_current_context(context)
        
        # 按金额买入
        order = order_value('000001.SZ', 20000)
        
        # 验证订单
        assert isinstance(order, Order)
        assert order.security == '000001.SZ'
        assert abs(order.amount * order.price) >= 19000  # 约20000元，允许误差
        assert abs(order.amount * order.price) <= 21000
        
        # 验证持仓价值
        position = context.portfolio.get_position('000001.SZ')
        assert position.value >= 19000
        assert position.value <= 21000
    
    @pytest.mark.trading_api
    def test_order_value_basic_sell(self):
        """测试按金额卖出"""
        context = get_jq_account("value_sell_test", 100000)
        set_current_context(context)
        
        # 先买入
        order_shares('000001.SZ', 2000)
        initial_cash = context.portfolio.available_cash
        
        # 按金额卖出
        sell_order = order_value('000001.SZ', -10000)
        
        # 验证卖出订单
        assert isinstance(sell_order, Order)
        assert sell_order.amount < 0  # 卖出数量为负
        
        # 验证现金增加
        assert context.portfolio.available_cash > initial_cash
    
    @pytest.mark.trading_api
    def test_order_value_with_price(self):
        """测试指定价格的按金额交易"""
        context = get_jq_account("value_price_test", 100000)
        set_current_context(context)
        
        # 指定价格按金额买入
        target_value = 30000
        price = 15.0
        
        order = order_value('000001.SZ', target_value, price)
        
        # 验证订单
        assert isinstance(order, Order)
        assert order.price == price
        
        # 计算期望数量
        expected_amount = int(target_value / price / 100) * 100  # 取整到100股
        assert abs(order.amount - expected_amount) <= 100
    
    @pytest.mark.trading_api
    def test_order_value_percentage_allocation(self):
        """测试按比例分配资金"""
        context = get_jq_account("allocation_test", 200000)
        set_current_context(context)
        
        # 分配不同比例的资金到不同股票
        allocation = {
            '000001.SZ': 0.3,  # 30%
            '000002.SZ': 0.2,  # 20%
            '600519.SH': 0.25, # 25%
            '000858.SZ': 0.15  # 15%
        }
        
        total_value = context.portfolio.total_value
        orders = []
        
        for stock, ratio in allocation.items():
            target_amount = total_value * ratio
            order = order_value(stock, target_amount)
            orders.append(order)
        
        # 验证所有订单
        assert len(orders) == 4
        assert all(isinstance(order, Order) for order in orders)
        
        # 验证分配比例
        portfolio = context.portfolio
        for stock, expected_ratio in allocation.items():
            position = portfolio.get_position(stock)
            actual_ratio = position.value / total_value
            assert abs(actual_ratio - expected_ratio) < 0.05  # 允许5%误差


class TestOrderTargetPercent:
    """测试order_target_percent函数"""
    
    @pytest.mark.trading_api
    def test_order_target_percent_initial_buy(self):
        """测试初始买入到目标比例"""
        context = get_jq_account("target_test", 100000)
        set_current_context(context)
        
        # 调整到20%仓位
        order = order_target_percent('000001.SZ', 0.2)
        
        # 验证订单
        assert isinstance(order, Order)
        assert order.amount > 0  # 应该是买入
        
        # 验证目标仓位
        portfolio = context.portfolio
        position = portfolio.get_position('000001.SZ')
        actual_percent = position.value / portfolio.total_value
        
        assert abs(actual_percent - 0.2) < 0.05  # 允许5%误差
    
    @pytest.mark.trading_api
    def test_order_target_percent_adjustment(self):
        """测试仓位调整"""
        context = get_jq_account("adjust_test", 100000)
        set_current_context(context)
        
        # 先建立10%仓位
        order_target_percent('000001.SZ', 0.1)
        
        # 调整到30%仓位
        adjust_order = order_target_percent('000001.SZ', 0.3)
        
        # 验证调整订单
        assert isinstance(adjust_order, Order)
        assert adjust_order.amount > 0  # 应该是加仓
        
        # 验证最终仓位
        portfolio = context.portfolio
        position = portfolio.get_position('000001.SZ')
        actual_percent = position.value / portfolio.total_value
        
        assert abs(actual_percent - 0.3) < 0.05
    
    @pytest.mark.trading_api
    def test_order_target_percent_reduce(self):
        """测试减仓到目标比例"""
        context = get_jq_account("reduce_test", 100000)
        set_current_context(context)
        
        # 先建立30%仓位
        order_target_percent('000001.SZ', 0.3)
        initial_amount = context.portfolio.get_position('000001.SZ').total_amount
        
        # 减仓到10%
        reduce_order = order_target_percent('000001.SZ', 0.1)
        
        # 验证减仓订单
        assert isinstance(reduce_order, Order)
        assert reduce_order.amount < 0  # 应该是卖出
        
        # 验证最终仓位
        portfolio = context.portfolio
        position = portfolio.get_position('000001.SZ')
        assert position.total_amount < initial_amount
        
        actual_percent = position.value / portfolio.total_value
        assert abs(actual_percent - 0.1) < 0.05
    
    @pytest.mark.trading_api
    def test_order_target_percent_clear_position(self):
        """测试清仓"""
        context = get_jq_account("clear_test", 100000)
        set_current_context(context)
        
        # 先建立仓位
        order_target_percent('000001.SZ', 0.2)
        assert context.portfolio.has_position('000001.SZ')
        
        # 清仓
        clear_order = order_target_percent('000001.SZ', 0.0)
        
        # 验证清仓订单
        assert isinstance(clear_order, Order)
        assert clear_order.amount < 0  # 全部卖出
        
        # 验证持仓清空
        position = context.portfolio.get_position('000001.SZ')
        assert position.total_amount == 0
    
    @pytest.mark.trading_api
    def test_order_target_percent_equal_weight(self):
        """测试等权重投资组合"""
        context = get_jq_account("equal_weight_test", 200000)
        set_current_context(context)
        
        # 等权重投资5只股票
        stocks = ['000001.SZ', '000002.SZ', '600519.SH', '000858.SZ', '002415.SZ']
        target_percent = 0.8 / len(stocks)  # 80%资金等分
        
        orders = []
        for stock in stocks:
            order = order_target_percent(stock, target_percent)
            orders.append(order)
        
        # 验证所有订单
        assert len(orders) == 5
        assert all(isinstance(order, Order) for order in orders)
        
        # 验证等权重分配
        portfolio = context.portfolio
        for stock in stocks:
            position = portfolio.get_position(stock)
            actual_percent = position.value / portfolio.total_value
            assert abs(actual_percent - target_percent) < 0.03  # 允许3%误差
        
        # 验证总仓位约80%
        total_position_percent = sum(
            portfolio.get_position(stock).value / portfolio.total_value 
            for stock in stocks
        )
        assert abs(total_position_percent - 0.8) < 0.1


class TestTradingAPIErrorHandling:
    """测试交易API错误处理"""
    
    @pytest.mark.trading_api
    def test_no_context_error(self):
        """测试未设置上下文时的错误处理"""
        # 清除当前上下文（如果有）
        set_current_context(None)
        
        # 尝试交易应该失败或返回None
        order = order_shares('000001.SZ', 1000)
        assert order is None
        
        order = order_value('000001.SZ', 10000)
        assert order is None
        
        order = order_target_percent('000001.SZ', 0.1)
        assert order is None
    
    @pytest.mark.trading_api
    def test_invalid_security_codes(self):
        """测试无效证券代码"""
        context = get_jq_account("invalid_test", 100000)
        set_current_context(context)
        
        invalid_codes = ['', '123', 'INVALID', '000001.XX']
        
        for code in invalid_codes:
            # 无效代码应该返回None或引发异常
            order = order_shares(code, 1000)
            if order is not None:
                # 如果返回订单，应该标记为失败
                assert hasattr(order, 'status')
    
    @pytest.mark.trading_api
    def test_insufficient_funds(self):
        """测试资金不足情况"""
        context = get_jq_account("insufficient_test", 1000)  # 只有1000元
        set_current_context(context)
        
        # 尝试买入超过资金的股票
        order = order_shares('000001.SZ', 1000, 100.0)  # 需要10万元
        
        # 应该失败或返回None
        if order is not None:
            assert order.status in ['rejected', 'failed']
        
        # 验证账户状态未变
        assert context.portfolio.available_cash == 1000
        assert not context.portfolio.has_position('000001.SZ')
    
    @pytest.mark.trading_api
    def test_invalid_amounts(self):
        """测试无效交易数量"""
        context = get_jq_account("invalid_amount_test", 100000)
        set_current_context(context)
        
        # 测试零数量
        order = order_shares('000001.SZ', 0)
        assert order is None
        
        # 测试非100整数倍
        order = order_shares('000001.SZ', 150)
        assert order is None
        
        # 测试负数量买入（应该是卖出）
        order = order_shares('000001.SZ', -1000)
        if order is not None:
            assert order.amount < 0  # 确实是卖出


class TestTradingAPIPerformance:
    """测试交易API性能"""
    
    @pytest.mark.trading_api
    @pytest.mark.performance
    def test_trading_api_performance(self):
        """测试交易API性能"""
        import time
        
        context = get_jq_account("performance_test", 500000)
        set_current_context(context)
        
        # 测试批量交易性能
        securities = [f"{i:06d}.SZ" for i in range(1, 21)]  # 20只股票
        
        start_time = time.time()
        
        orders = []
        for security in securities:
            order = order_shares(security, 100)
            orders.append(order)
        
        end_time = time.time()
        
        # 验证性能
        total_time = end_time - start_time
        avg_time_ms = (total_time / len(securities)) * 1000
        
        assert avg_time_ms < 50  # 每笔交易平均 < 50ms
        
        # 验证交易结果
        successful_orders = [o for o in orders if o is not None]
        assert len(successful_orders) >= len(securities) * 0.8  # 80%成功率
    
    @pytest.mark.trading_api
    @pytest.mark.performance
    def test_context_switching_performance(self):
        """测试上下文切换性能"""
        import time
        
        # 创建多个上下文
        contexts = []
        for i in range(10):
            context = get_jq_account(f"switch_test_{i}", 100000)
            contexts.append(context)
        
        # 测试快速切换性能
        start_time = time.time()
        
        for _ in range(100):
            for context in contexts:
                set_current_context(context)
                order_shares('000001.SZ', 100)
        
        end_time = time.time()
        
        # 验证性能
        total_operations = 100 * len(contexts)
        total_time = end_time - start_time
        avg_time_ms = (total_time / total_operations) * 1000
        
        assert avg_time_ms < 10  # 每次操作 < 10ms


class TestTradingAPIIntegration:
    """测试交易API集成功能"""
    
    @pytest.mark.trading_api
    def test_mixed_trading_strategies(self):
        """测试混合交易策略"""
        context = get_jq_account("mixed_test", 300000)
        set_current_context(context)
        
        # 策略1: 按股数买入核心持仓
        core_holdings = ['000001.SZ', '000002.SZ']
        for stock in core_holdings:
            order_shares(stock, 1000)
        
        # 策略2: 按金额买入成长股
        growth_stocks = ['600519.SH', '000858.SZ']
        for stock in growth_stocks:
            order_value(stock, 30000)
        
        # 策略3: 按比例调整卫星持仓
        satellite_stocks = ['002415.SZ', '000063.SZ']
        for stock in satellite_stocks:
            order_target_percent(stock, 0.05)  # 各5%
        
        # 验证最终组合
        portfolio = context.portfolio
        
        # 验证核心持仓
        for stock in core_holdings:
            position = portfolio.get_position(stock)
            assert position.total_amount == 1000
        
        # 验证成长股持仓
        for stock in growth_stocks:
            position = portfolio.get_position(stock)
            assert position.value >= 25000  # 约30000元，允许误差
        
        # 验证卫星持仓比例
        for stock in satellite_stocks:
            position = portfolio.get_position(stock)
            weight = position.value / portfolio.total_value
            assert abs(weight - 0.05) < 0.02  # 允许2%误差
        
        # 验证总体仓位合理
        total_positions = len([p for p in portfolio.positions.values() 
                              if p.total_amount > 0])
        assert total_positions == 6
    
    @pytest.mark.trading_api
    def test_rebalancing_workflow(self):
        """测试调仓工作流"""
        context = get_jq_account("rebalance_test", 200000)
        set_current_context(context)
        
        # 第一次建仓
        initial_stocks = ['000001.SZ', '000002.SZ', '600519.SH']
        for stock in initial_stocks:
            order_target_percent(stock, 0.25)  # 各25%
        
        # 验证初始建仓
        portfolio = context.portfolio
        for stock in initial_stocks:
            position = portfolio.get_position(stock)
            weight = position.value / portfolio.total_value
            assert abs(weight - 0.25) < 0.05
        
        # 第二次调仓 - 调整权重
        rebalance_weights = {
            '000001.SZ': 0.4,   # 增加到40%
            '000002.SZ': 0.15,  # 减少到15%
            '600519.SH': 0.0,   # 清仓
            '000858.SZ': 0.25,  # 新增25%
        }
        
        for stock, weight in rebalance_weights.items():
            order_target_percent(stock, weight)
        
        # 验证调仓结果
        updated_portfolio = context.portfolio
        
        # 验证增仓股票
        pos_001 = updated_portfolio.get_position('000001.SZ')
        weight_001 = pos_001.value / updated_portfolio.total_value
        assert abs(weight_001 - 0.4) < 0.05
        
        # 验证减仓股票
        pos_002 = updated_portfolio.get_position('000002.SZ')
        weight_002 = pos_002.value / updated_portfolio.total_value
        assert abs(weight_002 - 0.15) < 0.05
        
        # 验证清仓股票
        pos_519 = updated_portfolio.get_position('600519.SH')
        assert pos_519.total_amount == 0
        
        # 验证新增股票
        pos_858 = updated_portfolio.get_position('000858.SZ')
        weight_858 = pos_858.value / updated_portfolio.total_value
        assert abs(weight_858 - 0.25) < 0.05