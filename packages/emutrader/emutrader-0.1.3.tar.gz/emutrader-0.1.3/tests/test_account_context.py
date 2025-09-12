"""
StrategyContext 核心功能测试
测试策略上下文对象的所有功能和属性
"""

import pytest
from datetime import datetime, timedelta
from emutrader import get_jq_account, AccountContext, Portfolio, SubPortfolio
from emutrader.core.trader import EmuTrader


class TestAccountContextCreation:
    """测试AccountContext创建和初始化"""
    
    @pytest.mark.context
    def test_context_creation_via_get_jq_account(self):
        """测试通过get_jq_account创建上下文"""
        # 定义策略参数
        策略名称 = "test_strategy"
        初始资金 = 100000
        账户类型 = "STOCK"
        
        # 创建策略上下文
        context = get_jq_account(策略名称, 初始资金, 账户类型)
        
        # 验证类型（重构后返回EmuTrader对象）
        assert isinstance(context, EmuTrader)
        
        # 验证基本属性（重构后的属性访问）
        assert context.strategy_name == 策略名称
        assert context.initial_capital == 初始资金
        assert context.account_type == 账户类型
    
    @pytest.mark.context
    def test_context_direct_creation(self):
        """测试直接创建StrategyContext"""
        from emutrader.core.portfolio import Portfolio as DirectPortfolio
        
        # 定义参数
        策略名称 = "direct_test"
        初始资金 = 100000
        账户类型 = "STOCK"
        
        # 创建投资组合和上下文
        投资组合 = DirectPortfolio(initial_cash=初始资金)
        context = DirectStrategyContext(
            strategy_name=策略名称,
            portfolio=投资组合,
            account_type=账户类型
        )
        
        # 验证上下文创建
        assert isinstance(context, StrategyContext)
        assert context.run_params['strategy_name'] == 策略名称
        assert context.portfolio.total_value == 初始资金
    
    @pytest.mark.context
    def test_context_initialization_parameters(self):
        """测试Context初始化参数的各种组合"""
        # 测试默认参数
        context1 = get_jq_account("default_test")
        assert context1.portfolio.total_value == 100000.0  # 默认资金
        assert context1.run_params['account_type'] == "STOCK"  # 默认类型
        
        # 测试自定义参数
        context2 = get_jq_account("custom_test", 500000, "FUTURE")
        assert context2.portfolio.total_value == 500000.0
        assert context2.run_params['account_type'] == "FUTURE"
        
        # 测试大额资金
        context3 = get_jq_account("large_test", 10000000, "CREDIT")
        assert context3.portfolio.total_value == 10000000.0
        assert context3.run_params['account_type'] == "CREDIT"


class TestStrategyContextAttributes:
    """测试StrategyContext核心属性"""
    
    @pytest.mark.context
    def test_current_dt_attribute(self):
        """测试current_dt时间属性"""
        context = get_jq_account("dt_test", 100000)
        
        # 验证初始时间类型
        assert isinstance(context.current_dt, datetime)
        
        # 验证初始时间合理（应该是当前时间附近）
        now = datetime.now()
        time_diff = abs((now - context.current_dt).total_seconds())
        assert time_diff < 60  # 在1分钟内
        
        # 测试时间更新
        new_time = datetime(2024, 1, 15, 9, 30, 0)
        context.update_current_time(new_time)
        assert context.current_dt == new_time
    
    @pytest.mark.context
    def test_portfolio_attribute(self):
        """测试portfolio组合属性"""
        context = get_jq_account("portfolio_test", 100000)
        
        # 验证portfolio类型和基本属性
        assert isinstance(context.portfolio, Portfolio)
        assert context.portfolio.total_value == 100000.0
        assert context.portfolio.available_cash == 100000.0
        assert context.portfolio.market_value == 0.0
        
        # 验证portfolio是同一个对象引用
        portfolio_ref = context.portfolio
        assert context.portfolio is portfolio_ref
    
    @pytest.mark.context
    def test_subportfolios_attribute(self):
        """测试subportfolios子账户属性"""
        context = get_jq_account("sub_test", 100000)
        
        # 验证初始状态
        assert isinstance(context.subportfolios, list)
        assert len(context.subportfolios) == 0
        
        # 测试添加子账户
        from emutrader.core.subportfolio import SubPortfolio
        sub1 = SubPortfolio(type='STOCK', initial_cash=50000, index=0)
        sub2 = SubPortfolio(type='FUTURE', initial_cash=30000, index=1)
        
        context.add_subportfolio(sub1)
        context.add_subportfolio(sub2)
        
        assert len(context.subportfolios) == 2
        assert isinstance(context.subportfolios[0], SubPortfolio)
        assert isinstance(context.subportfolios[1], SubPortfolio)
        assert context.subportfolios[0].type == 'STOCK'
        assert context.subportfolios[1].type == 'FUTURE'
    
    @pytest.mark.context
    def test_run_params_attribute(self):
        """测试run_params运行参数属性"""
        context = get_jq_account("params_test", 200000, "CREDIT")
        
        # 验证run_params结构和内容
        assert isinstance(context.run_params, dict)
        
        expected_keys = ['strategy_name', 'initial_cash', 'account_type', 'created_at']
        for key in expected_keys:
            assert key in context.run_params
        
        assert context.run_params['strategy_name'] == "params_test"
        assert context.run_params['initial_cash'] == 200000
        assert context.run_params['account_type'] == "CREDIT"
        assert isinstance(context.run_params['created_at'], datetime)


class TestStrategyContextMethods:
    """测试StrategyContext核心方法"""
    
    @pytest.mark.context
    def test_update_current_time(self):
        """测试更新当前时间方法"""
        context = get_jq_account("time_test", 100000)
        
        # 记录原始时间
        original_time = context.current_dt
        
        # 测试更新到未来时间
        future_time = original_time + timedelta(days=1, hours=2, minutes=30)
        context.update_current_time(future_time)
        assert context.current_dt == future_time
        
        # 测试更新到过去时间
        past_time = original_time - timedelta(days=5)
        context.update_current_time(past_time)
        assert context.current_dt == past_time
        
        # 测试更新到特定时间
        specific_time = datetime(2024, 6, 15, 14, 30, 45)
        context.update_current_time(specific_time)
        assert context.current_dt == specific_time
    
    @pytest.mark.context
    def test_get_context_info(self):
        """测试获取上下文信息方法"""
        context = get_jq_account("info_test", 150000, "FUTURE")
        
        # 获取完整信息
        info = context.get_context_info()
        
        # 验证返回类型和结构
        assert isinstance(info, dict)
        
        expected_keys = [
            'strategy_name', 'current_dt', 'portfolio_info', 
            'subportfolios_count', 'run_params', 'created_at'
        ]
        
        for key in expected_keys:
            assert key in info, f"缺少关键信息: {key}"
        
        # 验证具体内容
        assert info['strategy_name'] == "info_test"
        assert isinstance(info['current_dt'], datetime)
        assert isinstance(info['portfolio_info'], dict)
        assert info['subportfolios_count'] == 0  # 初始无子账户
        assert info['run_params']['account_type'] == "FUTURE"
        
        # 测试添加子账户后的信息
        from emutrader.core.subportfolio import SubPortfolio
        sub = SubPortfolio(type='STOCK', initial_cash=50000, index=0)
        context.add_subportfolio(sub)
        
        updated_info = context.get_context_info()
        assert updated_info['subportfolios_count'] == 1
    
    @pytest.mark.context
    def test_add_subportfolio(self):
        """测试添加子账户方法"""
        context = get_jq_account("add_sub_test", 100000)
        
        # 验证初始状态
        assert len(context.subportfolios) == 0
        
        # 添加第一个子账户
        from emutrader.core.subportfolio import SubPortfolio
        sub1 = SubPortfolio(type='STOCK', initial_cash=60000, index=0)
        context.add_subportfolio(sub1)
        
        assert len(context.subportfolios) == 1
        assert context.subportfolios[0] is sub1
        assert context.subportfolios[0].type == 'STOCK'
        
        # 添加多个子账户
        sub2 = SubPortfolio(type='FUTURE', initial_cash=30000, index=1)
        sub3 = SubPortfolio(type='CREDIT', initial_cash=10000, index=2)
        
        context.add_subportfolio(sub2)
        context.add_subportfolio(sub3)
        
        assert len(context.subportfolios) == 3
        assert context.subportfolios[1].type == 'FUTURE'
        assert context.subportfolios[2].type == 'CREDIT'
    
    @pytest.mark.context
    def test_get_subportfolio(self):
        """测试获取指定子账户方法"""
        context = get_jq_account("get_sub_test", 100000)
        
        # 测试获取不存在的子账户
        result = context.get_subportfolio(0)
        assert result is None
        
        result = context.get_subportfolio(999)
        assert result is None
        
        # 添加子账户后测试
        from emutrader.core.subportfolio import SubPortfolio
        sub1 = SubPortfolio(type='STOCK', initial_cash=50000, index=0)
        sub2 = SubPortfolio(type='FUTURE', initial_cash=30000, index=1)
        sub3 = SubPortfolio(type='CREDIT', initial_cash=20000, index=2)
        
        context.add_subportfolio(sub1)
        context.add_subportfolio(sub2)
        context.add_subportfolio(sub3)
        
        # 测试获取存在的子账户
        retrieved_sub0 = context.get_subportfolio(0)
        retrieved_sub1 = context.get_subportfolio(1)
        retrieved_sub2 = context.get_subportfolio(2)
        
        assert retrieved_sub0 is sub1
        assert retrieved_sub1 is sub2
        assert retrieved_sub2 is sub3
        
        assert retrieved_sub0.type == 'STOCK'
        assert retrieved_sub1.type == 'FUTURE'
        assert retrieved_sub2.type == 'CREDIT'
        
        # 测试越界索引
        assert context.get_subportfolio(3) is None
        assert context.get_subportfolio(-1) is None


class TestStrategyContextIntegration:
    """测试StrategyContext与其他组件的集成"""
    
    @pytest.mark.context
    def test_context_portfolio_integration(self):
        """测试Context与Portfolio的集成"""
        context = get_jq_account("integration_test", 200000)
        
        # 验证Portfolio正确关联到Context
        portfolio = context.portfolio
        assert portfolio.total_value == 200000.0
        
        # 模拟Portfolio状态变化
        portfolio.available_cash = 150000.0
        portfolio.market_value = 50000.0
        
        # 验证Context中Portfolio状态同步更新
        assert context.portfolio.available_cash == 150000.0
        assert context.portfolio.market_value == 50000.0
        assert context.portfolio.total_value == 200000.0  # 总值不变
    
    @pytest.mark.context
    def test_context_subportfolio_integration(self):
        """测试Context与SubPortfolio的集成"""
        context = get_jq_account("sub_integration", 500000)
        
        # 添加子账户并测试集成
        from emutrader.core.subportfolio import SubPortfolio
        
        stock_sub = SubPortfolio(type='STOCK', initial_cash=300000, index=0)
        future_sub = SubPortfolio(type='FUTURE', initial_cash=200000, index=1)
        
        context.add_subportfolio(stock_sub)
        context.add_subportfolio(future_sub)
        
        # 验证子账户总资金与主账户一致
        total_sub_cash = sum(sub.available_cash for sub in context.subportfolios)
        assert total_sub_cash == context.portfolio.total_value
        
        # 测试子账户状态变化
        stock_sub.available_cash = 250000.0
        stock_sub.market_value = 50000.0
        
        # 验证可以通过Context访问到变化
        retrieved_stock = context.get_subportfolio(0)
        assert retrieved_stock.available_cash == 250000.0
        assert retrieved_stock.market_value == 50000.0
    
    @pytest.mark.context
    def test_context_time_consistency(self):
        """测试Context时间一致性"""
        context = get_jq_account("time_consistency", 100000)
        
        # 设置特定时间
        test_time = datetime(2024, 3, 15, 10, 30, 0)
        context.update_current_time(test_time)
        
        # 验证时间在所有组件中保持一致
        assert context.current_dt == test_time
        
        # 验证通过get_context_info获取的时间一致
        info = context.get_context_info()
        assert info['current_dt'] == test_time
        
        # 更新时间并验证一致性
        new_time = test_time + timedelta(hours=1)
        context.update_current_time(new_time)
        
        assert context.current_dt == new_time
        updated_info = context.get_context_info()
        assert updated_info['current_dt'] == new_time


class TestStrategyContextEdgeCases:
    """测试StrategyContext边界情况和异常处理"""
    
    @pytest.mark.context
    def test_context_large_values(self):
        """测试大数值情况"""
        # 测试超大初始资金
        large_cash = 1_000_000_000.0  # 10亿
        context = get_jq_account("large_test", large_cash)
        
        assert context.portfolio.total_value == large_cash
        assert context.portfolio.available_cash == large_cash
        
        # 测试极小初始资金
        small_cash = 0.01
        context_small = get_jq_account("small_test", small_cash)
        
        assert context_small.portfolio.total_value == small_cash
        assert context_small.portfolio.available_cash == small_cash
    
    @pytest.mark.context
    def test_context_special_strategy_names(self):
        """测试特殊策略名称"""
        special_names = [
            "test-strategy",      # 带连字符
            "test_strategy_123",  # 带下划线和数字
            "测试策略",            # 中文名称
            "Test Strategy",      # 带空格
            "test.strategy",      # 带点号
        ]
        
        for name in special_names:
            context = get_jq_account(name, 100000)
            assert context.run_params['strategy_name'] == name
    
    @pytest.mark.context
    def test_context_datetime_edge_cases(self):
        """测试时间边界情况"""
        context = get_jq_account("datetime_test", 100000)
        
        # 测试极值时间
        min_time = datetime.min
        max_time = datetime.max
        
        context.update_current_time(min_time)
        assert context.current_dt == min_time
        
        context.update_current_time(max_time)
        assert context.current_dt == max_time
        
        # 测试时区相关时间
        import pytz
        utc_time = datetime.now(pytz.UTC)
        context.update_current_time(utc_time)
        assert context.current_dt == utc_time
    
    @pytest.mark.context
    def test_context_subportfolio_edge_cases(self):
        """测试子账户边界情况"""
        context = get_jq_account("edge_test", 100000)
        
        # 测试添加大量子账户
        from emutrader.core.subportfolio import SubPortfolio
        
        max_subs = 100
        for i in range(max_subs):
            sub = SubPortfolio(type='STOCK', initial_cash=1000, index=i)
            context.add_subportfolio(sub)
        
        assert len(context.subportfolios) == max_subs
        
        # 测试获取边界索引
        assert context.get_subportfolio(0) is not None
        assert context.get_subportfolio(max_subs - 1) is not None
        assert context.get_subportfolio(max_subs) is None
        
        # 测试负数索引
        assert context.get_subportfolio(-1) is None
        assert context.get_subportfolio(-100) is None


class TestStrategyContextPerformance:
    """测试StrategyContext性能特性"""
    
    @pytest.mark.context
    @pytest.mark.performance
    def test_context_creation_performance(self):
        """测试Context创建性能"""
        import time
        
        start_time = time.time()
        
        # 创建多个Context
        contexts = []
        for i in range(100):
            context = get_jq_account(f"perf_test_{i}", 100000)
            contexts.append(context)
        
        end_time = time.time()
        
        # 验证创建速度
        creation_time = end_time - start_time
        avg_time_ms = (creation_time / 100) * 1000
        
        assert avg_time_ms < 10  # 平均每个Context创建时间 < 10ms
        assert len(contexts) == 100
        
        # 验证每个Context都正确初始化
        for i, context in enumerate(contexts):
            assert context.run_params['strategy_name'] == f"perf_test_{i}"
            assert context.portfolio.total_value == 100000.0
    
    @pytest.mark.context
    @pytest.mark.performance 
    def test_context_method_performance(self):
        """测试Context方法调用性能"""
        import time
        
        context = get_jq_account("method_perf", 100000)
        
        # 添加一些子账户
        from emutrader.core.subportfolio import SubPortfolio
        for i in range(10):
            sub = SubPortfolio(type='STOCK', initial_cash=10000, index=i)
            context.add_subportfolio(sub)
        
        # 测试get_context_info性能
        start_time = time.time()
        for _ in range(1000):
            info = context.get_context_info()
        end_time = time.time()
        
        avg_time_ms = ((end_time - start_time) / 1000) * 1000
        assert avg_time_ms < 1  # 平均每次调用 < 1ms
        
        # 测试get_subportfolio性能  
        start_time = time.time()
        for _ in range(1000):
            sub = context.get_subportfolio(5)
        end_time = time.time()
        
        avg_time_ms = ((end_time - start_time) / 1000) * 1000
        assert avg_time_ms < 0.1  # 平均每次获取 < 0.1ms