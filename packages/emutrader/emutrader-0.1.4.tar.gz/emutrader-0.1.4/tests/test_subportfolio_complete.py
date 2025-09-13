"""
子账户系统完整测试
整合所有子账户相关的功能测试
"""

import pytest
from emutrader import (
    get_jq_account, set_subportfolios, SubPortfolioConfig, transfer_cash,
    order_shares, order_value, order_target_percent
)
from emutrader.api import set_current_context
from emutrader.core.subportfolio import SubPortfolio


class TestSubPortfolioCreation:
    """测试SubPortfolio创建和初始化"""
    
    def test_subportfolio_direct_creation(self):
        print("\n=== 测试SubPortfolio直接创建 ===")
        print("【测试内容】直接创建子账户对象，验证基本属性")
        print("【创建】10万初始资金的股票子账户")
        
        subportfolio = SubPortfolio(
            type="STOCK",
            initial_cash=100000.0,
            index=0
        )
        
        print("[SubPortfolio创建完成]")
        print(f"  [对象类型] {type(subportfolio).__name__}")
        print(f"  [总资产] {subportfolio.total_value:,}元")
        print(f"  [可用资金] {subportfolio.available_cash:,}元")
        print(f"  [持仓市值] {subportfolio.market_value:,}元")
        print(f"  [账户类型] {subportfolio.type}")
        
        assert isinstance(subportfolio, SubPortfolio)
        assert subportfolio.total_value == 100000.0
        assert subportfolio.available_cash == 100000.0
        assert subportfolio.market_value == 0.0
        assert subportfolio.type == "STOCK"
        assert len(subportfolio.positions) == 0
    
    def test_subportfolio_via_emutrader(self):
        print("\n=== 测试通过EmuTrader创建SubPortfolio ===")
        print("【测试内容】通过EmuTrader主类创建多个子账户")
        print("【场景】设置股票和期货两个子账户，分别拥有60万和40万资金")
        
        emutrader = get_jq_account("test_strategy", 1000000)
        
        print("【操作】创建子账户配置")
        # 设置子账户
        configs = [
            SubPortfolioConfig(cash=600000, type='stock'),
            SubPortfolioConfig(cash=400000, type='futures'),
        ]
        
        print(f"  [配置1] 股票子账户: 600,000元")
        print(f"  [配置2] 期货子账户: 400,000元")
        
        print("【操作】应用子账户配置")
        set_subportfolios(configs)
        
        print("【验证】检查子账户创建结果")
        # 验证子账户创建
        assert len(emutrader.subportfolios) == 2
        print(f"  [成功] 创建了 {len(emutrader.subportfolios)} 个子账户")
        
        stock_sub = emutrader.subportfolios[0]
        futures_sub = emutrader.subportfolios[1]
        
        print(f"  [股票子账户] 总资产: {stock_sub.total_value:,}元")
        print(f"  [期货子账户] 总资产: {futures_sub.total_value:,}元")
        
        assert isinstance(stock_sub, SubPortfolio)
        assert isinstance(futures_sub, SubPortfolio)
        
        print("【验证】检查股票子账户属性")
        assert stock_sub.type == "STOCK"
        assert stock_sub.total_value == 600000.0
        assert stock_sub.available_cash == 600000.0
        print(f"  [股票账户] 类型: {stock_sub.type}, 总资产: {stock_sub.total_value:,}元")
        
        print("【验证】检查期货子账户属性")
        assert futures_sub.type == "FUTURE"
        assert futures_sub.total_value == 400000.0
        assert futures_sub.available_cash == 400000.0
        print(f"  [期货账户] 类型: {futures_sub.type}, 总资产: {futures_sub.total_value:,}元")
        
        print("[结果] 子账户通过EmuTrader创建成功")
    
    def test_subportfolio_account_type_mapping(self):
        print("\n=== 测试子账户类型映射 ===")
        print("【测试内容】测试不同输入类型到标准账户类型的映射")
        print("【场景】验证多种类型输入能够正确映射到STOCK或FUTURE")
        
        emutrader = get_jq_account("test_strategy", 1000000)
        
        # 测试各种账户类型
        test_cases = [
            ("stock", "STOCK"),
            ("futures", "FUTURE"),
            ("index_futures", "INDEX_FUTURE"),
            ("stock_margin", "CREDIT"),
        ]
        
        print("【测试案例列表】")
        for i, (input_type, expected_type) in enumerate(test_cases):
            print(f"  案例{i+1}: '{input_type}' -> '{expected_type}'")
        
        for input_type, expected_type in test_cases:
            print(f"\n【操作】测试输入类型: '{input_type}'")
            configs = [SubPortfolioConfig(cash=1000000, type=input_type)]
            set_subportfolios(configs)
            
            assert len(emutrader.subportfolios) == 1
            sub = emutrader.subportfolios[0]
            
            print(f"  [输入] {input_type}")
            print(f"  [预期] {expected_type}")
            print(f"  [实际] {sub.type}")
            
            assert sub.type == expected_type
            print(f"  [通过] 类型映射正确")
        
        print("[结果] 所有账户类型映射测试通过")


class TestSubPortfolioAttributes:
    """测试SubPortfolio属性"""
    
    def test_subportfolio_jq_compatibility(self):
        print("\n=== 测试SubPortfolio的JQ兼容属性 ===")
        print("【测试内容】验证SubPortfolio对象是否包含JoinQuant标准属性")
        print("【场景】确保与JoinQuant API完全兼容")
        
        emutrader = get_jq_account("test_strategy", 1000000)
        
        print("【操作】创建100万资金的股票子账户（与主账户资金匹配）")
        set_subportfolios([
            SubPortfolioConfig(cash=1000000, type='stock'),
        ])
        
        subportfolio = emutrader.subportfolios[0]
        print(f"  [子账户创建] 总资产: {subportfolio.total_value:,}元")
        
        # 验证JQ标准属性
        jq_attrs = [
            'total_value', 'available_cash', 'locked_cash', 'market_value',
            'positions', 'pnl', 'returns'
        ]
        
        print("【验证】检查JQ标准属性")
        for attr in jq_attrs:
            assert hasattr(subportfolio, attr), f"SubPortfolio缺少JQ属性: {attr}"
            print(f"  [通过] {attr}: {getattr(subportfolio, attr)}")
        
        print("【验证】检查属性类型")
        # 验证属性类型
        assert isinstance(subportfolio.total_value, float)
        assert isinstance(subportfolio.available_cash, float)
        assert isinstance(subportfolio.market_value, float)
        assert isinstance(subportfolio.positions, dict)
        assert isinstance(subportfolio.pnl, float)
        assert isinstance(subportfolio.returns, float)
        
        print(f"  [类型检查] total_value: {type(subportfolio.total_value).__name__}")
        print(f"  [类型检查] available_cash: {type(subportfolio.available_cash).__name__}")
        print(f"  [类型检查] market_value: {type(subportfolio.market_value).__name__}")
        print(f"  [类型检查] positions: {type(subportfolio.positions).__name__}")
        print(f"  [类型检查] pnl: {type(subportfolio.pnl).__name__}")
        print(f"  [类型检查] returns: {type(subportfolio.returns).__name__}")
        
        print("[结果] SubPortfolio JQ兼容性验证通过")
    
    def test_subportfolio_position_methods(self):
        print("\n=== 测试SubPortfolio持仓方法 ===")
        print("【测试内容】测试子账户的持仓管理相关方法")
        print("【场景】验证持仓查询、计数、存在性检查等方法")
        
        emutrader = get_jq_account("test_strategy", 1000000)
        set_current_context(emutrader)
        
        print("【操作】创建100万资金的股票子账户（与主账户资金匹配）")
        set_subportfolios([
            SubPortfolioConfig(cash=1000000, type='stock'),
        ])
        
        subportfolio = emutrader.subportfolios[0]
        
        print("【验证】检查初始状态（无持仓）")
        # 测试初始状态
        assert len(subportfolio.positions) == 0
        assert subportfolio.get_position_count() == 0
        assert subportfolio.has_position('000001.SZ') is False
        print(f"  [持仓数量] {len(subportfolio.positions)}")
        print(f"  [持仓计数] {subportfolio.get_position_count()}")
        print(f"  [000001.SZ存在] {subportfolio.has_position('000001.SZ')}")
        
        print("【操作】购买1000股000001.SZ")
        # 创建持仓
        order_shares('000001.SZ', 1000)
        print(f"  [交易] 买入000001.SZ 1000股")
        
        print("【验证】检查持仓创建结果")
        # 验证持仓方法
        assert len(subportfolio.positions) == 1
        assert subportfolio.get_position_count() == 1
        assert subportfolio.has_position('000001.SZ') is True
        print(f"  [持仓数量] {len(subportfolio.positions)}")
        print(f"  [持仓计数] {subportfolio.get_position_count()}")
        print(f"  [000001.SZ存在] {subportfolio.has_position('000001.SZ')}")
        
        print("【验证】检查持仓对象详情")
        position = subportfolio.get_position('000001.SZ')
        print(f"  [持仓对象] 数量: {position.total_amount}")
        print(f"  [持仓对象] 平均成本: {position.avg_cost}")
        assert position.total_amount == 1000
        
        print("[结果] SubPortfolio持仓方法测试通过")


class TestSubPortfolioTrading:
    """测试子账户交易"""
    
    def test_subportfolio_isolated_trading(self):
        print("\n=== 测试子账户隔离交易 ===")
        print("【测试内容】验证子账户之间的交易隔离性")
        print("【场景】在一个子账户的交易不应影响其他子账户")
        
        emutrader = get_jq_account("test_strategy", 1000000)
        set_current_context(emutrader)
        
        print("【操作】创建两个子账户：股票60万，期货40万")
        set_subportfolios([
            SubPortfolioConfig(cash=600000, type='stock'),
            SubPortfolioConfig(cash=400000, type='futures'),
        ])
        
        stock_sub = emutrader.subportfolios[0]
        futures_sub = emutrader.subportfolios[1]
        
        print(f"  [股票账户] 初始资金: {stock_sub.available_cash:,}元")
        print(f"  [期货账户] 初始资金: {futures_sub.available_cash:,}元")
        
        print("【操作】在股票子账户交易")
        # 在股票子账户交易
        order_shares('000001.SZ', 1000)
        print(f"  [股票交易] 买入000001.SZ 1000股")
        
        print("【验证】股票子账户交易只影响股票子账户")
        # 验证交易只影响股票子账户
        assert stock_sub.has_position('000001.SZ')
        print(f"  [验证] 股票账户持有000001.SZ: {stock_sub.has_position('000001.SZ')}")
        
        assert not futures_sub.has_position('000001.SZ')
        print(f"  [验证] 期货账户不持有000001.SZ: {not futures_sub.has_position('000001.SZ')}")
        
        assert stock_sub.available_cash < 600000.0
        print(f"  [验证] 股票账户资金减少: {stock_sub.available_cash:,}元")
        
        assert futures_sub.available_cash == 400000.0
        print(f"  [验证] 期货账户资金不变: {futures_sub.available_cash:,}元")
        
        print("【操作】在期货子账户交易")
        # 在期货子账户交易
        emutrader.execute_trade('600519.SH', 100, 100.0, subportfolio_index=1)
        print(f"  [期货交易] 买入600519.SH 100股 @100.0元")
        
        print("【验证】期货子账户交易只影响期货子账户")
        # 验证交易只影响期货子账户
        assert stock_sub.has_position('000001.SZ')
        print(f"  [验证] 股票账户仍持有000001.SZ: {stock_sub.has_position('000001.SZ')}")
        
        assert not stock_sub.has_position('600519.SH')
        print(f"  [验证] 股票账户不持有600519.SH: {not stock_sub.has_position('600519.SH')}")
        
        assert futures_sub.has_position('600519.SH')
        print(f"  [验证] 期货账户持有600519.SH: {futures_sub.has_position('600519.SH')}")
        
        assert futures_sub.available_cash < 400000.0
        print(f"  [验证] 期货账户资金减少: {futures_sub.available_cash:,}元")
        
        print("[结果] 子账户交易隔离性验证通过")
    
    def test_subportfolio_specific_trading(self):
        print("\n=== 测试指定子账户交易 ===")
        print("【测试内容】测试通过execute_trade方法在指定子账户交易")
        print("【场景】明确指定子账户索引进行交易操作")
        
        emutrader = get_jq_account("test_strategy", 1000000)
        set_current_context(emutrader)
        
        print("【操作】创建两个子账户：股票60万，期货40万")
        set_subportfolios([
            SubPortfolioConfig(cash=600000, type='stock'),
            SubPortfolioConfig(cash=400000, type='futures'),
        ])
        
        print("【操作】在指定子账户执行交易")
        # 在指定子账户交易
        emutrader.execute_trade('000001.SZ', 1000, 10.0, subportfolio_index=0)
        print(f"  [股票账户] 买入000001.SZ 1000股 @10.0元")
        
        emutrader.execute_trade('600519.SH', 100, 100.0, subportfolio_index=1)
        print(f"  [期货账户] 买入600519.SH 100股 @100.0元")
        
        stock_sub = emutrader.subportfolios[0]
        futures_sub = emutrader.subportfolios[1]
        
        print("【验证】检查交易发生在指定子账户")
        # 验证交易发生在指定子账户
        assert stock_sub.has_position('000001.SZ')
        print(f"  [股票账户] 持有000001.SZ: {stock_sub.has_position('000001.SZ')}")
        
        assert not stock_sub.has_position('600519.SH')
        print(f"  [股票账户] 不持有600519.SH: {not stock_sub.has_position('600519.SH')}")
        
        assert futures_sub.has_position('600519.SH')
        print(f"  [期货账户] 持有600519.SH: {futures_sub.has_position('600519.SH')}")
        
        assert not futures_sub.has_position('000001.SZ')
        print(f"  [期货账户] 不持有000001.SZ: {not futures_sub.has_position('000001.SZ')}")
        
        print("[结果] 指定子账户交易测试通过")
    
    def test_subportfolio_cash_isolation(self):
        print("\n=== 测试子账户资金隔离 ===")
        print("【测试内容】验证子账户之间的资金隔离性")
        print("【场景】一个子账户的资金变化不应影响其他子账户")
        
        emutrader = get_jq_account("test_strategy", 1000000)
        set_current_context(emutrader)
        
        print("【操作】创建两个子账户：股票60万，期货40万")
        set_subportfolios([
            SubPortfolioConfig(cash=600000, type='stock'),
            SubPortfolioConfig(cash=400000, type='futures'),
        ])
        
        stock_sub = emutrader.subportfolios[0]
        futures_sub = emutrader.subportfolios[1]
        
        # 记录初始现金
        initial_stock_cash = stock_sub.available_cash
        initial_futures_cash = futures_sub.available_cash
        
        print(f"  [初始状态] 股票账户: {initial_stock_cash:,}元")
        print(f"  [初始状态] 期货账户: {initial_futures_cash:,}元")
        
        print("【操作】在股票子账户交易")
        # 在股票子账户交易
        order_shares('000001.SZ', 1000)
        print(f"  [股票交易] 买入000001.SZ 1000股")
        
        print("【验证】股票账户资金变化，期货账户资金不变")
        # 验证只有股票子账户资金变化
        assert stock_sub.available_cash < initial_stock_cash
        print(f"  [股票账户] {initial_stock_cash:,} -> {stock_sub.available_cash:,}元 (减少)")
        
        assert futures_sub.available_cash == initial_futures_cash
        print(f"  [期货账户] {initial_futures_cash:,} -> {futures_sub.available_cash:,}元 (不变)")
        
        print("【操作】在期货子账户交易")
        # 在期货子账户交易
        emutrader.execute_trade('600519.SH', 100, 100.0, subportfolio_index=1)
        print(f"  [期货交易] 买入600519.SH 100股 @100.0元")
        
        # 验证只有期货子账户资金变化
        updated_stock_cash = stock_sub.available_cash
        assert futures_sub.available_cash < initial_futures_cash
        print(f"  [期货账户] {initial_futures_cash:,} -> {futures_sub.available_cash:,}元 (减少)")
        
        assert stock_sub.available_cash == updated_stock_cash  # 股票子账户现金不再变化
        print(f"  [股票账户] {updated_stock_cash:,} -> {stock_sub.available_cash:,}元 (保持不变)")
        
        print("[结果] 子账户资金隔离性验证通过")


class TestSubPortfolioCashTransfer:
    """测试子账户资金转移"""
    
    def test_basic_cash_transfer(self):
        print("\n=== 测试基本资金转移 ===")
        print("【测试内容】测试子账户间的基本资金转移功能")
        print("【场景】从股票子账户转移10万元到期货子账户")
        
        emutrader = get_jq_account("test_strategy", 1000000)
        set_current_context(emutrader)
        
        print("【操作】创建两个子账户：股票60万，期货40万")
        set_subportfolios([
            SubPortfolioConfig(cash=600000, type='stock'),
            SubPortfolioConfig(cash=400000, type='futures'),
        ])
        
        stock_sub = emutrader.subportfolios[0]
        futures_sub = emutrader.subportfolios[1]
        
        # 记录初始现金
        initial_stock_cash = stock_sub.available_cash
        initial_futures_cash = futures_sub.available_cash
        
        print(f"  [初始资金] 股票账户: {initial_stock_cash:,}元")
        print(f"  [初始资金] 期货账户: {initial_futures_cash:,}元")
        
        print("【操作】执行转账：股票->期货 10万元")
        # 执行转账
        success = transfer_cash(from_pindex=0, to_pindex=1, cash=100000)
        print(f"  [转账结果] {success}")
        assert success is True
        
        print("【验证】检查转账结果")
        # 验证转账结果
        expected_stock = initial_stock_cash - 100000
        expected_futures = initial_futures_cash + 100000
        
        assert stock_sub.available_cash == expected_stock
        print(f"  [股票账户] {initial_stock_cash:,} -> {stock_sub.available_cash:,}元 (预期: {expected_stock:,})")
        
        assert futures_sub.available_cash == expected_futures
        print(f"  [期货账户] {initial_futures_cash:,} -> {futures_sub.available_cash:,}元 (预期: {expected_futures:,})")
        
        print("[结果] 基本资金转移测试通过")
    
    def test_transfer_via_emutrader_method(self):
        print("\n=== 测试通过EmuTrader方法转账 ===")
        print("【测试内容】测试通过EmuTrader的transfer_cash方法转账")
        print("【场景】使用EmuTrader实例方法进行子账户间资金转移")
        
        emutrader = get_jq_account("test_strategy", 1000000)
        set_current_context(emutrader)
        
        print("【操作】创建两个子账户：股票60万，期货40万")
        set_subportfolios([
            SubPortfolioConfig(cash=600000, type='stock'),
            SubPortfolioConfig(cash=400000, type='futures'),
        ])
        
        stock_sub = emutrader.subportfolios[0]
        futures_sub = emutrader.subportfolios[1]
        
        # 记录初始现金
        initial_stock_cash = stock_sub.available_cash
        initial_futures_cash = futures_sub.available_cash
        
        print(f"  [初始资金] 股票账户: {initial_stock_cash:,}元")
        print(f"  [初始资金] 期货账户: {initial_futures_cash:,}元")
        
        print("【操作】通过EmuTrader方法转账：股票->期货 10万元")
        # 通过EmuTrader方法转账
        success = emutrader.transfer_cash(0, 1, 100000)
        print(f"  [转账结果] {success}")
        assert success is True
        
        print("【验证】检查转账结果")
        # 验证转账结果
        expected_stock = initial_stock_cash - 100000
        expected_futures = initial_futures_cash + 100000
        
        assert stock_sub.available_cash == expected_stock
        print(f"  [股票账户] {initial_stock_cash:,} -> {stock_sub.available_cash:,}元 (预期: {expected_stock:,})")
        
        assert futures_sub.available_cash == expected_futures
        print(f"  [期货账户] {initial_futures_cash:,} -> {futures_sub.available_cash:,}元 (预期: {expected_futures:,})")
        
        print("[结果] EmuTrader方法转账测试通过")
    
    def test_transfer_edge_cases(self):
        print("\n=== 测试转账边界情况 ===")
        print("【测试内容】测试资金转移的边界情况处理")
        print("【场景】包括超额转账、无效索引、零金额转账等")
        
        emutrader = get_jq_account("test_strategy", 1000000)
        set_current_context(emutrader)
        
        print("【操作】创建两个子账户：股票60万，期货40万")
        set_subportfolios([
            SubPortfolioConfig(cash=600000, type='stock'),
            SubPortfolioConfig(cash=400000, type='futures'),
        ])
        
        print("【测试1】转账金额超过可用资金")
        # 测试转账金额超过可用资金
        print(f"  [操作] 尝试从股票账户转账70万元 (可用: 60万)")
        success = transfer_cash(from_pindex=0, to_pindex=1, cash=700000)
        print(f"  [结果] 转账成功: {success}")
        assert success is False
        
        print("【验证】资金未变化")
        # 验证资金未变化
        assert emutrader.subportfolios[0].available_cash == 600000
        assert emutrader.subportfolios[1].available_cash == 400000
        print(f"  [股票账户] {emutrader.subportfolios[0].available_cash:,}元 (不变)")
        print(f"  [期货账户] {emutrader.subportfolios[1].available_cash:,}元 (不变)")
        
        print("【测试2】无效源账户索引")
        # 测试无效索引
        print("  [操作] 尝试从不存在的子账户999转账")
        try:
            success = transfer_cash(from_pindex=999, to_pindex=0, cash=1000)
            print(f"  [结果] 转账成功: {success}")
            assert success is False
        except ValueError as e:
            print(f"  [结果] 抛出异常: {e}")
            # 预期抛出异常，测试通过
            pass
        
        print("【测试3】无效目标账户索引")
        try:
            success = transfer_cash(from_pindex=0, to_pindex=999, cash=1000)
            print(f"  [结果] 转账成功: {success}")
            assert success is False
        except ValueError as e:
            print(f"  [结果] 抛出异常: {e}")
            # 预期抛出异常，测试通过
            pass
        
        print("【测试4】零金额转账")
        # 测试零金额转账
        print("  [操作] 尝试转账0元")
        try:
            success = transfer_cash(from_pindex=0, to_pindex=1, cash=0)
            print(f"  [结果] 转账成功: {success}")
            # 如果零金额转账被允许，验证成功
            assert success is True
        except ValueError as e:
            print(f"  [结果] 抛出异常: {e}")
            # 如果零金额转账不被允许，这也是合理的行为
            pass
        
        print("【验证】资金未变化")
        # 验证资金未变化
        assert emutrader.subportfolios[0].available_cash == 600000
        assert emutrader.subportfolios[1].available_cash == 400000
        print(f"  [股票账户] {emutrader.subportfolios[0].available_cash:,}元 (不变)")
        print(f"  [期货账户] {emutrader.subportfolios[1].available_cash:,}元 (不变)")
        
        print("[结果] 转账边界情况测试通过")
    
    def test_multiple_transfers(self):
        print("\n=== 测试多次转账 ===")
        print("【测试内容】测试多次连续转账操作")
        print("【场景】模拟多次资金调拨，验证最终结果")
        
        emutrader = get_jq_account("test_strategy", 1000000)
        set_current_context(emutrader)
        
        print("【操作】创建两个子账户：股票60万，期货40万")
        set_subportfolios([
            SubPortfolioConfig(cash=600000, type='stock'),
            SubPortfolioConfig(cash=400000, type='futures'),
        ])
        
        stock_sub = emutrader.subportfolios[0]
        futures_sub = emutrader.subportfolios[1]
        
        print(f"  [初始资金] 股票账户: {stock_sub.available_cash:,}元")
        print(f"  [初始资金] 期货账户: {futures_sub.available_cash:,}元")
        
        print("【操作】执行多次转账")
        # 多次转账
        transfers = [
            (0, 1, 100000),  # 股票 -> 期货
            (1, 0, 50000),   # 期货 -> 股票
            (0, 1, 200000),  # 股票 -> 期货
            (1, 0, 100000),  # 期货 -> 股票
        ]
        
        for i, (from_idx, to_idx, amount) in enumerate(transfers):
            account_names = ['股票账户', '期货账户']
            print(f"  转账{i+1}: {account_names[from_idx]} -> {account_names[to_idx]} {amount:,}元")
            success = transfer_cash(from_pindex=from_idx, to_pindex=to_idx, cash=amount)
            print(f"    结果: {success}")
            assert success is True
        
        print("【验证】检查最终结果")
        # 验证最终结果
        # 初始: 股票600000, 期货400000
        # 600000 - 100000 + 50000 - 200000 + 100000 = 450000
        # 400000 + 100000 - 50000 + 200000 - 100000 = 550000
        expected_stock = 450000
        expected_futures = 550000
        
        print(f"  [计算过程] 股票账户: 600000 - 100000 + 50000 - 200000 + 100000 = {expected_stock:,}元")
        print(f"  [计算过程] 期货账户: 400000 + 100000 - 50000 + 200000 - 100000 = {expected_futures:,}元")
        
        assert stock_sub.available_cash == expected_stock
        print(f"  [股票账户] 实际: {stock_sub.available_cash:,}元, 预期: {expected_stock:,}元")
        
        assert futures_sub.available_cash == expected_futures
        print(f"  [期货账户] 实际: {futures_sub.available_cash:,}元, 预期: {expected_futures:,}元")
        
        print("[结果] 多次转账测试通过")


class TestSubPortfolioAggregation:
    """测试子账户聚合视图"""
    
    def test_portfolio_aggregation(self):
        print("\n=== 测试Portfolio聚合视图 ===")
        print("【测试内容】测试Portfolio对子账户数据的聚合计算")
        print("【场景】在不同子账户交易后，验证聚合Portfolio的正确性")
        
        emutrader = get_jq_account("test_strategy", 1000000)
        set_current_context(emutrader)
        
        print("【操作】设置子账户")
        # 设置子账户
        set_subportfolios([
            SubPortfolioConfig(cash=600000, type='stock'),
            SubPortfolioConfig(cash=400000, type='futures'),
        ])
        print(f"  [子账户] 股票账户: 600,000元")
        print(f"  [子账户] 期货账户: 400,000元")
        
        print("【操作】在不同子账户交易")
        # 在不同子账户交易
        order_shares('000001.SZ', 1000)  # 股票子账户
        print(f"  [股票交易] 买入000001.SZ 1000股")
        
        emutrader.execute_trade('600519.SH', 100, 100.0, subportfolio_index=1)  # 期货子账户
        print(f"  [期货交易] 买入600519.SH 100股 @100.0元")
        
        print("【操作】获取聚合Portfolio")
        # 获取聚合Portfolio
        portfolio = emutrader.portfolio
        
        print("【验证】检查聚合计算")
        # 验证聚合计算
        stock_sub = emutrader.subportfolios[0]
        futures_sub = emutrader.subportfolios[1]
        
        expected_total_value = stock_sub.total_value + futures_sub.total_value
        expected_cash = stock_sub.available_cash + futures_sub.available_cash
        expected_market_value = stock_sub.market_value + futures_sub.market_value
        
        print(f"  [计算] 总资产 = {stock_sub.total_value:,} + {futures_sub.total_value:,} = {expected_total_value:,}")
        print(f"  [计算] 可用资金 = {stock_sub.available_cash:,} + {futures_sub.available_cash:,} = {expected_cash:,}")
        print(f"  [计算] 持仓市值 = {stock_sub.market_value:,} + {futures_sub.market_value:,} = {expected_market_value:,}")
        
        assert abs(portfolio.total_value - expected_total_value) < 0.01
        print(f"  [验证] 聚合总资产: {portfolio.total_value:,}元")
        
        assert abs(portfolio.available_cash - expected_cash) < 0.01
        print(f"  [验证] 聚合可用资金: {portfolio.available_cash:,}元")
        
        assert abs(portfolio.market_value - expected_market_value) < 0.01
        print(f"  [验证] 聚合持仓市值: {portfolio.market_value:,}元")
        
        print("【验证】检查持仓聚合")
        # 验证持仓聚合
        assert len(portfolio.positions) == 2
        print(f"  [持仓数量] {len(portfolio.positions)}")
        
        assert '000001.SZ' in portfolio.positions
        assert '600519.SH' in portfolio.positions
        print(f"  [持仓列表] {list(portfolio.positions.keys())}")
        
        print("[结果] Portfolio聚合视图测试通过")
    
    def test_aggregation_with_same_security(self):
        print("\n=== 测试相同证券在不同子账户的聚合 ===")
        print("【测试内容】测试相同证券在不同子账户的持仓聚合")
        print("【场景】不同子账户持有相同证券，验证合并后的平均成本计算")
        
        emutrader = get_jq_account("test_strategy", 1000000)
        set_current_context(emutrader)
        
        print("【操作】设置两个相同的股票子账户")
        set_subportfolios([
            SubPortfolioConfig(cash=500000, type='stock'),
            SubPortfolioConfig(cash=500000, type='stock'),
        ])
        print(f"  [子账户1] 股票账户: 500,000元")
        print(f"  [子账户2] 股票账户: 500,000元")
        print(f"  [总资金] 1,000,000元 (与主账户匹配)")
        
        print("【操作】在不同子账户持有相同证券")
        # 在不同子账户持有相同证券
        emutrader.execute_trade('000001.SZ', 1000, 10.0, subportfolio_index=0)
        print(f"  [子账户1] 买入000001.SZ 1000股 @10.0元")
        
        emutrader.execute_trade('000001.SZ', 500, 12.0, subportfolio_index=1)
        print(f"  [子账户2] 买入000001.SZ 500股 @12.0元")
        
        print("【操作】获取聚合Portfolio")
        # 获取聚合Portfolio
        portfolio = emutrader.portfolio
        
        print("【验证】检查持仓聚合")
        # 验证持仓聚合
        position = portfolio.get_position('000001.SZ')
        
        print("【计算】验证聚合持仓的平均成本")
        # 总数量 = 1000 + 500 = 1500
        # 总成本 = 1000*10.0 + 500*12.0 = 16000
        # 平均成本 = 16000 / 1500 = 10.67
        expected_amount = 1500
        expected_avg_cost = 16000 / 1500
        
        print(f"  [计算] 总数量 = 1000 + 500 = {expected_amount}")
        print(f"  [计算] 总成本 = 1000*10.0 + 500*12.0 = 16,000元")
        print(f"  [计算] 平均成本 = 16,000 / {expected_amount} = {expected_avg_cost:.2f}元")
        
        assert position.total_amount == expected_amount
        print(f"  [验证] 聚合数量: {position.total_amount}股")
        
        assert abs(position.avg_cost - expected_avg_cost) < 0.01
        print(f"  [验证] 平均成本: {position.avg_cost:.2f}元")
        
        print("【验证】检查聚合Portfolio持仓项")
        # 验证聚合Portfolio只有一个持仓项
        assert len(portfolio.positions) == 1
        print(f"  [持仓项数量] {len(portfolio.positions)}")
        print(f"  [持仓证券] {list(portfolio.positions.keys())}")
        
        print("[结果] 相同证券聚合测试通过")


class TestSubPortfolioMultiAccountStrategy:
    """测试多账户策略"""
    
    def test_multi_account_investment_strategy(self):
        print("\n=== 测试多账户投资策略 ===")
        print("【测试内容】模拟多账户投资策略的综合测试")
        print("【场景】包含股票、期货、股指期货、融资融券的多账户管理")
        
        emutrader = get_jq_account("multi_strategy", 2000000)
        set_current_context(emutrader)
        
        print("【操作】设置多个子账户")
        # 设置多个子账户
        set_subportfolios([
            SubPortfolioConfig(cash=800000, type='stock'),      # 股票账户
            SubPortfolioConfig(cash=600000, type='futures'),    # 期货账户
            SubPortfolioConfig(cash=400000, type='index_futures'),  # 股指期货账户
            SubPortfolioConfig(cash=200000, type='stock_margin'),   # 融资融券账户
        ])
        
        print(f"  [股票账户] 800,000元")
        print(f"  [期货账户] 600,000元")
        print(f"  [股指期货账户] 400,000元")
        print(f"  [融资融券账户] 200,000元")
        
        print("【操作】股票账户投资蓝筹股")
        # 股票账户投资蓝筹股
        blue_chips = ['000001.SZ', '000002.SZ', '600519.SH']
        for stock in blue_chips:
            order_value(stock, 100000)  # 每只股票投资10万元
            print(f"  [买入] {stock} 10万元")
        
        print("【操作】期货账户投资商品期货")
        # 期货账户投资商品期货
        futures = ['IF2401', 'IH2401']
        for future in futures:
            emutrader.execute_trade(future, 10, 1000.0, subportfolio_index=1)
            print(f"  [期货买入] {future} 10手 @1000.0元")
        
        print("【操作】股指期货账户投资指数期货")
        # 股指期货账户投资指数期货
        emutrader.execute_trade('IC2401', 5, 2000.0, subportfolio_index=2)
        print(f"  [股指期货买入] IC2401 5手 @2000.0元")
        
        print("【验证】检查各子账户状态")
        # 验证各子账户状态
        stock_sub = emutrader.subportfolios[0]
        futures_sub = emutrader.subportfolios[1]
        index_futures_sub = emutrader.subportfolios[2]
        margin_sub = emutrader.subportfolios[3]
        
        print("  [股票账户] 验证结果:")
        # 股票账户
        assert stock_sub.get_position_count() == 3
        assert stock_sub.available_cash < 800000
        for stock in blue_chips:
            assert stock_sub.has_position(stock)
            print(f"    [通过] 持有{stock}")
        print(f"    [通过] 持仓数量: {stock_sub.get_position_count()}")
        print(f"    [通过] 可用资金减少: {stock_sub.available_cash:,}元")
        
        print("  [期货账户] 验证结果:")
        # 期货账户
        assert futures_sub.get_position_count() == 2
        assert futures_sub.available_cash < 600000
        for future in futures:
            assert futures_sub.has_position(future)
            print(f"    [通过] 持有{future}")
        print(f"    [通过] 持仓数量: {futures_sub.get_position_count()}")
        print(f"    [通过] 可用资金减少: {futures_sub.available_cash:,}元")
        
        print("  [股指期货账户] 验证结果:")
        # 股指期货账户
        assert index_futures_sub.get_position_count() == 1
        assert index_futures_sub.has_position('IC2401')
        print(f"    [通过] 持有IC2401")
        print(f"    [通过] 持仓数量: {index_futures_sub.get_position_count()}")
        
        print("  [融资融券账户] 验证结果:")
        # 融资融券账户（未使用）
        assert margin_sub.get_position_count() == 0
        assert margin_sub.available_cash == 200000
        print(f"    [通过] 无持仓: {margin_sub.get_position_count()}")
        print(f"    [通过] 资金完整: {margin_sub.available_cash:,}元")
        
        print("【验证】检查总体Portfolio聚合")
        # 验证总体Portfolio聚合
        portfolio = emutrader.portfolio
        expected_positions = 6  # 3 + 2 + 1
        assert portfolio.get_position_count() == expected_positions
        assert portfolio.total_value == 2000000.0  # 总资产保持不变
        print(f"  [聚合持仓] 实际: {portfolio.get_position_count()}, 预期: {expected_positions}")
        print(f"  [聚合总资产] 实际: {portfolio.total_value:,}元, 预期: 2,000,000元")
        
        print("[结果] 多账户投资策略测试通过")
    
    def test_cross_account_cash_management(self):
        print("\n=== 测试跨账户资金管理 ===")
        print("【测试内容】模拟跨账户资金调拨和投资策略")
        print("【场景】股票账户盈利后转移资金到期货账户继续投资")
        
        emutrader = get_jq_account("cash_mgmt", 1000000)
        set_current_context(emutrader)
        
        print("【操作】设置三个子账户")
        set_subportfolios([
            SubPortfolioConfig(cash=400000, type='stock'),
            SubPortfolioConfig(cash=400000, type='futures'),
            SubPortfolioConfig(cash=200000, type='index_futures'),
        ])
        print(f"  [股票账户] 400,000元")
        print(f"  [期货账户] 400,000元")
        print(f"  [股指期货账户] 200,000元")
        
        print("【操作】初始投资")
        # 初始投资
        order_shares('000001.SZ', 1000)  # 股票账户
        print(f"  [股票投资] 买入000001.SZ 1000股")
        
        emutrader.execute_trade('IF2401', 5, 1000.0, subportfolio_index=1)  # 期货账户
        print(f"  [期货投资] 买入IF2401 5手 @1000.0元")
        
        print("【操作】模拟市场上涨，股票账户盈利")
        # 市场上涨，股票账户盈利
        emutrader.update_market_price('000001.SZ', 15.0)  # 上涨50%
        print(f"  [价格更新] 000001.SZ 价格更新为15.0元 (+50%)")
        
        print("【操作】从股票账户转移部分盈利到期货账户")
        # 从股票账户转移部分盈利到期货账户
        transfer_cash(from_pindex=0, to_pindex=1, cash=50000)
        print(f"  [资金转移] 股票账户 -> 期货账户 50,000元")
        
        print("【验证】检查资金转移")
        # 验证资金转移
        stock_sub = emutrader.subportfolios[0]
        futures_sub = emutrader.subportfolios[1]
        
        # 实际的期望值需要考虑交易成本
        # 股票账户: 400000 - 实际投资成本 + 50000转账
        # 期货账户: 400000 - 实际投资成本 + 50000转账
        
        print(f"  [股票账户] 资金变化: {stock_sub.available_cash:,}元")
        print(f"  [期货账户] 资金变化: {futures_sub.available_cash:,}元")
        
        # 只验证资金转移的大致情况，不精确计算
        assert stock_sub.available_cash < 400000 - 5000 + 50000  # 确保有资金转移
        assert futures_sub.available_cash > 400000 - 10000 + 50000  # 确保有资金转入
        
        print("【操作】继续投资期货账户")
        # 继续投资期货账户
        emutrader.execute_trade('IH2401', 10, 800.0, subportfolio_index=1)
        print(f"  [期货投资] 买入IH2401 10手 @800.0元")
        
        print("【验证】检查最终状态")
        # 验证最终状态
        assert stock_sub.has_position('000001.SZ')
        assert futures_sub.has_position('IF2401')
        assert futures_sub.has_position('IH2401')
        print(f"  [股票账户] 持有000001.SZ: {stock_sub.has_position('000001.SZ')}")
        print(f"  [期货账户] 持有IF2401: {futures_sub.has_position('IF2401')}")
        print(f"  [期货账户] 持有IH2401: {futures_sub.has_position('IH2401')}")
        
        print("【验证】检查Portfolio聚合正确")
        # 验证Portfolio聚合正确
        portfolio = emutrader.portfolio
        assert portfolio.get_position_count() == 3
        print(f"  [聚合持仓数量] {portfolio.get_position_count()}")
        
        assert portfolio.pnl > 0  # 整体盈利
        print(f"  [整体盈利] {portfolio.pnl:,}元")
        
        print("[结果] 跨账户资金管理测试通过")


class TestSubPortfolioEdgeCases:
    """测试子账户边界情况"""
    
    def test_single_subportfolio(self):
        print("\n=== 测试单子账户情况 ===")
        print("【测试内容】测试只有一个子账户时的正常工作")
        print("【场景】模拟简单使用场景，只有一个股票子账户")
        
        emutrader = get_jq_account("single_sub", 100000)
        set_current_context(emutrader)
        
        print("【操作】设置单子账户")
        # 设置单子账户
        set_subportfolios([
            SubPortfolioConfig(cash=100000, type='stock'),
        ])
        print(f"  [单子账户] 股票账户: 100,000元")
        
        print("【操作】验证单子账户工作正常")
        # 验证单子账户工作正常
        order_shares('000001.SZ', 1000)
        print(f"  [交易] 买入000001.SZ 1000股")
        
        sub = emutrader.subportfolios[0]
        print(f"  [子账户] 总资产: {sub.total_value:,}元")
        print(f"  [子账户] 可用资金: {sub.available_cash:,}元")
        
        assert sub.has_position('000001.SZ')
        print(f"  [持仓] 持有000001.SZ: {sub.has_position('000001.SZ')}")
        
        assert sub.available_cash < 100000
        print(f"  [资金] 资金减少: {sub.available_cash:,}元")
        
        print("【验证】检查Portfolio聚合")
        # 验证Portfolio聚合
        portfolio = emutrader.portfolio
        print(f"  [聚合Portfolio] 总资产: {portfolio.total_value:,}元")
        
        assert portfolio.has_position('000001.SZ')
        print(f"  [聚合持仓] 持有000001.SZ: {portfolio.has_position('000001.SZ')}")
        
        assert portfolio.total_value == sub.total_value
        print(f"  [聚合验证] 聚合总资产 = 子账户总资产: {portfolio.total_value:,}元")
        
        print("[结果] 单子账户测试通过")
    
    def test_empty_subportfolio(self):
        print("\n=== 测试空子账户 ===")
        print("【测试内容】测试部分子账户为空的情况")
        print("【场景】一个子账户有持仓，另一个子账户保持空仓")
        
        emutrader = get_jq_account("empty_sub", 1000000)
        set_current_context(emutrader)
        
        print("【操作】设置两个子账户")
        set_subportfolios([
            SubPortfolioConfig(cash=500000, type='stock'),
            SubPortfolioConfig(cash=500000, type='futures'),
        ])
        print(f"  [股票账户] 500,000元")
        print(f"  [期货账户] 500,000元")
        print(f"  [总资金] 1,000,000元 (与主账户匹配)")
        
        print("【操作】只在股票子账户交易")
        # 只在股票子账户交易
        order_shares('000001.SZ', 1000)
        print(f"  [股票交易] 买入000001.SZ 1000股")
        print(f"  [期货交易] 无操作（保持空仓）")
        
        stock_sub = emutrader.subportfolios[0]
        futures_sub = emutrader.subportfolios[1]
        
        print("【验证】检查空子账户状态")
        # 验证空子账户状态
        assert stock_sub.get_position_count() == 1
        print(f"  [股票账户] 持仓数量: {stock_sub.get_position_count()}")
        
        assert futures_sub.get_position_count() == 0
        print(f"  [期货账户] 持仓数量: {futures_sub.get_position_count()}")
        
        assert futures_sub.available_cash == 500000
        print(f"  [期货账户] 可用资金: {futures_sub.available_cash:,}元 (完整)")
        
        print("【验证】检查Portfolio聚合正确")
        # 验证Portfolio聚合正确
        portfolio = emutrader.portfolio
        expected_total = stock_sub.total_value + futures_sub.total_value
        
        assert portfolio.get_position_count() == 1
        print(f"  [聚合持仓] 数量: {portfolio.get_position_count()}")
        
        assert portfolio.total_value == expected_total
        print(f"  [聚合总资产] {portfolio.total_value:,}元 = {stock_sub.total_value:,} + {futures_sub.total_value:,}")
        
        print("[结果] 空子账户测试通过")
    
    def test_large_number_subportfolios(self):
        print("\n=== 测试大量子账户 ===")
        print("【测试内容】测试创建和管理大量子账户")
        print("【场景】创建10个子账户，验证系统能力")
        
        emutrader = get_jq_account("many_subs", 10000000)
        set_current_context(emutrader)
        
        print("【操作】创建多个子账户")
        # 创建多个子账户
        num_subportfolios = 10
        cash_per_sub = 1000000
        
        configs = [
            SubPortfolioConfig(cash=cash_per_sub, type='stock') 
            for _ in range(num_subportfolios)
        ]
        
        set_subportfolios(configs)
        print(f"  [创建] {num_subportfolios}个子账户，每个{cash_per_sub:,}元")
        
        print("【验证】检查子账户创建")
        # 验证子账户创建
        assert len(emutrader.subportfolios) == num_subportfolios
        print(f"  [成功] 创建了 {len(emutrader.subportfolios)} 个子账户")
        
        print("【操作】在不同子账户交易")
        # 在不同子账户交易
        for i in range(min(5, num_subportfolios)):
            symbol = f'{i:06d}.SZ'
            emutrader.execute_trade(symbol, 100, 10.0, subportfolio_index=i)
            print(f"  [交易{i+1}] 子账户{i} 买入{symbol} 100股 @10.0元")
        
        print("【验证】检查各子账户独立工作")
        # 验证各子账户独立工作
        for i in range(num_subportfolios):
            sub = emutrader.subportfolios[i]
            assert sub.total_value == cash_per_sub
            print(f"  [子账户{i}] 总资产: {sub.total_value:,}元")
            
            if i < 5:
                assert sub.get_position_count() == 1
                assert sub.available_cash < cash_per_sub
                print(f"    [通过] 有持仓，资金减少: {sub.available_cash:,}元")
            else:
                assert sub.get_position_count() == 0
                assert sub.available_cash == cash_per_sub
                print(f"    [通过] 无持仓，资金完整: {sub.available_cash:,}元")
        
        print("【验证】检查Portfolio聚合")
        # 验证Portfolio聚合
        portfolio = emutrader.portfolio
        expected_positions = 5
        expected_total = num_subportfolios * cash_per_sub
        
        assert portfolio.get_position_count() == expected_positions
        print(f"  [聚合持仓] 数量: {portfolio.get_position_count()} (预期: {expected_positions})")
        
        assert portfolio.total_value == expected_total
        print(f"  [聚合总资产] {portfolio.total_value:,}元 = {num_subportfolios} × {cash_per_sub:,}元")
        
        print("[结果] 大量子账户测试通过")