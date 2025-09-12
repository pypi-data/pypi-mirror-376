"""
JoinQuant API 兼容性测试
验证EmuTrader 100%兼容聚宽API的核心功能（基于新架构）
"""

import pytest
from datetime import datetime
from emutrader import (
    get_jq_account, order_shares, order_value, order_target_percent,
    set_subportfolios, SubPortfolioConfig, transfer_cash,
    Portfolio, Position, SubPortfolio
)
from emutrader.api import set_current_context, set_sub_context
from emutrader.core.trader import EmuTrader


class TestJQCompatibility:
    """测试聚宽API兼容性"""
    
    @pytest.mark.jq_compatibility
    def test_get_jq_account_basic(self):
        """测试获取聚宽账户基础功能"""
        # 创建JQ兼容账户
        emutrader = get_jq_account("test_strategy", 100000, "STOCK")
        
        # 验证返回类型（新架构返回EmuTrader）
        assert isinstance(emutrader, EmuTrader)
        
        # 验证JQ兼容属性存在
        assert hasattr(emutrader, 'portfolio')
        assert hasattr(emutrader, 'subportfolios')
        
        # 验证属性类型
        assert isinstance(emutrader.portfolio, Portfolio)
        assert isinstance(emutrader.subportfolios, list)
        
        # 验证初始状态
        assert emutrader.portfolio.total_value == 100000.0
        assert emutrader.portfolio.available_cash == 100000.0
        assert emutrader.portfolio.market_value == 0.0
        assert len(emutrader.subportfolios) == 0
        
        # 验证策略信息通过属性访问
        assert emutrader.strategy_name == "test_strategy"
        assert emutrader.account_type == "STOCK"
    
    @pytest.mark.jq_compatibility
    def test_portfolio_jq_compatibility(self):
        """测试投资组合对象JQ兼容性"""
        emutrader = get_jq_account("test_strategy", 100000)
        投资组合 = emutrader.portfolio
        
        # 验证JQ标准属性
        jq兼容属性列表 = [
            'total_value',      # 总资产
            'available_cash',   # 可用资金  
            'locked_cash',      # 冻结资金
            'market_value',     # 持仓市值
            'positions',        # 持仓字典
            'pnl',             # 当日盈亏
            'returns'          # 累计收益率
        ]
        
        for 属性名 in jq兼容属性列表:
            assert hasattr(投资组合, 属性名), f"Portfolio缺少JQ兼容属性: {属性名}"
        
        # 验证positions是字典类型
        assert isinstance(投资组合.positions, dict)
        
        # 验证数值属性类型
        assert isinstance(投资组合.total_value, float)
        assert isinstance(投资组合.available_cash, float)
        assert isinstance(投资组合.market_value, float)
        assert isinstance(投资组合.pnl, float)
        assert isinstance(投资组合.returns, float)
    
    @pytest.mark.jq_compatibility
    def test_position_jq_compatibility(self):
        """测试持仓对象JQ兼容性"""
        emutrader = get_jq_account("test_strategy", 100000)
        set_current_context(emutrader)
        
        # 创建持仓
        order_shares('000001.SZ', 1000)
        
        # 获取持仓对象
        持仓对象 = emutrader.portfolio.get_position('000001.SZ')
        assert 持仓对象 is not None
        
        # 验证JQ标准持仓属性
        jq持仓属性列表 = [
            'total_amount',     # 总持仓量
            'closeable_amount', # 可平仓量
            'avg_cost',         # 平均成本
            'value',           # 持仓价值
            'pnl',             # 持仓盈亏
            'side'             # 持仓方向
        ]
        
        for 属性名 in jq持仓属性列表:
            assert hasattr(持仓对象, 属性名), f"Position缺少JQ兼容属性: {属性名}"
        
        # 验证属性值合理性
        assert 持仓对象.total_amount == 1000
        assert 持仓对象.closeable_amount <= 持仓对象.total_amount
        assert 持仓对象.avg_cost > 0
        assert 持仓对象.value > 0
        assert 持仓对象.side in ['long', 'short']
    
    @pytest.mark.jq_compatibility  
    def test_global_trading_functions(self):
        """测试全局交易函数JQ兼容性"""
        emutrader = get_jq_account("test_strategy", 100000)
        set_current_context(emutrader)
        
        # 测试order_shares - JQ标准函数
        order1 = order_shares('000001.SZ', 1000)
        assert order1 is not None
        
        # 验证交易结果反映在portfolio中
        portfolio = emutrader.portfolio
        assert portfolio.available_cash < 100000.0
        assert portfolio.market_value > 0
        assert len(portfolio.positions) >= 1
        assert '000001.SZ' in portfolio.positions
        
        # 测试order_value - JQ标准函数
        order2 = order_value('000002.SZ', 10000)
        assert order2 is not None
        
        # 测试order_target_percent - JQ标准函数
        order3 = order_target_percent('600519.SH', 0.2)
        assert order3 is not None
        
        # 验证最终状态
        final_positions = len(portfolio.positions)
        assert final_positions >= 2  # 至少有2个持仓
    
    @pytest.mark.jq_compatibility
    def test_subportfolio_jq_compatibility(self):
        """测试子账户系统JQ兼容性"""
        emutrader = get_jq_account("test_strategy", 1000000)
        set_current_context(emutrader)
        
        # 测试set_subportfolios - JQ标准函数
        configs = [
            SubPortfolioConfig(cash=400000, type='stock'),
            SubPortfolioConfig(cash=300000, type='futures'),
            SubPortfolioConfig(cash=200000, type='index_futures'),
            SubPortfolioConfig(cash=100000, type='stock_margin'),
        ]
        
        set_subportfolios(configs)
        
        # 验证子账户创建成功
        assert len(emutrader.subportfolios) == 4
        
        # 验证每个子账户的JQ兼容性
        account_types = ['STOCK', 'FUTURE', 'INDEX_FUTURE', 'CREDIT']
        expected_cash = [400000, 300000, 200000, 100000]
        
        for i, subportfolio in enumerate(emutrader.subportfolios):
            # 验证子账户属性
            assert isinstance(subportfolio, SubPortfolio)
            assert hasattr(subportfolio, 'type')
            assert hasattr(subportfolio, 'total_value')
            assert hasattr(subportfolio, 'available_cash')
            assert hasattr(subportfolio, 'market_value')
            assert hasattr(subportfolio, 'positions')
            assert hasattr(subportfolio, 'pnl')
            assert hasattr(subportfolio, 'returns')
            
            # 验证子账户值
            assert subportfolio.type == account_types[i]
            assert subportfolio.available_cash == expected_cash[i]
            assert subportfolio.total_value == expected_cash[i]
            
        # 测试transfer_cash - JQ标准函数
        success = transfer_cash(from_pindex=1, to_pindex=0, cash=50000)
        assert success is True
        
        # 验证转账结果
        stock_sub = emutrader.subportfolios[0]
        futures_sub = emutrader.subportfolios[1]
        assert stock_sub.available_cash == 450000  # 400000 + 50000
        assert futures_sub.available_cash == 250000  # 300000 - 50000


class TestJQWorkflow:
    """测试完整的聚宽工作流程"""
    
    @pytest.mark.jq_compatibility
    def test_complete_jq_workflow(self):
        """测试完整的聚宽策略工作流程"""
        # 1. 创建策略上下文 - 与JQ完全相同
        context = get_jq_account("完整测试", 1000000, "STOCK")
        set_current_context(context)
        set_sub_context(context)
        
        # 2. 验证初始状态 - JQ风格
        assert context.portfolio.total_value == 1000000.0
        assert context.portfolio.available_cash == 1000000.0
        assert context.portfolio.market_value == 0.0
        assert context.portfolio.returns == 0.0
        
        # 3. 设置子账户 - JQ API
        set_subportfolios([
            SubPortfolioConfig(cash=600000, type='stock'),
            SubPortfolioConfig(cash=400000, type='futures'),
        ])
        
        assert len(context.subportfolios) == 2
        
        # 4. 执行交易 - JQ API
        stock_pool = ['000001.SZ', '000002.SZ', '600519.SH', '000858.SZ']
        
        # 等权重投资
        target_percent = 0.6 / len(stock_pool)  # 60%资金投入股票
        
        for security in stock_pool:
            order = order_target_percent(security, target_percent)
            assert order is not None
        
        # 5. 验证交易结果
        portfolio = context.portfolio
        
        # 检查资金使用情况
        assert portfolio.available_cash < 1000000.0  # 资金被使用
        assert portfolio.market_value > 0  # 有持仓价值
        
        # 检查持仓
        positions = portfolio.positions
        assert len(positions) >= len(stock_pool)
        
        for security in stock_pool:
            if security in positions:
                position = positions[security]
                assert position.total_amount > 0
                assert position.value > 0
                weight = position.value / portfolio.total_value
                assert 0.1 < weight < 0.25  # 每只股票权重合理
        
        # 6. 子账户资金转移
        success = transfer_cash(from_pindex=1, to_pindex=0, cash=100000)
        assert success is True
        
        stock_sub = context.subportfolios[0]
        futures_sub = context.subportfolios[1]
        assert stock_sub.available_cash > 600000  # 增加了资金
        assert futures_sub.available_cash < 400000  # 减少了资金
        
        # 7. 继续交易测试
        order_shares('002415.SZ', 1000)  # 按股数下单
        order_value('600036.SH', 50000)  # 按金额下单
        
        # 8. 验证最终状态
        final_portfolio = context.portfolio
        final_positions = len([p for p in final_portfolio.positions.values() 
                              if p.total_amount > 0])
        
        assert final_positions >= 4  # 至少4个有效持仓
        assert abs(final_portfolio.total_value - 1000000.0) < 10000  # 总资产合理范围
    
    @pytest.mark.jq_compatibility
    def test_jq_strategy_simulation(self):
        """模拟真实聚宽策略运行"""
        # 模拟JQ策略initialize函数
        def initialize(context):
            context.stocks = ['000001.SZ', '000002.SZ', '600519.SH']
            context.counter = 0
            context.rebalance_frequency = 3
            
            # 设置子账户
            set_subportfolios([
                SubPortfolioConfig(cash=500000, type='stock'),
                SubPortfolioConfig(cash=300000, type='futures'),
            ])
        
        # 模拟JQ策略handle_data函数
        def handle_data(context, data):
            context.counter += 1
            
            if context.counter % context.rebalance_frequency == 0:
                # 等权重调仓
                target_percent = 0.8 / len(context.stocks)
                for stock in context.stocks:
                    order_target_percent(stock, target_percent)
        
        # 创建策略上下文
        emutrader = get_jq_account("jq_simulation", 800000, "STOCK")
        set_current_context(emutrader)
        
        # 初始化策略
        initialize(emutrader)
        
        # 验证初始化结果
        assert hasattr(emutrader, 'stocks')
        assert hasattr(emutrader, 'counter')
        assert len(emutrader.subportfolios) == 2
        
        # 模拟多天运行
        for day in range(10):
            data = {}  # 模拟市场数据
            handle_data(emutrader, data)
            
            # 验证每天的状态
            assert emutrader.counter == day + 1
            
            # 调仓日验证
            if (day + 1) % 3 == 0:
                positions = emutrader.portfolio.positions
                active_positions = len([p for p in positions.values() 
                                      if p.total_amount > 0])
                assert active_positions >= 1  # 至少有持仓
        
        # 验证最终结果
        final_portfolio = emutrader.portfolio
        assert final_portfolio.total_value > 700000  # 合理范围
        assert final_portfolio.market_value > 0  # 有持仓
        assert emutrader.counter == 10  # 运行了10天


class TestJQCompatibilityEdgeCases:
    """测试JQ兼容性边界情况"""
    
    @pytest.mark.jq_compatibility
    def test_empty_operations(self):
        """测试空操作的JQ兼容性"""
        context = get_jq_account("edge_test", 100000)
        set_current_context(context)
        
        # 测试获取不存在的持仓
        position = context.portfolio.get_position('999999.SZ')
        assert position.total_amount == 0  # JQ返回空持仓对象
        
        # 测试空持仓列表
        positions = context.portfolio.positions
        assert isinstance(positions, dict)
        assert len(positions) == 0
    
    @pytest.mark.jq_compatibility
    def test_account_type_compatibility(self):
        """测试不同账户类型的JQ兼容性"""
        # 测试账户类型兼容性映射
        account_type_mappings = {
            "STOCK": "STOCK",
            "stock": "STOCK", 
            "FUTURE": "FUTURES",   # FUTURE -> FUTURES (兼容性映射)
            "FUTURES": "FUTURES",
            "future": "FUTURES",
            "futures": "FUTURES",
            "CREDIT": "STOCK",     # 融资融券归类为股票账户
            "INDEX_FUTURE": "FUTURES"  # 股指期货归类为期货账户
        }
        
        for input_type, expected_type in account_type_mappings.items():
            emutrader = get_jq_account(f"test_{input_type.lower()}", 100000, input_type)
            
            assert emutrader.account_type == expected_type, f"输入{input_type}应该映射到{expected_type}"
            assert isinstance(emutrader.portfolio, Portfolio)
            assert emutrader.portfolio.total_value == 100000.0
    
    @pytest.mark.jq_compatibility
    def test_concurrent_contexts(self):
        """测试多个策略上下文并存"""
        # 创建多个策略
        emutrader1 = get_jq_account("strategy1", 100000, "STOCK")
        emutrader2 = get_jq_account("strategy2", 200000, "FUTURE")
        emutrader3 = get_jq_account("strategy3", 150000, "CREDIT")
        
        # 验证相互独立
        assert emutrader1.portfolio.total_value == 100000
        assert emutrader2.portfolio.total_value == 200000
        assert emutrader3.portfolio.total_value == 150000
        
        assert emutrader1.strategy_name == "strategy1"
        assert emutrader2.strategy_name == "strategy2"
        assert emutrader3.strategy_name == "strategy3"
        
        # 验证类型隔离
        assert emutrader1.account_type == "STOCK"
        assert emutrader2.account_type == "FUTURES"  # FUTURE映射到FUTURES
        assert emutrader3.account_type == "STOCK"    # CREDIT映射到STOCK


class TestJQAPISignatures:
    """测试JQ API函数签名完全兼容"""
    
    @pytest.mark.jq_compatibility
    def test_get_jq_account_signature(self):
        """测试get_jq_account函数签名"""
        # 测试各种参数组合
        emutrader1 = get_jq_account("test")  # 最少参数
        emutrader2 = get_jq_account("test", 100000)  # 两个参数
        emutrader3 = get_jq_account("test", 100000, "STOCK")  # 全部参数
        
        assert all(isinstance(ctx, EmuTrader) for ctx in [emutrader1, emutrader2, emutrader3])
    
    @pytest.mark.jq_compatibility  
    def test_trading_function_signatures(self):
        """测试交易函数签名兼容性"""
        emutrader = get_jq_account("sig_test", 100000)
        set_current_context(emutrader)
        
        # order_shares的各种调用方式
        order1 = order_shares('000001.SZ', 1000)  # 基本调用
        order2 = order_shares('000002.SZ', 1000, 10.0)  # 带价格
        
        # order_value的各种调用方式
        order3 = order_value('000003.SZ', 10000)  # 基本调用
        order4 = order_value('000004.SZ', 10000, 15.0)  # 带价格
        
        # order_target_percent的调用
        order5 = order_target_percent('600519.SH', 0.2)
        
        # 验证所有调用都成功
        orders = [order1, order2, order3, order4, order5]
        assert all(order is not None for order in orders)
    
    @pytest.mark.jq_compatibility
    def test_subportfolio_function_signatures(self):
        """测试子账户函数签名兼容性"""
        emutrader = get_jq_account("sub_test", 100000)
        set_current_context(emutrader)
        
        # set_subportfolios的各种调用方式
        configs1 = [SubPortfolioConfig(cash=50000, type='stock')]
        set_subportfolios(configs1)
        
        configs2 = [
            SubPortfolioConfig(cash=30000, type='stock'),
            SubPortfolioConfig(cash=20000, type='futures')
        ]
        set_subportfolios(configs2)  # 重新设置
        
        # transfer_cash调用
        success = transfer_cash(from_pindex=1, to_pindex=0, cash=5000)
        assert success is True
        
        # 验证最终状态
        assert len(emutrader.subportfolios) == 2