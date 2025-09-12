"""
SubPortfolio 系统测试
测试子账户系统的创建、管理、资金转移等功能
"""

import pytest
from emutrader import (
    get_jq_account, set_subportfolios, SubPortfolioConfig, transfer_cash,
    SubPortfolio
)
from emutrader.api import set_current_context


class TestSubPortfolioConfig:
    """测试SubPortfolioConfig配置类"""
    
    @pytest.mark.subportfolio
    def test_subportfolio_config_creation(self):
        """测试SubPortfolioConfig创建"""
        # 基本配置
        config = SubPortfolioConfig(cash=100000, type='stock')
        
        assert config.cash == 100000
        assert config.type == 'stock'
        
        # 验证默认值
        assert hasattr(config, '__dict__')
    
    @pytest.mark.subportfolio
    def test_subportfolio_config_types(self):
        """测试各种账户类型配置"""
        account_types = [
            ('stock', 'STOCK'),
            ('futures', 'FUTURE'),
            ('index_futures', 'INDEX_FUTURE'),
            ('stock_margin', 'CREDIT'),
        ]
        
        for config_type, expected_type in account_types:
            config = SubPortfolioConfig(cash=50000, type=config_type)
            assert config.type == config_type
    
    @pytest.mark.subportfolio
    def test_subportfolio_config_validation(self):
        """测试SubPortfolioConfig参数验证"""
        # 有效配置
        valid_config = SubPortfolioConfig(cash=100000, type='stock')
        assert valid_config.cash == 100000
        
        # 测试不同资金额度
        configs = [
            SubPortfolioConfig(cash=1000, type='stock'),      # 小额
            SubPortfolioConfig(cash=1000000, type='futures'), # 大额
            SubPortfolioConfig(cash=0, type='credit'),        # 零资金
        ]
        
        for config in configs:
            assert config.cash >= 0
            assert config.type in ['stock', 'futures', 'index_futures', 'stock_margin', 'credit']


class TestSetSubportfolios:
    """测试set_subportfolios函数"""
    
    @pytest.mark.subportfolio
    def test_set_single_subportfolio(self):
        """测试设置单个子账户"""
        context = get_jq_account("single_sub_test", 100000)
        set_current_context(context)
        
        # 设置单个股票子账户
        configs = [SubPortfolioConfig(cash=100000, type='stock')]
        set_subportfolios(configs)
        
        # 验证子账户创建成功
        assert len(context.subportfolios) == 1
        subportfolio = context.subportfolios[0]
        
        assert isinstance(subportfolio, SubPortfolio)
        assert subportfolio.type == 'STOCK'
        assert subportfolio.available_cash == 100000
        assert subportfolio.total_value == 100000
        assert subportfolio.index == 0
    
    @pytest.mark.subportfolio
    def test_set_multiple_subportfolios(self):
        """测试设置多个子账户"""
        context = get_jq_account("multi_sub_test", 500000)
        set_current_context(context)
        
        # 设置多个不同类型的子账户
        configs = [
            SubPortfolioConfig(cash=200000, type='stock'),
            SubPortfolioConfig(cash=150000, type='futures'),
            SubPortfolioConfig(cash=100000, type='index_futures'),
            SubPortfolioConfig(cash=50000, type='stock_margin'),
        ]
        set_subportfolios(configs)
        
        # 验证所有子账户
        assert len(context.subportfolios) == 4
        
        expected_types = ['STOCK', 'FUTURE', 'INDEX_FUTURE', 'CREDIT']
        expected_cash = [200000, 150000, 100000, 50000]
        
        for i, (expected_type, expected_amount) in enumerate(zip(expected_types, expected_cash)):
            sub = context.subportfolios[i]
            assert sub.type == expected_type
            assert sub.available_cash == expected_amount
            assert sub.index == i
    
    @pytest.mark.subportfolio
    def test_set_subportfolios_replaces_existing(self):
        """测试重新设置子账户会替换现有子账户"""
        context = get_jq_account("replace_test", 300000)
        set_current_context(context)
        
        # 第一次设置
        initial_configs = [
            SubPortfolioConfig(cash=150000, type='stock'),
            SubPortfolioConfig(cash=150000, type='futures'),
        ]
        set_subportfolios(initial_configs)
        
        assert len(context.subportfolios) == 2
        
        # 第二次设置（应该替换）
        new_configs = [
            SubPortfolioConfig(cash=100000, type='stock'),
            SubPortfolioConfig(cash=100000, type='index_futures'),
            SubPortfolioConfig(cash=100000, type='stock_margin'),
        ]
        set_subportfolios(new_configs)
        
        # 验证被替换
        assert len(context.subportfolios) == 3
        assert context.subportfolios[0].type == 'STOCK'
        assert context.subportfolios[1].type == 'INDEX_FUTURE'
        assert context.subportfolios[2].type == 'CREDIT'
    
    @pytest.mark.subportfolio
    def test_set_subportfolios_cash_consistency(self):
        """测试子账户资金与主账户一致性"""
        initial_cash = 800000
        context = get_jq_account("consistency_test", initial_cash)
        set_current_context(context)
        
        # 设置子账户
        configs = [
            SubPortfolioConfig(cash=300000, type='stock'),
            SubPortfolioConfig(cash=250000, type='futures'),
            SubPortfolioConfig(cash=150000, type='index_futures'),
            SubPortfolioConfig(cash=100000, type='stock_margin'),
        ]
        set_subportfolios(configs)
        
        # 验证子账户总资金等于主账户
        total_sub_cash = sum(sub.available_cash for sub in context.subportfolios)
        assert total_sub_cash == initial_cash
        
        # 验证主账户Portfolio状态
        assert context.portfolio.total_value == initial_cash


class TestSubPortfolioObject:
    """测试SubPortfolio对象功能"""
    
    @pytest.mark.subportfolio
    def test_subportfolio_attributes(self):
        """测试SubPortfolio属性"""
        context = get_jq_account("attr_test", 100000)
        set_current_context(context)
        
        # 创建子账户
        configs = [SubPortfolioConfig(cash=100000, type='stock')]
        set_subportfolios(configs)
        
        subportfolio = context.subportfolios[0]
        
        # 验证JQ兼容属性
        jq_attributes = [
            'type', 'index', 'total_value', 'available_cash', 
            'market_value', 'positions', 'pnl', 'returns'
        ]
        
        for attr in jq_attributes:
            assert hasattr(subportfolio, attr), f"SubPortfolio缺少属性: {attr}"
        
        # 验证初始值
        assert subportfolio.type == 'STOCK'
        assert subportfolio.index == 0
        assert subportfolio.total_value == 100000
        assert subportfolio.available_cash == 100000
        assert subportfolio.market_value == 0
        assert isinstance(subportfolio.positions, dict)
        assert len(subportfolio.positions) == 0
        assert subportfolio.pnl == 0
        assert subportfolio.returns == 0
    
    @pytest.mark.subportfolio
    def test_subportfolio_methods(self):
        """测试SubPortfolio方法"""
        context = get_jq_account("methods_test", 200000)
        set_current_context(context)
        
        # 创建子账户
        configs = [
            SubPortfolioConfig(cash=120000, type='stock'),
            SubPortfolioConfig(cash=80000, type='futures'),
        ]
        set_subportfolios(configs)
        
        stock_sub = context.subportfolios[0]
        futures_sub = context.subportfolios[1]
        
        # 测试get_position方法
        position = stock_sub.get_position('000001.SZ')
        assert position.total_amount == 0  # 初始无持仓
        
        # 测试has_position方法
        assert stock_sub.has_position('000001.SZ') is False
        
        # 测试get_subportfolio_info方法
        info = stock_sub.get_subportfolio_info()
        assert isinstance(info, dict)
        assert info['type'] == 'STOCK'
        assert info['index'] == 0
        assert info['available_cash'] == 120000
    
    @pytest.mark.subportfolio
    def test_subportfolio_account_types(self):
        """测试各种账户类型的子账户"""
        context = get_jq_account("types_test", 400000)
        set_current_context(context)
        
        # 创建所有支持的账户类型
        configs = [
            SubPortfolioConfig(cash=100000, type='stock'),
            SubPortfolioConfig(cash=100000, type='futures'),
            SubPortfolioConfig(cash=100000, type='index_futures'),
            SubPortfolioConfig(cash=100000, type='stock_margin'),
        ]
        set_subportfolios(configs)
        
        expected_mappings = {
            0: 'STOCK',
            1: 'FUTURE',
            2: 'INDEX_FUTURE',
            3: 'CREDIT',
        }
        
        for i, expected_type in expected_mappings.items():
            sub = context.subportfolios[i]
            assert sub.type == expected_type
            assert sub.index == i
            assert sub.available_cash == 100000


class TestTransferCash:
    """测试transfer_cash资金转移功能"""
    
    @pytest.mark.subportfolio
    def test_basic_cash_transfer(self):
        """测试基本资金转移"""
        context = get_jq_account("transfer_test", 200000)
        set_current_context(context)
        
        # 设置子账户
        configs = [
            SubPortfolioConfig(cash=120000, type='stock'),
            SubPortfolioConfig(cash=80000, type='futures'),
        ]
        set_subportfolios(configs)
        
        stock_sub = context.subportfolios[0]
        futures_sub = context.subportfolios[1]
        
        # 记录转移前状态
        initial_stock_cash = stock_sub.available_cash
        initial_futures_cash = futures_sub.available_cash
        
        # 从期货账户转移20000到股票账户
        result = transfer_cash(from_pindex=1, to_pindex=0, cash=20000)
        
        # 验证转移成功
        assert result is True
        
        # 验证资金变化
        assert stock_sub.available_cash == initial_stock_cash + 20000  # 120000 + 20000 = 140000
        assert futures_sub.available_cash == initial_futures_cash - 20000  # 80000 - 20000 = 60000
        
        # 验证总资金不变
        total_cash = stock_sub.available_cash + futures_sub.available_cash
        assert total_cash == 200000
    
    @pytest.mark.subportfolio
    def test_transfer_cash_validation(self):
        """测试资金转移验证"""
        context = get_jq_account("validation_test", 150000)
        set_current_context(context)
        
        # 设置子账户
        configs = [
            SubPortfolioConfig(cash=100000, type='stock'),
            SubPortfolioConfig(cash=50000, type='futures'),
        ]
        set_subportfolios(configs)
        
        # 测试转移金额超过可用资金
        result = transfer_cash(from_pindex=1, to_pindex=0, cash=60000)  # 超过50000
        assert result is False
        
        # 验证资金未变化
        assert context.subportfolios[0].available_cash == 100000
        assert context.subportfolios[1].available_cash == 50000
        
        # 测试无效索引
        result = transfer_cash(from_pindex=5, to_pindex=0, cash=10000)
        assert result is False
        
        result = transfer_cash(from_pindex=0, to_pindex=5, cash=10000)
        assert result is False
        
        # 测试负金额
        result = transfer_cash(from_pindex=0, to_pindex=1, cash=-10000)
        assert result is False
        
        # 测试零金额
        result = transfer_cash(from_pindex=0, to_pindex=1, cash=0)
        assert result is False
        
        # 测试相同账户转移
        result = transfer_cash(from_pindex=0, to_pindex=0, cash=10000)
        assert result is False
    
    @pytest.mark.subportfolio
    def test_multiple_transfers(self):
        """测试多次资金转移"""
        context = get_jq_account("multiple_transfer_test", 300000)
        set_current_context(context)
        
        # 设置3个子账户
        configs = [
            SubPortfolioConfig(cash=150000, type='stock'),
            SubPortfolioConfig(cash=100000, type='futures'),
            SubPortfolioConfig(cash=50000, type='index_futures'),
        ]
        set_subportfolios(configs)
        
        # 执行多次转移
        transfers = [
            (0, 1, 30000),  # 股票 -> 期货
            (1, 2, 25000),  # 期货 -> 金融期货  
            (2, 0, 15000),  # 金融期货 -> 股票
        ]
        
        for from_idx, to_idx, amount in transfers:
            result = transfer_cash(from_pindex=from_idx, to_pindex=to_idx, cash=amount)
            assert result is True
        
        # 验证最终状态
        # 股票: 150000 - 30000 + 15000 = 135000
        # 期货: 100000 + 30000 - 25000 = 105000  
        # 金融期货: 50000 + 25000 - 15000 = 60000
        
        assert context.subportfolios[0].available_cash == 135000
        assert context.subportfolios[1].available_cash == 105000
        assert context.subportfolios[2].available_cash == 60000
        
        # 验证总资金守恒
        total_cash = sum(sub.available_cash for sub in context.subportfolios)
        assert total_cash == 300000
    
    @pytest.mark.subportfolio
    def test_transfer_with_trading(self):
        """测试转移资金后的交易功能"""
        context = get_jq_account("transfer_trading_test", 200000)
        set_current_context(context)
        
        # 设置子账户
        configs = [
            SubPortfolioConfig(cash=120000, type='stock'),
            SubPortfolioConfig(cash=80000, type='futures'),
        ]
        set_subportfolios(configs)
        
        # 转移资金增加股票账户资金
        transfer_cash(from_pindex=1, to_pindex=0, cash=30000)
        
        # 验证转移后状态
        stock_sub = context.subportfolios[0]
        futures_sub = context.subportfolios[1]
        
        assert stock_sub.available_cash == 150000  # 120000 + 30000
        assert futures_sub.available_cash == 50000  # 80000 - 30000
        
        # 后续可以集成交易测试（需要交易系统支持子账户）


class TestSubPortfolioIntegration:
    """测试SubPortfolio系统集成功能"""
    
    @pytest.mark.subportfolio
    def test_subportfolio_context_integration(self):
        """测试SubPortfolio与Context集成"""
        context = get_jq_account("context_integration", 500000)
        set_current_context(context)
        
        # 设置子账户
        configs = [
            SubPortfolioConfig(cash=200000, type='stock'),
            SubPortfolioConfig(cash=150000, type='futures'),
            SubPortfolioConfig(cash=100000, type='index_futures'),
            SubPortfolioConfig(cash=50000, type='stock_margin'),
        ]
        set_subportfolios(configs)
        
        # 验证Context正确管理子账户
        assert len(context.subportfolios) == 4
        
        # 验证Context方法与子账户交互
        sub0 = context.get_subportfolio(0)
        sub1 = context.get_subportfolio(1)
        
        assert sub0 is context.subportfolios[0]
        assert sub1 is context.subportfolios[1]
        assert sub0.type == 'STOCK'
        assert sub1.type == 'FUTURE'
        
        # 验证Context信息包含子账户信息
        context_info = context.get_context_info()
        assert context_info['subportfolios_count'] == 4
    
    @pytest.mark.subportfolio
    def test_subportfolio_portfolio_integration(self):
        """测试SubPortfolio与主Portfolio集成"""
        context = get_jq_account("portfolio_integration", 300000)
        set_current_context(context)
        
        # 设置子账户
        configs = [
            SubPortfolioConfig(cash=180000, type='stock'),
            SubPortfolioConfig(cash=120000, type='futures'),
        ]
        set_subportfolios(configs)
        
        # 验证主Portfolio状态
        portfolio = context.portfolio
        assert portfolio.total_value == 300000
        
        # 验证子账户资金分配不影响主Portfolio总值
        total_sub_value = sum(sub.total_value for sub in context.subportfolios)
        assert total_sub_value == portfolio.total_value
        
        # 转移资金后验证一致性
        transfer_cash(from_pindex=1, to_pindex=0, cash=50000)
        
        # 主Portfolio总值应保持不变
        assert portfolio.total_value == 300000
        
        # 子账户总值应保持不变
        updated_total_sub_value = sum(sub.total_value for sub in context.subportfolios)
        assert updated_total_sub_value == 300000


class TestSubPortfolioEdgeCases:
    """测试SubPortfolio边界情况"""
    
    @pytest.mark.subportfolio
    def test_zero_cash_subportfolio(self):
        """测试零资金子账户"""
        context = get_jq_account("zero_cash_test", 100000)
        set_current_context(context)
        
        # 创建零资金子账户
        configs = [
            SubPortfolioConfig(cash=100000, type='stock'),
            SubPortfolioConfig(cash=0, type='futures'),
        ]
        set_subportfolios(configs)
        
        # 验证零资金子账户正常创建
        assert len(context.subportfolios) == 2
        assert context.subportfolios[1].available_cash == 0
        assert context.subportfolios[1].total_value == 0
        
        # 测试向零资金账户转移资金
        result = transfer_cash(from_pindex=0, to_pindex=1, cash=20000)
        assert result is True
        
        assert context.subportfolios[0].available_cash == 80000
        assert context.subportfolios[1].available_cash == 20000
    
    @pytest.mark.subportfolio
    def test_large_number_of_subportfolios(self):
        """测试大量子账户"""
        context = get_jq_account("many_subs_test", 1000000)
        set_current_context(context)
        
        # 创建多个子账户
        num_subs = 50
        cash_per_sub = 1000000 // num_subs
        
        configs = []
        account_types = ['stock', 'futures', 'index_futures', 'stock_margin']
        
        for i in range(num_subs):
            account_type = account_types[i % len(account_types)]
            config = SubPortfolioConfig(cash=cash_per_sub, type=account_type)
            configs.append(config)
        
        set_subportfolios(configs)
        
        # 验证所有子账户创建成功
        assert len(context.subportfolios) == num_subs
        
        # 验证资金分配正确
        total_sub_cash = sum(sub.available_cash for sub in context.subportfolios)
        expected_total = cash_per_sub * num_subs
        assert abs(total_sub_cash - expected_total) < num_subs  # 允许整数除法误差
        
        # 测试批量转移
        for i in range(0, num_subs - 1, 2):
            transfer_cash(from_pindex=i, to_pindex=i + 1, cash=1000)
        
        # 验证转移后总资金不变
        final_total_cash = sum(sub.available_cash for sub in context.subportfolios)
        assert abs(final_total_cash - expected_total) < num_subs
    
    @pytest.mark.subportfolio
    def test_subportfolio_precision_handling(self):
        """测试子账户精度处理"""
        context = get_jq_account("precision_test", 100000.123456)
        set_current_context(context)
        
        # 设置带小数的子账户
        configs = [
            SubPortfolioConfig(cash=60000.654321, type='stock'),
            SubPortfolioConfig(cash=40000.469135, type='futures'),
        ]
        set_subportfolios(configs)
        
        # 验证精度保持
        stock_sub = context.subportfolios[0]
        futures_sub = context.subportfolios[1]
        
        assert isinstance(stock_sub.available_cash, float)
        assert isinstance(futures_sub.available_cash, float)
        
        # 测试小额转移的精度
        result = transfer_cash(from_pindex=0, to_pindex=1, cash=0.123456)
        assert result is True
        
        # 验证精度计算正确
        total_cash = stock_sub.available_cash + futures_sub.available_cash
        assert abs(total_cash - 100000.123456) < 1e-6


class TestSubPortfolioPerformance:
    """测试SubPortfolio性能"""
    
    @pytest.mark.subportfolio
    @pytest.mark.performance
    def test_subportfolio_creation_performance(self):
        """测试子账户创建性能"""
        import time
        
        context = get_jq_account("perf_test", 1000000)
        set_current_context(context)
        
        # 创建大量子账户配置
        num_subs = 100
        configs = []
        
        for i in range(num_subs):
            config = SubPortfolioConfig(cash=10000, type='stock')
            configs.append(config)
        
        # 测试创建性能
        start_time = time.time()
        set_subportfolios(configs)
        end_time = time.time()
        
        # 验证性能
        creation_time = end_time - start_time
        assert creation_time < 1.0  # 100个子账户创建应在1秒内
        
        # 验证创建结果
        assert len(context.subportfolios) == num_subs
        
        # 测试访问性能
        start_time = time.time()
        for i in range(num_subs):
            sub = context.get_subportfolio(i)
            assert sub is not None
        end_time = time.time()
        
        access_time = end_time - start_time
        assert access_time < 0.1  # 100次访问应在0.1秒内
    
    @pytest.mark.subportfolio
    @pytest.mark.performance
    def test_transfer_performance(self):
        """测试资金转移性能"""
        import time
        
        context = get_jq_account("transfer_perf", 1000000)
        set_current_context(context)
        
        # 创建10个子账户
        configs = [SubPortfolioConfig(cash=100000, type='stock') for _ in range(10)]
        set_subportfolios(configs)
        
        # 测试大量转移操作性能
        num_transfers = 1000
        
        start_time = time.time()
        
        for i in range(num_transfers):
            from_idx = i % 10
            to_idx = (i + 1) % 10
            transfer_cash(from_pindex=from_idx, to_pindex=to_idx, cash=100)
        
        end_time = time.time()
        
        # 验证性能
        total_time = end_time - start_time
        avg_time_ms = (total_time / num_transfers) * 1000
        
        assert avg_time_ms < 1.0  # 每次转移 < 1ms
        
        # 验证资金守恒
        total_cash = sum(sub.available_cash for sub in context.subportfolios)
        assert abs(total_cash - 1000000) < 1.0