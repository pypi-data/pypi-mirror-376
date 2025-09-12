"""
Portfolio 核心功能测试
测试投资组合对象的所有功能和JQ兼容性
"""

import pytest
from emutrader import get_jq_account, order_shares
from emutrader.core.portfolio import Portfolio
from emutrader.core.position import Position
from emutrader.api import set_current_context


class TestPortfolioCreation:
    """测试Portfolio创建和初始化"""
    
    @pytest.mark.portfolio
    def test_portfolio_creation_via_context(self):
        """测试通过Context创建Portfolio"""
        context = get_jq_account("portfolio_test", 200000, "STOCK")
        portfolio = context.portfolio
        
        # 验证Portfolio类型和基本属性
        assert isinstance(portfolio, Portfolio)
        assert portfolio.total_value == 200000.0
        assert portfolio.available_cash == 200000.0
        assert portfolio.locked_cash == 0.0
        assert portfolio.market_value == 0.0
        assert portfolio.pnl == 0.0
        assert portfolio.returns == 0.0
    
    @pytest.mark.portfolio
    def test_portfolio_direct_creation(self):
        """测试直接创建Portfolio"""
        portfolio = Portfolio(initial_cash=500000)
        
        # 验证直接创建的Portfolio
        assert isinstance(portfolio, Portfolio)
        assert portfolio.total_value == 500000.0
        assert portfolio.available_cash == 500000.0
        assert portfolio.market_value == 0.0
        
        # 验证positions字典初始化
        assert isinstance(portfolio.positions, dict)
        assert len(portfolio.positions) == 0
    
    @pytest.mark.portfolio
    def test_portfolio_with_different_initial_cash(self):
        """测试不同初始资金的Portfolio"""
        test_cases = [
            1000.0,      # 小额资金
            100000.0,    # 标准资金  
            1000000.0,   # 大额资金
            10000000.0,  # 超大资金
        ]
        
        for initial_cash in test_cases:
            portfolio = Portfolio(initial_cash=initial_cash)
            assert portfolio.total_value == initial_cash
            assert portfolio.available_cash == initial_cash
            assert portfolio.market_value == 0.0


class TestPortfolioAttributes:
    """测试Portfolio核心属性"""
    
    @pytest.mark.portfolio
    def test_portfolio_jq_standard_attributes(self):
        """测试Portfolio JQ标准属性"""
        portfolio = Portfolio(initial_cash=100000)
        
        # 验证所有JQ标准属性存在
        jq_attributes = [
            'total_value',      # 总资产
            'available_cash',   # 可用资金
            'locked_cash',      # 冻结资金  
            'market_value',     # 持仓市值
            'positions',        # 持仓字典
            'pnl',             # 当日盈亏
            'returns'          # 累计收益率
        ]
        
        for attr in jq_attributes:
            assert hasattr(portfolio, attr), f"Portfolio缺少JQ标准属性: {attr}"
            
        # 验证属性类型
        assert isinstance(portfolio.total_value, float)
        assert isinstance(portfolio.available_cash, float)
        assert isinstance(portfolio.locked_cash, float)
        assert isinstance(portfolio.market_value, float)
        assert isinstance(portfolio.positions, dict)
        assert isinstance(portfolio.pnl, float)
        assert isinstance(portfolio.returns, float)
    
    @pytest.mark.portfolio
    def test_portfolio_calculated_properties(self):
        """测试Portfolio计算属性"""
        portfolio = Portfolio(initial_cash=100000)
        
        # 初始状态验证
        assert portfolio.total_value == 100000.0
        assert portfolio.returns == 0.0  # 初始收益率为0
        
        # 模拟资金变化
        portfolio.available_cash = 80000.0
        portfolio.market_value = 25000.0
        
        # 验证total_value计算正确
        expected_total = portfolio.available_cash + portfolio.locked_cash + portfolio.market_value
        assert abs(portfolio.total_value - expected_total) < 0.01
        
        # 验证returns计算
        expected_returns = (portfolio.total_value - 100000.0) / 100000.0
        assert abs(portfolio.returns - expected_returns) < 0.001
    
    @pytest.mark.portfolio
    def test_portfolio_positions_dict(self):
        """测试Portfolio持仓字典"""
        context = get_jq_account("positions_test", 100000)
        portfolio = context.portfolio
        set_current_context(context)
        
        # 初始状态无持仓
        assert isinstance(portfolio.positions, dict)
        assert len(portfolio.positions) == 0
        
        # 添加持仓后验证
        order_shares('000001.SZ', 1000)
        order_shares('000002.SZ', 500)
        
        # 验证持仓字典更新
        positions = portfolio.positions
        assert len(positions) >= 2
        
        # 验证持仓对象类型
        for security, position in positions.items():
            assert isinstance(security, str)
            assert isinstance(position, Position)
            assert position.total_amount > 0


class TestPortfolioMethods:
    """测试Portfolio核心方法"""
    
    @pytest.mark.portfolio
    def test_get_position_method(self):
        """测试获取持仓方法"""
        context = get_jq_account("get_pos_test", 100000)
        portfolio = context.portfolio
        set_current_context(context)
        
        # 测试获取不存在的持仓
        position = portfolio.get_position('999999.SZ')
        assert isinstance(position, Position)
        assert position.total_amount == 0  # 空持仓
        
        # 创建持仓后测试
        order_shares('000001.SZ', 1000)
        
        position = portfolio.get_position('000001.SZ')
        assert isinstance(position, Position)
        assert position.total_amount == 1000
        assert position.avg_cost > 0
        assert position.value > 0
    
    @pytest.mark.portfolio
    def test_has_position_method(self):
        """测试检查持仓方法"""
        context = get_jq_account("has_pos_test", 100000)
        portfolio = context.portfolio
        set_current_context(context)
        
        # 初始无持仓
        assert portfolio.has_position('000001.SZ') is False
        assert portfolio.has_position('000002.SZ') is False
        
        # 创建持仓后测试
        order_shares('000001.SZ', 1000)
        
        assert portfolio.has_position('000001.SZ') is True
        assert portfolio.has_position('000002.SZ') is False
        
        # 添加更多持仓
        order_shares('000002.SZ', 500)
        order_shares('600519.SH', 100)
        
        assert portfolio.has_position('000002.SZ') is True
        assert portfolio.has_position('600519.SH') is True
        assert portfolio.has_position('999999.SZ') is False
    
    @pytest.mark.portfolio
    def test_get_position_count_method(self):
        """测试获取持仓数量方法"""
        context = get_jq_account("count_test", 100000)
        portfolio = context.portfolio
        set_current_context(context)
        
        # 初始持仓数量为0
        assert portfolio.get_position_count() == 0
        
        # 添加持仓并测试计数
        order_shares('000001.SZ', 1000)
        assert portfolio.get_position_count() == 1
        
        order_shares('000002.SZ', 500)
        assert portfolio.get_position_count() == 2
        
        order_shares('600519.SH', 200)
        assert portfolio.get_position_count() == 3
        
        # 验证只计算有效持仓（total_amount > 0）
        active_count = len([p for p in portfolio.positions.values() 
                           if p.total_amount > 0])
        assert portfolio.get_position_count() == active_count
    
    @pytest.mark.portfolio
    def test_get_portfolio_info_method(self):
        """测试获取组合信息方法"""
        context = get_jq_account("info_test", 150000)
        portfolio = context.portfolio
        set_current_context(context)
        
        # 获取初始信息
        info = portfolio.get_portfolio_info()
        
        # 验证返回结构
        assert isinstance(info, dict)
        expected_keys = [
            'total_value', 'available_cash', 'locked_cash', 'market_value',
            'positions_count', 'pnl', 'returns', 'cash_ratio', 'position_ratio'
        ]
        
        for key in expected_keys:
            assert key in info, f"缺少组合信息: {key}"
        
        # 验证初始值
        assert info['total_value'] == 150000.0
        assert info['available_cash'] == 150000.0
        assert info['positions_count'] == 0
        assert info['cash_ratio'] == 1.0  # 全部为现金
        assert info['position_ratio'] == 0.0  # 无持仓
        
        # 添加持仓后验证信息更新
        order_shares('000001.SZ', 1000)
        order_shares('000002.SZ', 500)
        
        updated_info = portfolio.get_portfolio_info()
        
        assert updated_info['positions_count'] >= 2
        assert updated_info['market_value'] > 0
        assert updated_info['cash_ratio'] < 1.0  # 现金比例减少
        assert updated_info['position_ratio'] > 0.0  # 有持仓比例


class TestPortfolioStateManagement:
    """测试Portfolio状态管理"""
    
    @pytest.mark.portfolio
    def test_portfolio_cash_management(self):
        """测试Portfolio现金管理"""
        portfolio = Portfolio(initial_cash=100000)
        
        # 测试冻结资金
        portfolio.freeze_cash(10000)
        assert portfolio.available_cash == 90000.0
        assert portfolio.locked_cash == 10000.0
        assert portfolio.total_value == 100000.0
        
        # 测试释放资金
        portfolio.unfreeze_cash(5000)
        assert portfolio.available_cash == 95000.0
        assert portfolio.locked_cash == 5000.0
        
        # 测试释放过多资金（边界情况）
        portfolio.unfreeze_cash(10000)  # 超过冻结金额
        assert portfolio.available_cash == 100000.0
        assert portfolio.locked_cash == 0.0
    
    @pytest.mark.portfolio
    def test_portfolio_position_management(self):
        """测试Portfolio持仓管理"""
        context = get_jq_account("pos_mgmt_test", 100000)
        portfolio = context.portfolio
        set_current_context(context)
        
        # 添加持仓
        order_shares('000001.SZ', 1000)
        
        # 验证持仓添加成功
        position = portfolio.get_position('000001.SZ')
        assert position.total_amount == 1000
        
        # 增加同一股票持仓
        order_shares('000001.SZ', 500)
        
        updated_position = portfolio.get_position('000001.SZ')
        assert updated_position.total_amount == 1500
        
        # 减少持仓
        order_shares('000001.SZ', -300)
        
        reduced_position = portfolio.get_position('000001.SZ')
        assert reduced_position.total_amount == 1200
    
    @pytest.mark.portfolio  
    def test_portfolio_pnl_calculation(self):
        """测试Portfolio盈亏计算"""
        context = get_jq_account("pnl_test", 100000)
        portfolio = context.portfolio
        set_current_context(context)
        
        # 初始盈亏为0
        assert portfolio.pnl == 0.0
        assert portfolio.returns == 0.0
        
        # 添加持仓
        order_shares('000001.SZ', 1000)
        
        # 获取持仓并模拟价格变化
        position = portfolio.get_position('000001.SZ')
        original_cost = position.avg_cost
        
        # 模拟价格上涨10%
        new_price = original_cost * 1.1
        position.update_price(new_price)
        
        # 重新计算portfolio状态
        portfolio._update_calculated_fields()
        
        # 验证盈亏计算
        expected_pnl = (new_price - original_cost) * 1000
        assert abs(portfolio.pnl - expected_pnl) < 1.0
        
        # 验证收益率计算
        expected_returns = expected_pnl / 100000.0
        assert abs(portfolio.returns - expected_returns) < 0.001


class TestPortfolioConsistency:
    """测试Portfolio数据一致性"""
    
    @pytest.mark.portfolio
    def test_portfolio_value_consistency(self):
        """测试Portfolio价值一致性"""
        context = get_jq_account("consistency_test", 200000)
        portfolio = context.portfolio
        set_current_context(context)
        
        # 验证初始状态一致性
        assert portfolio.total_value == portfolio.available_cash + portfolio.locked_cash + portfolio.market_value
        
        # 添加多个持仓
        securities = ['000001.SZ', '000002.SZ', '600519.SH', '000858.SZ']
        for security in securities:
            order_shares(security, 500)
        
        # 验证添加持仓后一致性
        calculated_total = portfolio.available_cash + portfolio.locked_cash + portfolio.market_value
        assert abs(portfolio.total_value - calculated_total) < 1.0
        
        # 验证持仓市值计算一致性
        positions_market_value = sum(pos.value for pos in portfolio.positions.values() 
                                   if pos.total_amount > 0)
        assert abs(portfolio.market_value - positions_market_value) < 1.0
    
    @pytest.mark.portfolio
    def test_portfolio_position_consistency(self):
        """测试Portfolio持仓一致性"""
        context = get_jq_account("pos_consistency", 100000)
        portfolio = context.portfolio
        set_current_context(context)
        
        # 添加持仓
        order_shares('000001.SZ', 1000)
        order_shares('000002.SZ', 500)
        
        # 验证持仓字典与方法返回一致性
        positions_dict = portfolio.positions
        
        for security in ['000001.SZ', '000002.SZ']:
            dict_position = positions_dict.get(security)
            method_position = portfolio.get_position(security)
            
            assert dict_position is method_position  # 应该是同一个对象
            assert portfolio.has_position(security) is True
        
        # 验证持仓计数一致性
        active_positions = len([p for p in positions_dict.values() if p.total_amount > 0])
        assert portfolio.get_position_count() == active_positions
    
    @pytest.mark.portfolio
    def test_portfolio_cash_flow_consistency(self):
        """测试Portfolio现金流一致性"""
        portfolio = Portfolio(initial_cash=100000)
        original_total = portfolio.total_value
        
        # 模拟交易现金流
        portfolio.available_cash -= 20000  # 买入股票
        portfolio.market_value += 20000   # 对应市值增加
        
        # 验证总价值保持一致
        assert abs(portfolio.total_value - original_total) < 0.01
        
        # 模拟卖出现金流
        portfolio.available_cash += 15000  # 卖出收入
        portfolio.market_value -= 15000   # 对应市值减少
        
        # 验证总价值仍保持一致
        assert abs(portfolio.total_value - original_total) < 0.01


class TestPortfolioEdgeCases:
    """测试Portfolio边界情况"""
    
    @pytest.mark.portfolio
    def test_portfolio_zero_cash(self):
        """测试零资金Portfolio"""
        portfolio = Portfolio(initial_cash=0.0)
        
        assert portfolio.total_value == 0.0
        assert portfolio.available_cash == 0.0
        assert portfolio.market_value == 0.0
        assert portfolio.returns == 0.0
    
    @pytest.mark.portfolio
    def test_portfolio_negative_scenarios(self):
        """测试负值场景处理"""
        portfolio = Portfolio(initial_cash=100000)
        
        # 模拟亏损情况
        portfolio.market_value = 50000  # 持仓市值
        portfolio.available_cash = 30000  # 可用现金
        
        # 总价值 = 30000 + 0 + 50000 = 80000
        # 收益率 = (80000 - 100000) / 100000 = -0.2
        assert portfolio.total_value == 80000.0
        assert portfolio.returns == -0.2
        assert portfolio.pnl == -20000.0
    
    @pytest.mark.portfolio
    def test_portfolio_large_positions(self):
        """测试大量持仓情况"""
        context = get_jq_account("large_pos_test", 1000000)
        portfolio = context.portfolio
        set_current_context(context)
        
        # 添加大量持仓
        num_positions = 100
        for i in range(num_positions):
            security = f"{i:06d}.SZ"
            order_shares(security, 100)
        
        # 验证大量持仓处理
        assert portfolio.get_position_count() >= num_positions * 0.9  # 允许部分失败
        assert len(portfolio.positions) >= num_positions * 0.9
        
        # 验证性能和一致性
        info = portfolio.get_portfolio_info()
        assert isinstance(info, dict)
        assert info['positions_count'] >= num_positions * 0.9
    
    @pytest.mark.portfolio
    def test_portfolio_precision_handling(self):
        """测试精度处理"""
        portfolio = Portfolio(initial_cash=100000.123456789)
        
        # 验证精度保持合理
        assert isinstance(portfolio.total_value, float)
        assert portfolio.total_value > 100000.12
        assert portfolio.total_value < 100000.13
        
        # 测试小额交易精度
        portfolio.available_cash = 99999.999999
        portfolio.market_value = 0.000001
        
        # 验证计算精度
        total = portfolio.total_value
        expected = portfolio.available_cash + portfolio.market_value
        assert abs(total - expected) < 1e-6


class TestPortfolioIntegration:
    """测试Portfolio与其他组件集成"""
    
    @pytest.mark.portfolio
    def test_portfolio_context_integration(self):
        """测试Portfolio与Context集成"""
        context = get_jq_account("integration", 100000)
        portfolio = context.portfolio
        
        # 验证Portfolio正确关联到Context
        assert context.portfolio is portfolio
        
        # 验证Context信息在Portfolio中可访问
        info = portfolio.get_portfolio_info()
        assert isinstance(info, dict)
    
    @pytest.mark.portfolio
    def test_portfolio_trading_integration(self):
        """测试Portfolio与交易系统集成"""
        context = get_jq_account("trading_integration", 100000)
        portfolio = context.portfolio
        set_current_context(context)
        
        # 记录交易前状态
        initial_cash = portfolio.available_cash
        initial_market_value = portfolio.market_value
        
        # 执行交易
        order_shares('000001.SZ', 1000)
        
        # 验证Portfolio状态更新
        assert portfolio.available_cash < initial_cash  # 现金减少
        assert portfolio.market_value > initial_market_value  # 市值增加
        assert portfolio.has_position('000001.SZ') is True
        
        # 验证总价值基本保持（考虑手续费）
        value_change = abs(portfolio.total_value - 100000.0)
        assert value_change < 500  # 允许手续费等成本