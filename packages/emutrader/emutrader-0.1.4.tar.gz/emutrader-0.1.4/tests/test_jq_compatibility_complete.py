"""
JoinQuant API兼容性测试
验证EmuTrader 100%兼容聚宽API的所有功能
"""

import pytest
from datetime import datetime
from emutrader import (
    get_jq_account, order_shares, order_value, order_target_percent,
    set_subportfolios, SubPortfolioConfig, transfer_cash,
    Portfolio, Position, SubPortfolio, OrderCost
)
from emutrader.api import set_current_context, set_sub_context, set_order_cost
from emutrader.core.trader import EmuTrader


class TestJQAccountCreation:
    """测试JQ账户创建"""
    
    def test_get_jq_account_basic_functionality(self):
        print("\n=== 测试get_jq_account基础功能 ===")
        print("【测试内容】验证JQ兼容账户创建函数的基本功能")
        print("【操作】创建10万初始资金的股票策略账户")
        
        # 标准创建方式
        emutrader = get_jq_account("test_strategy", 100000, "STOCK")
        
        print("[账户创建完成]")
        print(f"  [实例类型] {type(emutrader).__name__}")
        
        # 验证返回类型
        assert isinstance(emutrader, EmuTrader)
        print("  [[成功]] 返回EmuTrader实例")
        
        # 验证JQ兼容属性
        print("[验证JQ兼容属性]")
        jq_attrs = ['portfolio', 'subportfolios']
        for attr in jq_attrs:
            assert hasattr(emutrader, attr), f"缺少JQ属性: {attr}"
            print(f"  [[成功]] {attr}: 存在")
        assert hasattr(emutrader, 'strategy_name')
        assert hasattr(emutrader, 'account_type')
        
        # 验证初始状态
        print("[验证初始状态]")
        print(f"  [总资产] {emutrader.portfolio.total_value:,}元 (预期: 100,000)")
        print(f"  [可用资金] {emutrader.portfolio.available_cash:,}元 (预期: 100,000)")
        print(f"  [持仓市值] {emutrader.portfolio.market_value:,}元 (预期: 0)")
        print(f"  [收益率] {emutrader.portfolio.returns:.4f} (预期: 0)")
        print(f"  [子账户数量] {len(emutrader.subportfolios)}个 (预期: 0)")
        
        assert emutrader.portfolio.total_value == 100000.0
        assert emutrader.portfolio.available_cash == 100000.0
        assert emutrader.portfolio.market_value == 0.0
        assert emutrader.portfolio.returns == 0.0
        assert len(emutrader.subportfolios) == 0
        
        # 验证策略信息
        print("[验证策略信息]")
        print(f"  [策略名称] {emutrader.strategy_name} (预期: test_strategy)")
        print(f"  [账户类型] {emutrader.account_type} (预期: STOCK)")
        
        assert emutrader.strategy_name == "test_strategy"
        assert emutrader.account_type == "STOCK"
    
    def test_get_jq_account_parameter_variations(self):
        print("\n=== 测试get_jq_account参数变化 ===")
        print("【测试内容】验证不同参数组合的账户创建功能")
        print("【操作】测试1个、2个、3个参数的不同调用方式")
        
        # 测试最少参数
        print("[测试1个参数: 仅策略名称]")
        emutrader1 = get_jq_account("test1")
        assert isinstance(emutrader1, EmuTrader)
        assert emutrader1.strategy_name == "test1"
        print(f"  [策略名称] {emutrader1.strategy_name} [成功]")
        
        # 测试两个参数
        print("[测试2个参数: 策略名称+资金]")
        emutrader2 = get_jq_account("test2", 200000)
        print(f"  [总资产] {emutrader2.portfolio.total_value:,}元 (预期: 200,000)")
        assert emutrader2.portfolio.total_value == 200000.0
        
        # 测试完整参数
        print("[测试3个参数: 策略名称+资金+账户类型]")
        emutrader3 = get_jq_account("test3", 300000, "FUTURE")
        print(f"  [总资产] {emutrader3.portfolio.total_value:,}元 (预期: 300,000)")
        print(f"  [账户类型] {emutrader3.account_type} (预期: FUTURES)")
        
        assert emutrader3.portfolio.total_value == 300000.0
        assert emutrader3.account_type == "FUTURES"
    
    def test_get_jq_account_account_type_mapping(self):
        print("\n=== 测试账户类型兼容性映射 ===")
        print("【测试内容】验证不同账户类型格式的自动映射功能")
        print("【验证】大小写不敏感，以及特殊类型到标准类型的映射")
        
        test_cases = [
            ("STOCK", "STOCK"),
            ("stock", "STOCK"),
            ("FUTURE", "FUTURES"),
            ("FUTURES", "FUTURES"),
            ("future", "FUTURES"),
            ("futures", "FUTURES"),
            ("CREDIT", "STOCK"),
            ("INDEX_FUTURE", "FUTURES")
        ]
        
        print("[测试不同输入类型的映射结果]")
        for input_type, expected_type in test_cases:
            print(f"[测试] 输入: '{input_type}' → 预期: '{expected_type}'")
            
            emutrader = get_jq_account(f"test_{input_type}", 100000, input_type)
            
            actual_type = emutrader.account_type
            print(f"  [结果] 映射后: '{actual_type}'")
            assert actual_type == expected_type, f"映射失败: {input_type} → {actual_type}, 预期: {expected_type}"
            print(f"  [成功] 映射正确")


class TestJQPortfolioCompatibility:
    """测试JQ Portfolio兼容性"""
    
    def test_portfolio_jq_attributes(self):
        print("\n=== 测试Portfolio的JQ标准属性 ===")
        print("【测试内容】验证Portfolio对象是否完全兼容JQ标准属性")
        print("【验证】7个核心JQ属性的存在性和类型")
        
        emutrader = get_jq_account("test_strategy", 100000)
        portfolio = emutrader.portfolio
        
        # 验证所有JQ标准属性
        jq_attrs = [
            'total_value',      # 总资产
            'available_cash',   # 可用资金
            'locked_cash',      # 冻结资金
            'market_value',     # 持仓市值
            'positions',        # 持仓字典
            'pnl',             # 当日盈亏
            'returns'          # 累计收益率
        ]
        
        print("[验证JQ属性存在性]")
        for attr in jq_attrs:
            assert hasattr(portfolio, attr), f"Portfolio缺少JQ属性: {attr}"
            print(f"  [成功] {attr}: 存在")
        
        print("[验证属性类型]")
        type_checks = [
            ('total_value', float),
            ('available_cash', float),
            ('locked_cash', float),
            ('market_value', float),
            ('positions', dict),
            ('pnl', float),
            ('returns', float)
        ]
        
        for attr, expected_type in type_checks:
            actual_value = getattr(portfolio, attr)
            assert isinstance(actual_value, expected_type), f"{attr}类型错误: {type(actual_value)}, 预期: {expected_type}"
            print(f"  [成功] {attr}: {type(actual_value).__name__}")
    
    def test_portfolio_positions_dict_compatibility(self):
        """测试Portfolio的positions字典JQ兼容性"""
        print("\n=== 测试Portfolio的positions字典JQ兼容性 ===")
        print("【测试内容】验证Portfolio的positions字典是否完全兼容JQ API")
        print("【验证】positions字典的类型、内容、以及持仓对象类型")
        
        emutrader = get_jq_account("test_strategy", 100000)
        set_current_context(emutrader)
        
        print("[验证初始状态]")
        # 初始状态
        positions = emutrader.portfolio.positions
        assert isinstance(positions, dict)
        print(f"  [positions类型] {type(positions).__name__} (预期: dict)")
        assert len(positions) == 0
        print(f"  [初始持仓数量] {len(positions)}个 (预期: 0)")
        
        print("[添加持仓操作]")
        # 添加持仓
        print("  执行买入操作: order_shares('000001.SZ', 1000)")
        order_shares('000001.SZ', 1000)
        print("  执行买入操作: order_shares('000002.SZ', 500)")
        order_shares('000002.SZ', 500)
        
        print("[验证positions字典]")
        # 验证positions字典
        positions = emutrader.portfolio.positions
        print(f"  [持仓数量] {len(positions)}个 (预期: >= 2)")
        assert len(positions) >= 2
        
        print("[验证持仓对象类型和属性]")
        # 验证持仓对象类型
        for security, position in positions.items():
            print(f"  [持仓代码] {security}")
            assert isinstance(security, str)
            print(f"    [代码类型] {type(security).__name__} [成功]")
            
            assert isinstance(position, Position)
            print(f"    [持仓对象类型] {type(position).__name__} [成功]")
            
            assert position.total_amount > 0
            print(f"    [持仓数量] {position.total_amount}股 (> 0) [成功]")
    
    def test_portfolio_methods_compatibility(self):
        """测试Portfolio方法的JQ兼容性"""
        print("\n=== 测试Portfolio方法的JQ兼容性 ===")
        print("【测试内容】验证Portfolio类提供的JQ兼容方法")
        print("【测试方法】get_position()、has_position()方法的正确性")
        
        emutrader = get_jq_account("test_strategy", 100000)
        set_current_context(emutrader)
        
        portfolio = emutrader.portfolio
        
        print("[测试get_position方法 - 空持仓]")
        # 测试get_position方法
        print("  获取不存在持仓: portfolio.get_position('000001.SZ')")
        position = portfolio.get_position('000001.SZ')
        assert isinstance(position, Position)
        print(f"    [返回类型] {type(position).__name__} [成功]")
        assert position.total_amount == 0
        print(f"    [持仓数量] {position.total_amount}股 (预期: 0) [成功]")
        
        print("[创建持仓]")
        # 创建持仓后测试
        print("  买入1000股: order_shares('000001.SZ', 1000)")
        order_shares('000001.SZ', 1000)
        
        print("[测试get_position方法 - 有持仓]")
        position = portfolio.get_position('000001.SZ')
        print(f"    [持仓数量] {position.total_amount}股 (预期: 1000)")
        assert position.total_amount == 1000
        print("    [验证成功] [成功]")
        
        print("[测试has_position方法]")
        # 测试has_position方法
        print("  检查存在持仓: portfolio.has_position('000001.SZ')")
        result1 = portfolio.has_position('000001.SZ')
        print(f"    [结果] {result1} (预期: True)")
        assert result1 is True
        
        print("  检查不存在持仓: portfolio.has_position('999999.SZ')")
        result2 = portfolio.has_position('999999.SZ')
        print(f"    [结果] {result2} (预期: False)")
        assert result2 is False


class TestJQPositionCompatibility:
    """测试JQ Position兼容性"""
    
    def test_position_jq_attributes(self):
        """测试Position的JQ标准属性"""
        print("\n=== 测试Position的JQ标准属性 ===")
        print("【测试内容】验证Position对象是否完全兼容JQ标准属性")
        print("【验证】6个核心JQ持仓属性的存在性和合理性")
        
        emutrader = get_jq_account("test_strategy", 100000)
        set_current_context(emutrader)
        
        print("[创建持仓]")
        # 创建持仓
        print("  买入1000股: order_shares('000001.SZ', 1000)")
        order_shares('000001.SZ', 1000)
        position = emutrader.portfolio.get_position('000001.SZ')
        
        print("[验证JQ标准持仓属性]")
        # 验证JQ标准持仓属性
        jq_position_attrs = [
            'total_amount',     # 总持仓量
            'closeable_amount', # 可平仓量
            'avg_cost',         # 平均成本
            'value',           # 持仓价值
            'pnl',             # 持仓盈亏
            'side'             # 持仓方向
        ]
        
        for attr in jq_position_attrs:
            assert hasattr(position, attr), f"Position缺少JQ属性: {attr}"
            print(f"  [成功] {attr}: 存在")
        
        print("[验证属性值合理性]")
        # 验证属性值合理性
        print(f"  [总持仓量] {position.total_amount}股 (预期: 1000)")
        assert position.total_amount == 1000
        
        print(f"  [可平仓量] {position.closeable_amount}股 (<= 总持仓量)")
        assert position.closeable_amount <= position.total_amount
        
        print(f"  [平均成本] {position.avg_cost:.2f}元 (> 0)")
        assert position.avg_cost > 0
        
        print(f"  [持仓价值] {position.value:.2f}元 (> 0)")
        assert position.value > 0
        
        print(f"  [持仓方向] {position.side} (预期: long或short)")
        assert position.side in ['long', 'short']
    
    def test_position_empty_handling(self):
        """测试空持仓处理（JQ兼容性）"""
        print("\n=== 测试空持仓处理（JQ兼容性） ===")
        print("【测试内容】验证JQ API中获取不存在持仓时的处理方式")
        print("【验证】JQ返回空持仓对象，而不是None")
        
        emutrader = get_jq_account("test_strategy", 100000)
        
        print("[获取不存在的持仓]")
        # 获取不存在的持仓
        print("  尝试获取不存在持仓: portfolio.get_position('999999.SZ')")
        position = emutrader.portfolio.get_position('999999.SZ')
        
        print("[验证返回对象类型]")
        # JQ返回空持仓对象，不是None
        assert isinstance(position, Position)
        print(f"  [返回类型] {type(position).__name__} [成功]")
        
        print("[验证空持仓属性值]")
        assert position.total_amount == 0
        print(f"  [总持仓量] {position.total_amount}股 [成功]")
        
        assert position.value == 0
        print(f"  [持仓价值] {position.value}元 [成功]")
        
        assert position.pnl == 0
        print(f"  [持仓盈亏] {position.pnl}元 [成功]")


class TestJQTradingFunctions:
    """测试JQ交易函数兼容性"""
    
    def test_order_shares_compatibility(self):
        """测试order_shares函数JQ兼容性"""
        print("\n=== 测试order_shares函数JQ兼容性 ===")
        print("【测试内容】验证order_shares函数是否完全兼容JQ API")
        print("【测试场景】基本买入、带价格参数的买入")
        
        emutrader = get_jq_account("test_strategy", 100000)
        set_current_context(emutrader)
        
        print("[记录初始状态]")
        # 记录初始状态
        initial_cash = emutrader.portfolio.available_cash
        print(f"  [初始可用资金] {initial_cash:,.2f}元")
        
        print("[测试基本调用 - 按数量买入]")
        # 测试基本调用
        print("  执行买入: order_shares('000001.SZ', 1000)")
        order1 = order_shares('000001.SZ', 1000)
        assert order1 is not None
        print(f"  [返回值] {order1} (不是None) [成功]")
        
        print("[验证交易结果]")
        # 验证交易结果
        final_cash = emutrader.portfolio.available_cash
        print(f"  [交易后资金] {final_cash:,.2f}元 < {initial_cash:,.2f}元")
        assert final_cash < initial_cash
        
        has_position = emutrader.portfolio.has_position('000001.SZ')
        print(f"  [持仓状态] {has_position} (预期: True)")
        assert has_position
        
        position = emutrader.portfolio.get_position('000001.SZ')
        print(f"  [持仓数量] {position.total_amount}股 (预期: 1000)")
        assert position.total_amount == 1000
        
        print("[测试带价格参数的调用]")
        # 测试带价格参数的调用
        print("  执行指定价格买入: order_shares('000002.SZ', 500, 15.0)")
        order2 = order_shares('000002.SZ', 500, 15.0)
        assert order2 is not None
        print(f"  [返回值] {order2} [成功]")
        
        has_position2 = emutrader.portfolio.has_position('000002.SZ')
        print(f"  [持仓状态] {has_position2} (预期: True)")
        assert has_position2
    
    def test_order_value_compatibility(self):
        """测试order_value函数JQ兼容性"""
        print("\n=== 测试order_value函数JQ兼容性 ===")
        print("【测试内容】验证order_value函数是否完全兼容JQ API")
        print("【测试场景】按金额买入、带价格参数的按金额买入")
        
        emutrader = get_jq_account("test_strategy", 100000)
        set_current_context(emutrader)
        
        print("[记录初始状态]")
        # 记录初始状态
        initial_cash = emutrader.portfolio.available_cash
        print(f"  [初始可用资金] {initial_cash:,.2f}元")
        
        print("[测试基本调用 - 按金额买入]")
        # 测试基本调用
        print("  执行按金额买入: order_value('000001.SZ', 10000)")
        order = order_value('000001.SZ', 10000)
        assert order is not None
        print(f"  [返回值] {order} [成功]")
        
        print("[验证交易结果]")
        # 验证交易结果
        final_cash = emutrader.portfolio.available_cash
        print(f"  [交易后资金] {final_cash:,.2f}元 < {initial_cash:,.2f}元")
        assert final_cash < initial_cash
        
        has_position = emutrader.portfolio.has_position('000001.SZ')
        print(f"  [持仓状态] {has_position} (预期: True)")
        assert has_position
        
        position = emutrader.portfolio.get_position('000001.SZ')
        print(f"  [持仓价值] {position.value:,.2f}元 (> 0)")
        assert position.value > 0
        
        print("[测试带价格参数的调用]")
        # 测试带价格参数的调用
        print("  执行指定价格按金额买入: order_value('000002.SZ', 20000, 20.0)")
        order2 = order_value('000002.SZ', 20000, 20.0)
        assert order2 is not None
        print(f"  [返回值] {order2} [成功]")
        
        has_position2 = emutrader.portfolio.has_position('000002.SZ')
        print(f"  [持仓状态] {has_position2} (预期: True)")
        assert has_position2
    
    def test_order_target_percent_compatibility(self):
        """测试order_target_percent函数JQ兼容性"""
        print("\n=== 测试order_target_percent函数JQ兼容性 ===")
        print("【测试内容】验证order_target_percent函数是否完全兼容JQ API")
        print("【测试场景】按目标比例调仓、多股票目标比例")
        
        emutrader = get_jq_account("test_strategy", 100000)
        set_current_context(emutrader)
        
        print("[测试基本调用 - 目标比例20%]")
        # 测试基本调用
        print("  执行目标比例买入: order_target_percent('000001.SZ', 0.2)")
        order = order_target_percent('000001.SZ', 0.2)
        assert order is not None
        print(f"  [返回值] {order} [成功]")
        
        print("[验证交易结果]")
        # 验证交易结果
        has_position = emutrader.portfolio.has_position('000001.SZ')
        print(f"  [持仓状态] {has_position} (预期: True)")
        assert has_position
        
        position = emutrader.portfolio.get_position('000001.SZ')
        # 目标比例应该是总资产的20%左右
        total_value = emutrader.portfolio.total_value
        expected_value = total_value * 0.2
        actual_value = position.value
        
        print(f"  [总资产] {total_value:,.2f}元")
        print(f"  [目标价值] {expected_value:,.2f}元 (20%)")
        print(f"  [实际价值] {actual_value:,.2f}元")
        print(f"  [误差范围] 允许10%误差")
        
        tolerance = expected_value * 0.1  # 10%误差范围
        assert abs(actual_value - expected_value) < tolerance
        print(f"  [验证结果] 误差 {abs(actual_value - expected_value):,.2f}元 < {tolerance:,.2f}元 [成功]")
        
        print("[测试多个股票的目标比例]")
        # 测试多个股票的目标比例
        print("  执行第二只股票目标比例: order_target_percent('000002.SZ', 0.15)")
        order2 = order_target_percent('000002.SZ', 0.15)
        assert order2 is not None
        print(f"  [返回值] {order2} [成功]")
        
        has_position2 = emutrader.portfolio.has_position('000002.SZ')
        print(f"  [持仓状态] {has_position2} (预期: True)")
        assert has_position2
    
    def test_trading_function_return_values(self):
        """测试交易函数返回值兼容性"""
        print("\n=== 测试交易函数返回值兼容性 ===")
        print("【测试内容】验证所有JQ交易函数都有正确的返回值")
        print("【测试函数】order_shares、order_value、order_target_percent")
        
        emutrader = get_jq_account("test_strategy", 100000)
        set_current_context(emutrader)
        
        print("[测试所有交易函数都有返回值]")
        # 测试所有交易函数都有返回值
        print("  执行按数量买入: order_shares('000001.SZ', 1000)")
        order1 = order_shares('000001.SZ', 1000)
        
        print("  执行按金额买入: order_value('000002.SZ', 10000)")
        order2 = order_value('000002.SZ', 10000)
        
        print("  执行目标比例买入: order_target_percent('600519.SH', 0.1)")
        order3 = order_target_percent('600519.SH', 0.1)
        
        print("[验证返回值不为None]")
        # JQ API中交易函数返回Order对象或类似结构
        print(f"  [order_shares返回值] {order1} (不是None)")
        assert order1 is not None
        
        print(f"  [order_value返回值] {order2} (不是None)")
        assert order2 is not None
        
        print(f"  [order_target_percent返回值] {order3} (不是None)")
        assert order3 is not None
        
        print("[所有交易函数返回值验证成功] [成功]")


class TestJQSubportfolioSystem:
    """测试JQ子账户系统兼容性"""
    
    def test_set_subportfolios_compatibility(self):
        """测试set_subportfolios函数JQ兼容性"""
        print("\n=== 测试set_subportfolios函数JQ兼容性 ===")
        print("【测试内容】验证set_subportfolios函数是否完全兼容JQ API")
        print("【测试场景】单子账户设置、多子账户设置")
        
        emutrader = get_jq_account("test_strategy", 1000000)
        set_current_context(emutrader)
        
        print("[测试单子账户设置]")
        # 测试单子账户设置（资金必须匹配主账户）
        print("  创建单子账户配置: SubPortfolioConfig(cash=1000000, type='stock')")
        configs1 = [SubPortfolioConfig(cash=1000000, type='stock')]
        print("  执行设置子账户: set_subportfolios(configs1)")
        set_subportfolios(configs1)
        
        print(f"  [子账户数量] {len(emutrader.subportfolios)}个 (预期: 1)")
        assert len(emutrader.subportfolios) == 1
        
        print("[验证子账户资金分配]")
        # 验证子账户资金分配
        actual_cash = emutrader.subportfolios[0].available_cash
        print(f"  [子账户可用资金] {actual_cash:,}元 (预期: 1,000,000)")
        assert actual_cash == 1000000
        
        print("[测试多子账户设置]")
        # 测试多子账户设置 - 确保总金额匹配主账户
        print("  创建多子账户配置:")
        print("    子账户0: SubPortfolioConfig(cash=500000, type='stock')")
        print("    子账户1: SubPortfolioConfig(cash=300000, type='futures')")
        print("    子账户2: SubPortfolioConfig(cash=200000, type='index_futures')")
        
        configs2 = [
            SubPortfolioConfig(cash=500000, type='stock'),
            SubPortfolioConfig(cash=300000, type='futures'),
            SubPortfolioConfig(cash=200000, type='index_futures'),
        ]
        print("  执行设置子账户: set_subportfolios(configs2)")
        set_subportfolios(configs2)
        
        print(f"  [子账户数量] {len(emutrader.subportfolios)}个 (预期: 3)")
        assert len(emutrader.subportfolios) == 3
        
        print("[验证子账户类型和金额]")
        # 验证子账户类型和金额
        account_types = ['STOCK', 'FUTURE', 'INDEX_FUTURE']
        expected_cash = [500000, 300000, 200000]
        
        for i, sub in enumerate(emutrader.subportfolios):
            print(f"  [子账户{i}]")
            print(f"    [账户类型] {sub.type} (预期: {account_types[i]})")
            assert sub.type == account_types[i]
            print(f"    [可用资金] {sub.available_cash:,}元 (预期: {expected_cash[i]:,})")
            assert sub.available_cash == expected_cash[i]
    
    def test_subportfolio_jq_attributes(self):
        """测试子账户的JQ兼容属性"""
        print("\n=== 测试子账户的JQ兼容属性 ===")
        print("【测试内容】验证子账户SubPortfolio是否完全兼容JQ属性")
        print("【验证】子账户的6个核心JQ属性")
        
        emutrader = get_jq_account("test_strategy", 1000000)
        set_current_context(emutrader)
        
        print("[设置子账户]")
        # 设置子账户 - 确保总金额匹配主账户
        print("  创建子账户配置:")
        print("    子账户0: SubPortfolioConfig(cash=700000, type='stock')")
        print("    子账户1: SubPortfolioConfig(cash=300000, type='futures')")
        
        set_subportfolios([
            SubPortfolioConfig(cash=700000, type='stock'),
            SubPortfolioConfig(cash=300000, type='futures'),
        ])
        
        print("[验证每个子账户的JQ兼容属性]")
        # 验证每个子账户的JQ兼容属性
        for i, subportfolio in enumerate(emutrader.subportfolios):
            print(f"  [子账户{i}]")
            assert isinstance(subportfolio, SubPortfolio)
            print(f"    [实例类型] {type(subportfolio).__name__} [成功]")
            
            print("    [验证JQ标准属性]")
            # JQ标准属性
            jq_attrs = [
                'total_value', 'available_cash', 'market_value',
                'positions', 'pnl', 'returns'
            ]
            
            for attr in jq_attrs:
                assert hasattr(subportfolio, attr), f"SubPortfolio缺少JQ属性: {attr}"
                print(f"      [成功] {attr}: 存在")
            
            print("    [验证属性类型]")
            # 验证属性类型
            assert isinstance(subportfolio.total_value, float)
            print(f"      [total_value] {type(subportfolio.total_value).__name__} [成功]")
            
            assert isinstance(subportfolio.available_cash, float)
            print(f"      [available_cash] {type(subportfolio.available_cash).__name__} [成功]")
            
            assert isinstance(subportfolio.market_value, float)
            print(f"      [market_value] {type(subportfolio.market_value).__name__} [成功]")
            
            assert isinstance(subportfolio.positions, dict)
            print(f"      [positions] {type(subportfolio.positions).__name__} [成功]")
            
            assert isinstance(subportfolio.pnl, float)
            print(f"      [pnl] {type(subportfolio.pnl).__name__} [成功]")
            
            assert isinstance(subportfolio.returns, float)
            print(f"      [returns] {type(subportfolio.returns).__name__} [成功]")
    
    def test_transfer_cash_compatibility(self):
        """测试transfer_cash函数JQ兼容性"""
        print("\n=== 测试transfer_cash函数JQ兼容性 ===")
        print("【测试内容】验证transfer_cash函数是否完全兼容JQ API")
        print("【测试场景】正向转账、反向转账")
        
        emutrader = get_jq_account("test_strategy", 1000000)
        set_current_context(emutrader)
        
        print("[设置子账户]")
        set_subportfolios([
            SubPortfolioConfig(cash=600000, type='stock'),
            SubPortfolioConfig(cash=400000, type='futures'),
        ])
        
        print("[记录初始状态]")
        # 记录初始状态
        stock_sub = emutrader.subportfolios[0]
        futures_sub = emutrader.subportfolios[1]
        initial_stock_cash = stock_sub.available_cash
        initial_futures_cash = futures_sub.available_cash
        
        print(f"  [股票子账户初始资金] {initial_stock_cash:,}元")
        print(f"  [期货子账户初始资金] {initial_futures_cash:,}元")
        
        print("[执行转账 - 期货转股票]")
        # 执行转账
        transfer_amount = 100000
        print(f"  执行转账: transfer_cash(from_pindex=1, to_pindex=0, cash={transfer_amount})")
        success = transfer_cash(from_pindex=1, to_pindex=0, cash=transfer_amount)
        print(f"  [转账结果] {success} (预期: True)")
        assert success is True
        
        print("[验证转账结果]")
        # 验证转账结果
        expected_stock_cash = initial_stock_cash + transfer_amount
        expected_futures_cash = initial_futures_cash - transfer_amount
        
        print(f"  [股票子账户资金] {stock_sub.available_cash:,}元 (预期: {expected_stock_cash:,})")
        assert stock_sub.available_cash == expected_stock_cash
        
        print(f"  [期货子账户资金] {futures_sub.available_cash:,}元 (预期: {expected_futures_cash:,})")
        assert futures_sub.available_cash == expected_futures_cash
        
        print("[测试反向转账 - 股票转期货]")
        # 测试反向转账
        reverse_amount = 50000
        print(f"  执行反向转账: transfer_cash(from_pindex=0, to_pindex=1, cash={reverse_amount})")
        success2 = transfer_cash(from_pindex=0, to_pindex=1, cash=reverse_amount)
        print(f"  [转账结果] {success2} (预期: True)")
        assert success2 is True
        
        print("[验证反向转账结果]")
        final_stock_cash = initial_stock_cash + transfer_amount - reverse_amount
        final_futures_cash = initial_futures_cash - transfer_amount + reverse_amount
        
        print(f"  [股票子账户最终资金] {stock_sub.available_cash:,}元 (预期: {final_stock_cash:,})")
        assert stock_sub.available_cash == final_stock_cash
        
        print(f"  [期货子账户最终资金] {futures_sub.available_cash:,}元 (预期: {final_futures_cash:,})")
        assert futures_sub.available_cash == final_futures_cash
        
        print("[转账功能验证成功] [成功]")
    
    def test_transfer_cash_edge_cases(self):
        """测试资金转账边界情况"""
        print("\n=== 测试资金转账边界情况 ===")
        print("【测试内容】验证转账函数在各种边界情况下的处理")
        print("【测试场景】资金不足、无效索引等异常情况")
        
        emutrader = get_jq_account("test_strategy", 1000000)
        set_current_context(emutrader)
        
        print("[设置子账户]")
        set_subportfolios([
            SubPortfolioConfig(cash=600000, type='stock'),
            SubPortfolioConfig(cash=400000, type='futures'),
        ])
        
        print(f"  [股票子账户资金] {emutrader.subportfolios[0].available_cash:,}元")
        print(f"  [期货子账户资金] {emutrader.subportfolios[1].available_cash:,}元")
        
        print("[测试转账金额超过可用资金]")
        # 测试转账金额超过可用资金
        excess_amount = 700000
        print(f"  尝试超额转账: transfer_cash(from_pindex=0, to_pindex=1, cash={excess_amount})")
        print(f"  [可用资金] {emutrader.subportfolios[0].available_cash:,}元 < {excess_amount:,}元")
        
        success = transfer_cash(from_pindex=0, to_pindex=1, cash=excess_amount)
        print(f"  [转账结果] {success} (预期: False - 应该失败)")
        assert success is False  # 应该失败
        
        print("[验证资金未变化]")
        # 验证资金未变化
        stock_cash_after = emutrader.subportfolios[0].available_cash
        futures_cash_after = emutrader.subportfolios[1].available_cash
        
        print(f"  [股票子账户资金] {stock_cash_after:,}元 (预期: 600,000 - 未变化)")
        assert stock_cash_after == 600000
        
        print(f"  [期货子账户资金] {futures_cash_after:,}元 (预期: 400,000 - 未变化)")
        assert futures_cash_after == 400000
        
        print("[测试无效索引]")
        # 测试无效索引 - 应该返回False而不是抛出异常
        print("  测试from_pindex无效索引")
        try:
            success = transfer_cash(from_pindex=999, to_pindex=0, cash=1000)
            print(f"    [转账结果] {success} (预期: False)")
            assert success is False
        except ValueError as e:
            # 如果抛出异常也是合理的，说明索引无效
            print(f"    [抛出异常] ValueError: {e} [成功]")
            pass
        
        print("  测试to_pindex无效索引")
        try:
            success = transfer_cash(from_pindex=0, to_pindex=999, cash=1000)
            print(f"    [转账结果] {success} (预期: False)")
            assert success is False
        except ValueError as e:
            # 如果抛出异常也是合理的，说明索引无效
            print(f"    [抛出异常] ValueError: {e} [成功]")
            pass
        
        print("[边界情况测试完成] [成功]")


class TestJQOrderCostSystem:
    """测试JQ交易成本系统兼容性"""
    
    def test_set_order_cost_compatibility(self):
        """测试set_order_cost函数JQ兼容性"""
        print("\n=== 测试set_order_cost函数JQ兼容性 ===")
        print("【测试内容】验证set_order_cost函数是否完全兼容JQ API")
        print("【测试场景】设置股票交易成本、设置特定证券交易成本")
        
        emutrader = get_jq_account("test_strategy", 100000)
        
        print("[创建股票交易成本配置]")
        # 创建交易成本配置
        print("  创建股票成本配置: OrderCost(")
        print("    open_tax=0, close_tax=0.001,")
        print("    open_commission=0.0003, close_commission=0.0003,")
        print("    close_today_commission=0, min_commission=5")
        print("  )")
        
        stock_cost = OrderCost(
            open_tax=0,
            close_tax=0.001,
            open_commission=0.0003,
            close_commission=0.0003,
            close_today_commission=0,
            min_commission=5
        )
        
        print("[设置股票交易成本]")
        # 设置股票交易成本
        print("  执行设置: set_order_cost(stock_cost, type='stock')")
        set_order_cost(stock_cost, type='stock')
        
        print("[验证设置成功]")
        # 验证设置成功
        assert 'stock' in emutrader._order_costs
        print(f"  [成本类型存在] 'stock' in _order_costs [成功]")
        
        assert emutrader._order_costs['stock'] == stock_cost
        print(f"  [成本配置正确] emutrader._order_costs['stock'] == stock_cost [成功]")
        
        print("[设置特定证券的交易成本]")
        # 设置特定证券的交易成本
        print("  创建期货成本配置: OrderCost(")
        print("    open_tax=0, close_tax=0.0001,")
        print("    open_commission=0.0002, close_commission=0.0002,")
        print("    close_today_commission=0.0001, min_commission=1")
        print("  )")
        
        future_cost = OrderCost(
            open_tax=0,
            close_tax=0.0001,
            open_commission=0.0002,
            close_commission=0.0002,
            close_today_commission=0.0001,
            min_commission=1
        )
        
        print("  执行设置: set_order_cost(future_cost, type='futures', ref='IF2301')")
        set_order_cost(future_cost, type='futures', ref='IF2301')
        
        print("[验证特定证券成本设置]")
        # 验证特定证券成本设置
        assert 'IF2301' in emutrader._specific_order_costs
        print(f"  [特定证券存在] 'IF2301' in _specific_order_costs [成功]")
        
        assert emutrader._specific_order_costs['IF2301'] == future_cost
        print(f"  [特定成本正确] emutrader._specific_order_costs['IF2301'] == future_cost [成功]")
        
        print("[交易成本设置验证成功] [成功]")
    
    def test_order_cost_calculation_compatibility(self):
        """测试交易成本计算JQ兼容性"""
        print("\n=== 测试交易成本计算JQ兼容性 ===")
        print("【测试内容】验证交易成本计算是否完全兼容JQ API")
        print("【测试场景】买入成本计算、卖出成本计算")
        
        emutrader = get_jq_account("test_strategy", 100000)
        
        print("[设置股票交易成本]")
        # 设置股票交易成本
        print("  配置股票交易成本: OrderCost(")
        print("    open_tax=0, close_tax=0.001,")
        print("    open_commission=0.0003, close_commission=0.0003,")
        print("    close_today_commission=0, min_commission=5")
        print("  )")
        
        stock_cost = OrderCost(
            open_tax=0,
            close_tax=0.001,
            open_commission=0.0003,
            close_commission=0.0003,
            close_today_commission=0,
            min_commission=5
        )
        
        set_order_cost(stock_cost, type='stock')
        
        print("[测试买入成本计算]")
        # 测试买入成本计算
        security = '000001.SZ'
        amount = 1000
        price = 10.0
        trade_type = 'open'
        
        print(f"  买入参数: {security}, {amount}股, {price}元, {trade_type}")
        print(f"  交易价值 = {amount} * {price} = {amount * price}元")
        print(f"  佣金 = {amount * price} * 0.0003 = {amount * price * 0.0003}元")
        print(f"  印花税 = 0 (买入无印花税)")
        print(f"  最小佣金 = max({amount * price * 0.0003}, 5.0) = {max(amount * price * 0.0003, 5.0)}元")
        print(f"  总成本 = {max(amount * price * 0.0003, 5.0)} + 0 = {max(amount * price * 0.0003, 5.0)}元")
        
        total_cost, commission, tax = emutrader.calculate_trading_cost(
            security, amount, price, trade_type
        )
        
        print(f"  [计算结果] 总成本: {total_cost}元, 佣金: {commission}元, 印花税: {tax}元")
        print(f"  [预期结果] 总成本: 5.0元, 佣金: 5.0元, 印花税: 0.0元")
        
        assert total_cost == 5.0
        assert commission == 5.0
        assert tax == 0.0
        print("  [买入成本计算正确] [成功]")
        
        print("[测试卖出成本计算]")
        # 测试卖出成本计算
        trade_type = 'close'
        
        print(f"  卖出参数: {security}, {amount}股, {price}元, {trade_type}")
        print(f"  交易价值 = {amount} * {price} = {amount * price}元")
        print(f"  佣金 = {amount * price} * 0.0003 = {amount * price * 0.0003}元")
        print(f"  印花税 = {amount * price} * 0.001 = {amount * price * 0.001}元")
        print(f"  最小佣金 = max({amount * price * 0.0003}, 5.0) = {max(amount * price * 0.0003, 5.0)}元")
        print(f"  总成本 = {max(amount * price * 0.0003, 5.0)} + {amount * price * 0.001} = {max(amount * price * 0.0003, 5.0) + amount * price * 0.001}元")
        
        total_cost, commission, tax = emutrader.calculate_trading_cost(
            security, amount, price, trade_type
        )
        
        print(f"  [计算结果] 总成本: {total_cost}元, 佣金: {commission}元, 印花税: {tax}元")
        print(f"  [预期结果] 总成本: 15.0元, 佣金: 5.0元, 印花税: 10.0元")
        
        assert total_cost == 15.0
        assert commission == 5.0
        assert tax == 10.0
        print("  [卖出成本计算正确] [成功]")
        
        print("[交易成本计算验证成功] [成功]")


class TestJQWorkflowCompatibility:
    """测试完整的JQ工作流程兼容性"""
    
    def test_complete_jq_strategy_workflow(self):
        """测试完整的JQ策略工作流程"""
        print("\n=== 测试完整的JQ策略工作流程 ===")
        print("【测试内容】模拟完整的JQ策略运行流程")
        print("【测试步骤】创建上下文、设置子账户、执行交易、资金转移、验证结果")
        
        print("[步骤1: 创建策略上下文 - 与JQ完全相同]")
        # 1. 创建策略上下文 - 与JQ完全相同
        print("  创建策略: get_jq_account('完整测试', 1000000, 'STOCK')")
        context = get_jq_account("完整测试", 1000000, "STOCK")
        print("  设置当前上下文: set_current_context(context)")
        set_current_context(context)
        print("  设置子上下文: set_sub_context(context)")
        set_sub_context(context)
        
        print("[步骤2: 验证初始状态]")
        # 2. 验证初始状态
        print(f"  [总资产] {context.portfolio.total_value:,.2f}元 (预期: 1,000,000)")
        assert context.portfolio.total_value == 1000000.0
        
        print(f"  [可用资金] {context.portfolio.available_cash:,.2f}元 (预期: 1,000,000)")
        assert context.portfolio.available_cash == 1000000.0
        
        print(f"  [持仓市值] {context.portfolio.market_value:,.2f}元 (预期: 0)")
        assert context.portfolio.market_value == 0.0
        
        print(f"  [收益率] {context.portfolio.returns:.4f} (预期: 0)")
        assert context.portfolio.returns == 0.0
        
        print("[步骤3: 设置子账户]")
        # 3. 设置子账户
        print("  设置子账户配置:")
        print("    子账户0: SubPortfolioConfig(cash=600000, type='stock')")
        print("    子账户1: SubPortfolioConfig(cash=400000, type='futures')")
        
        set_subportfolios([
            SubPortfolioConfig(cash=600000, type='stock'),
            SubPortfolioConfig(cash=400000, type='futures'),
        ])
        
        print(f"  [子账户数量] {len(context.subportfolios)}个 (预期: 2)")
        assert len(context.subportfolios) == 2
        
        print("[步骤4: 执行交易 - JQ API]")
        # 4. 执行交易 - JQ API
        stock_pool = ['000001.SZ', '000002.SZ', '600519.SH', '000858.SZ']
        print(f"  [股票池] {stock_pool}")
        
        # 等权重投资
        target_percent = 0.6 / len(stock_pool)  # 60%资金投入股票
        print(f"  [目标比例] 每只股票占总资产的{target_percent:.2%} (总投入60%)")
        
        for security in stock_pool:
            print(f"    执行目标比例买入: order_target_percent('{security}', {target_percent})")
            order = order_target_percent(security, target_percent)
            assert order is not None
            print(f"      [返回值] {order} [成功]")
        
        print("[步骤5: 验证交易结果]")
        # 5. 验证交易结果
        portfolio = context.portfolio
        
        # 检查资金使用情况
        print(f"  [可用资金] {portfolio.available_cash:,.2f}元 < 1,000,000.0元")
        assert portfolio.available_cash < 1000000.0
        
        print(f"  [持仓市值] {portfolio.market_value:,.2f}元 (> 0)")
        assert portfolio.market_value > 0
        
        # 检查持仓
        positions = portfolio.positions
        print(f"  [持仓数量] {len(positions)}个 (预期: >= {len(stock_pool)})")
        assert len(positions) >= len(stock_pool)
        
        print("[验证各股票持仓权重]")
        for security in stock_pool:
            if security in positions:
                position = positions[security]
                print(f"    [{security}]")
                print(f"      [持仓数量] {position.total_amount}股 (> 0)")
                assert position.total_amount > 0
                
                print(f"      [持仓价值] {position.value:,.2f}元 (> 0)")
                assert position.value > 0
                
                weight = position.value / portfolio.total_value
                print(f"      [资产权重] {weight:.2%} (预期: 0.08-0.25之间)")
                # 由于价格和交易成本的影响，权重可能在0.08-0.25之间
                assert 0.08 < weight < 0.25
        
        print("[步骤6: 子账户资金转移]")
        # 6. 子账户资金转移
        print("  执行转账: transfer_cash(from_pindex=1, to_pindex=0, cash=100000)")
        success = transfer_cash(from_pindex=1, to_pindex=0, cash=100000)
        print(f"  [转账结果] {success} (预期: True)")
        assert success is True
        
        stock_sub = context.subportfolios[0]
        futures_sub = context.subportfolios[1]
        
        print(f"  [股票子账户可用资金] {stock_sub.available_cash:,.2f}元 (< 600,000 - 交易消耗)")
        # 由于股票子账户已经进行了交易，可用现金减少，但总价值增加
        assert stock_sub.available_cash < 600000  # 交易消耗了现金
        
        print(f"  [股票子账户总价值] {stock_sub.total_value:,.2f}元 (> 600,000 - 持仓增值)")
        assert stock_sub.total_value > 600000    # 但总价值增加了
        
        print(f"  [期货子账户可用资金] {futures_sub.available_cash:,.2f}元 (< 400,000 - 转出资金)")
        assert futures_sub.available_cash < 400000  # 期货子账户转出了资金
        
        print("[步骤7: 继续交易]")
        # 7. 继续交易
        print("  继续买入操作:")
        print("    order_shares('002415.SZ', 1000)")
        order_shares('002415.SZ', 1000)
        print("    order_value('600036.SH', 50000)")
        order_value('600036.SH', 50000)
        
        print("[步骤8: 验证最终状态]")
        # 8. 验证最终状态
        final_positions = len([p for p in portfolio.positions.values() 
                              if p.total_amount > 0])
        print(f"  [有效持仓数量] {final_positions}个 (预期: >= 4)")
        assert final_positions >= 4
        
        total_value_diff = abs(portfolio.total_value - 1000000.0)
        print(f"  [总资产偏差] {total_value_diff:,.2f}元 (预期: < 10,000)")
        assert total_value_diff < 10000
        
        print("[完整JQ策略工作流程测试成功] [成功]")
    
    def test_jq_strategy_simulation(self):
        """模拟真实JQ策略运行"""
        print("\n=== 模拟真实JQ策略运行 ===")
        print("【测试内容】模拟完整的JQ策略运行周期")
        print("【测试步骤】初始化、多日运行、调仓、结果验证")
        
        print("[定义策略函数 - 模拟JQ策略]")
        # 模拟JQ策略initialize函数
        def initialize(context):
            print("    [策略初始化] 设置股票池和参数")
            context.stocks = ['000001.SZ', '000002.SZ', '600519.SH']
            context.counter = 0
            context.rebalance_frequency = 3
            
            # 设置子账户
            print("    [策略初始化] 设置子账户")
            set_subportfolios([
                SubPortfolioConfig(cash=500000, type='stock'),
                SubPortfolioConfig(cash=300000, type='futures'),
            ])
        
        # 模拟JQ策略handle_data函数
        def handle_data(context, data):
            context.counter += 1
            print(f"    [第{context.counter}天] 处理市场数据")
            
            if context.counter % context.rebalance_frequency == 0:
                # 等权重调仓
                target_percent = 0.8 / len(context.stocks)
                print(f"      [调仓日] 等权重调仓，每只股票占比{target_percent:.1%}")
                for stock in context.stocks:
                    print(f"        调仓: {stock}")
                    order_target_percent(stock, target_percent)
        
        print("[创建策略上下文]")
        # 创建策略上下文
        emutrader = get_jq_account("jq_simulation", 800000, "STOCK")
        set_current_context(emutrader)
        
        print(f"  [策略名称] {emutrader.strategy_name}")
        print(f"  [初始资金] {emutrader.portfolio.total_value:,.2f}元")
        
        print("[初始化策略]")
        # 初始化策略
        initialize(emutrader)
        
        print("[验证初始化结果]")
        # 验证初始化结果
        assert hasattr(emutrader, 'stocks')
        print(f"  [股票池] {emutrader.stocks} [成功]")
        
        assert hasattr(emutrader, 'counter')
        print(f"  [计数器] 存在 [成功]")
        
        print(f"  [子账户数量] {len(emutrader.subportfolios)}个 (预期: 2)")
        assert len(emutrader.subportfolios) == 2
        
        print("[模拟多天运行]")
        # 模拟多天运行
        for day in range(10):
            print(f"  [第{day+1}天] 模拟市场数据")
            data = {}  # 模拟市场数据
            handle_data(emutrader, data)
            
            print(f"    [计数器] {emutrader.counter} (预期: {day+1})")
            assert emutrader.counter == day + 1
            
            # 调仓日验证
            if (day + 1) % 3 == 0:
                print(f"    [调仓日验证] 第{day+1}天是调仓日")
                positions = emutrader.portfolio.positions
                active_positions = len([p for p in positions.values() 
                                      if p.total_amount > 0])
                print(f"      [有效持仓] {active_positions}个 (预期: >= 1)")
                assert active_positions >= 1
        
        print("[验证最终结果]")
        # 验证最终结果
        final_portfolio = emutrader.portfolio
        print(f"  [最终总资产] {final_portfolio.total_value:,.2f}元 (预期: > 700,000)")
        assert final_portfolio.total_value > 700000
        
        print(f"  [最终持仓市值] {final_portfolio.market_value:,.2f}元 (> 0)")
        assert final_portfolio.market_value > 0
        
        print(f"  [总运行天数] {emutrader.counter}天 (预期: 10)")
        assert emutrader.counter == 10
        
        print("[JQ策略模拟运行测试成功] [成功]")


class TestJQCompatibilityEdgeCases:
    """测试JQ兼容性边界情况"""
    
    def test_empty_operations_compatibility(self):
        """测试空操作的JQ兼容性"""
        print("\n=== 测试空操作的JQ兼容性 ===")
        print("【测试内容】验证JQ API中对空操作的处理方式")
        print("【测试场景】获取不存在的持仓、空持仓列表")
        
        context = get_jq_account("edge_test", 100000)
        set_current_context(context)
        
        print("[测试获取不存在的持仓]")
        # 测试获取不存在的持仓
        print("  尝试获取不存在持仓: portfolio.get_position('999999.SZ')")
        position = context.portfolio.get_position('999999.SZ')
        print(f"  [返回类型] {type(position).__name__} (预期: Position)")
        assert isinstance(position, Position)
        
        print(f"  [持仓数量] {position.total_amount}股 (预期: 0 - JQ返回空持仓对象)")
        assert position.total_amount == 0  # JQ返回空持仓对象
        
        print("[测试空持仓列表]")
        # 测试空持仓列表
        print("  获取持仓字典: portfolio.positions")
        positions = context.portfolio.positions
        print(f"  [返回类型] {type(positions).__name__} (预期: dict)")
        assert isinstance(positions, dict)
        
        print(f"  [持仓数量] {len(positions)}个 (预期: 0)")
        assert len(positions) == 0
        
        print("[空操作兼容性验证成功] [成功]")
    
    def test_concurrent_contexts_compatibility(self):
        """测试多个策略上下文并存"""
        print("\n=== 测试多个策略上下文并存 ===")
        print("【测试内容】验证多个策略账户可以独立运行")
        print("【测试场景】创建不同类型和资金规模的策略账户")
        
        print("[创建多个策略]")
        # 创建多个策略
        print("  创建策略1: get_jq_account('strategy1', 100000, 'STOCK')")
        emutrader1 = get_jq_account("strategy1", 100000, "STOCK")
        
        print("  创建策略2: get_jq_account('strategy2', 200000, 'FUTURE')")
        emutrader2 = get_jq_account("strategy2", 200000, "FUTURE")
        
        print("  创建策略3: get_jq_account('strategy3', 150000, 'CREDIT')")
        emutrader3 = get_jq_account("strategy3", 150000, "CREDIT")
        
        print("[验证相互独立]")
        # 验证相互独立
        print(f"  [策略1总资产] {emutrader1.portfolio.total_value:,}元 (预期: 100,000)")
        assert emutrader1.portfolio.total_value == 100000
        
        print(f"  [策略2总资产] {emutrader2.portfolio.total_value:,}元 (预期: 200,000)")
        assert emutrader2.portfolio.total_value == 200000
        
        print(f"  [策略3总资产] {emutrader3.portfolio.total_value:,}元 (预期: 150,000)")
        assert emutrader3.portfolio.total_value == 150000
        
        print("[验证策略名称独立]")
        print(f"  [策略1名称] {emutrader1.strategy_name} (预期: strategy1)")
        assert emutrader1.strategy_name == "strategy1"
        
        print(f"  [策略2名称] {emutrader2.strategy_name} (预期: strategy2)")
        assert emutrader2.strategy_name == "strategy2"
        
        print(f"  [策略3名称] {emutrader3.strategy_name} (预期: strategy3)")
        assert emutrader3.strategy_name == "strategy3"
        
        print("[验证类型隔离]")
        # 验证类型隔离
        print(f"  [策略1账户类型] {emutrader1.account_type} (预期: STOCK)")
        assert emutrader1.account_type == "STOCK"
        
        print(f"  [策略2账户类型] {emutrader2.account_type} (预期: FUTURES)")
        assert emutrader2.account_type == "FUTURES"
        
        print(f"  [策略3账户类型] {emutrader3.account_type} (预期: STOCK - CREDIT映射到STOCK)")
        assert emutrader3.account_type == "STOCK"
        
        print("[多策略独立运行验证成功] [成功]")
    
    def test_trading_with_insufficient_cash(self):
        """测试资金不足时的交易处理"""
        print("\n=== 测试资金不足时的交易处理 ===")
        print("【测试内容】验证资金不足时交易函数的正确处理")
        print("【测试场景】尝试购买超过可用资金的股票")
        
        print("[创建低资金账户]")
        context = get_jq_account("cash_test", 1000)  # 只有1000元
        set_current_context(context)
        
        print(f"  [账户资金] {context.portfolio.available_cash:,}元 (仅有1000元)")
        
        print("[尝试超额购买]")
        # 尝试购买超过资金的股票
        purchase_amount = 100000  # 需要100000元
        print(f"  尝试购买: order_value('000001.SZ', {purchase_amount})")
        print(f"  [所需资金] {purchase_amount:,}元 > 可用资金 {context.portfolio.available_cash:,}元")
        
        order = order_value('000001.SZ', purchase_amount)
        print(f"  [返回值] {order}")
        
        print("[验证交易失败处理]")
        # 验证交易失败，资金未变化
        has_position = context.portfolio.has_position('000001.SZ')
        print(f"  [持仓状态] {has_position} (预期: False - 交易失败)")
        assert not has_position
        
        current_cash = context.portfolio.available_cash
        print(f"  [当前资金] {current_cash:,}元 (预期: 1,000 - 未变化)")
        assert current_cash == 1000.0
        
        print("[资金不足处理验证成功] [成功]")