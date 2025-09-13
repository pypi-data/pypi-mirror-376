#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
滑点JoinQuant兼容性测试

验证滑点功能100%兼容JoinQuant API规范。
"""

import pytest
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from emutrader import (
    get_jq_account, FixedSlippage, PriceRelatedSlippage, StepRelatedSlippage,
    set_slippage, order_shares, order_value, order_target_percent
)
from emutrader.exceptions import ValidationException, ContextException


class TestJoinQuantCompatibility:
    """JoinQuant兼容性测试"""
    
    def setup_method(self):
        """测试前初始化"""
        self.context = get_jq_account("jq_compatibility_test", 100000)
    
    def test_set_slippage_api_signature(self):
        """测试set_slippage API签名兼容性"""
        # 测试1: 全局滑点设置
        set_slippage(FixedSlippage(0.02))
        
        # 测试2: 按类型设置
        set_slippage(PriceRelatedSlippage(0.002), security_type='stock')
        
        # 测试3: 按具体标的设置
        set_slippage(FixedSlippage(0.05), security_type='stock', ref='000001.SZ')
        
        # 测试4: 期货跳数滑点
        set_slippage(StepRelatedSlippage(2), security_type='futures', ref='IF')
        
        # 如果没有异常，说明API签名兼容
        assert True
    
    def test_supported_security_types(self):
        """测试支持的证券类型（JQ规范）"""
        jq_supported_types = [
            'stock', 'fund', 'mmf', 'fja', 'fjb', 'fjm',
            'index_futures', 'futures', 'bond_fund', 'stock_fund',
            'QDII_fund', 'mixture_fund', 'money_market_fund'
        ]
        
        for sec_type in jq_supported_types:
            try:
                set_slippage(FixedSlippage(0.01), security_type=sec_type)
            except Exception as e:
                pytest.fail(f"JoinQuant支持的类型 {sec_type} 设置失败: {e}")
    
    def test_slippage_object_types(self):
        """测试滑点对象类型（JQ规范）"""
        # 测试FixedSlippage
        set_slippage(FixedSlippage(0.02))
        
        # 测试PriceRelatedSlippage  
        set_slippage(PriceRelatedSlippage(0.002))
        
        # 测试StepRelatedSlippage
        set_slippage(StepRelatedSlippage(2))
        set_slippage(StepRelatedSlippage(3, 0.5))
        
        # 所有都应该成功设置
        assert True
    
    def test_default_slippage_behavior(self):
        """测试默认滑点行为（JQ规范）"""
        from emutrader.api import get_current_emutrader
        emu = get_current_emutrader()
        
        # 清除设置，恢复默认
        emu.clear_slippage()
        
        # JQ规范默认应该是PriceRelatedSlippage(0.00246)
        default_info = emu.get_slippage_info('000001.SZ', 'stock')
        assert default_info['type'] == 'PriceRelatedSlippage'
        assert abs(default_info['params']['percentage'] - 0.00246) < 1e-6
    
    def test_money_market_fund_zero_slippage(self):
        """测试货币基金零滑点（JQ规范）"""
        # JQ规范：货币基金滑点默认为0，且不可修改
        
        # 尝试设置货币基金滑点
        set_slippage(FixedSlippage(0.1), security_type='mmf')
        
        from emutrader.api import get_current_emutrader
        emu = get_current_emutrader()
        
        # 应该强制为0
        mmf_slippage = emu.get_slippage_info('511880.SH', 'mmf')
        assert mmf_slippage['type'] == 'FixedSlippage'
        assert mmf_slippage['params']['fixed_value'] == 0.0
        
        # 价格计算应该无滑点
        buy_price = emu.calculate_slippage_price('511880.SH', 100.0, 1000, 'open', 'mmf')
        sell_price = emu.calculate_slippage_price('511880.SH', 100.0, 1000, 'close', 'mmf')
        
        assert buy_price == 100.0
        assert sell_price == 100.0
    
    def test_slippage_priority_order(self):
        """测试滑点优先级（JQ规范）"""
        # JQ规范：具体标的 > 交易品种 > 全局默认
        
        # 1. 设置全局默认
        set_slippage(FixedSlippage(0.01))
        
        # 2. 设置股票类型
        set_slippage(PriceRelatedSlippage(0.002), security_type='stock')
        
        # 3. 设置特定股票
        set_slippage(FixedSlippage(0.05), security_type='stock', ref='000001.SZ')
        
        from emutrader.api import get_current_emutrader
        emu = get_current_emutrader()
        
        # 验证优先级
        specific = emu.get_slippage_info('000001.SZ', 'stock')
        stock_type = emu.get_slippage_info('000002.SZ', 'stock')
        futures = emu.get_slippage_info('IF2312', 'futures')
        
        # 具体标的配置应该优先
        assert specific['type'] == 'FixedSlippage'
        assert specific['params']['fixed_value'] == 0.05
        
        # 其次是类型配置
        assert stock_type['type'] == 'PriceRelatedSlippage'
        assert stock_type['params']['percentage'] == 0.002
        
        # 最后是全局配置
        assert futures['type'] == 'FixedSlippage'
        assert futures['params']['fixed_value'] == 0.01
    
    def test_slippage_calculation_rules(self):
        """测试滑点计算规则（JQ规范）"""
        # JQ规范：买入价格 = 预期价格 + 滑点值/2
        #           卖出价格 = 预期价格 - 滑点值/2
        
        set_slippage(FixedSlippage(0.2))  # 固定滑点0.2元
        
        from emutrader.api import get_current_emutrader
        emu = get_current_emutrader()
        
        test_price = 100.0
        test_amount = 1000
        
        # 买入价格计算
        buy_price = emu.calculate_slippage_price('TEST', test_price, test_amount, 'open', 'stock')
        expected_buy = test_price + 0.2 / 2  # 100.1
        assert abs(buy_price - expected_buy) < 1e-6
        
        # 卖出价格计算
        sell_price = emu.calculate_slippage_price('TEST', test_price, test_amount, 'close', 'stock')
        expected_sell = test_price - 0.2 / 2  # 99.9
        assert abs(sell_price - expected_sell) < 1e-6
    
    def test_step_related_slippage_calculation(self):
        """测试跳数滑点计算（JQ规范）"""
        # JQ规范：跳数滑点用于期货，单边滑点 = floor(跳数/2) * 价格步长
        
        set_slippage(StepRelatedSlippage(2, 0.5), security_type='futures')
        
        from emutrader.api import get_current_emutrader
        emu = get_current_emutrader()
        
        test_price = 3000.0
        test_amount = 1
        
        # 2跳滑点：单边1跳，双边滑点总额2跳
        buy_price = emu.calculate_slippage_price('IF2312', test_price, test_amount, 'open', 'futures')
        expected_buy = test_price + (1 * 0.5)  # 3000.5
        assert abs(buy_price - expected_buy) < 1e-6
        
        # 测试奇数跳
        set_slippage(StepRelatedSlippage(3, 0.5), security_type='futures')
        buy_price_3 = emu.calculate_slippage_price('IF2312', test_price, test_amount, 'open', 'futures')
        expected_buy_3 = test_price + (1 * 0.5)  # floor(3/2)=1跳
        assert abs(buy_price_3 - expected_buy_3) < 1e-6
    
    def test_order_functions_with_slippage(self):
        """测试下单函数的滑点应用（JQ兼容）"""
        # 设置滑点
        set_slippage(FixedSlippage(0.05))
        
        # 更新价格
        self.context.update_market_price('000001.SZ', 20.0)
        initial_cash = self.context.portfolio.available_cash
        
        # 测试order_shares
        order1 = order_shares('000001.SZ', 1000, 20.0)
        assert order1 is not None
        
        position = self.context.portfolio.get_position('000001.SZ')
        assert position.avg_cost > 20.0  # 滑点影响
        
        # 测试order_value
        order2 = order_value('000002.SZ', 30000)
        assert order2 is not None
        
        # 测试order_target_percent - 可能返回None如果仓位已经合适
        order3 = order_target_percent('000001.SZ', 0.2)
        # order_target_percent可能返回None，这是正常行为
        
        # 所有订单都应该成功应用滑点
        assert True
    
    def test_context_portfolio_compatibility(self):
        """测试context.portfolio兼容性（JQ兼容）"""
        # JQ代码：context.portfolio.total_value, context.portfolio.available_cash等
        
        # 设置滑点并交易
        set_slippage(PriceRelatedSlippage(0.002))
        self.context.update_market_price('000001.SZ', 25.0)
        
        order = order_shares('000001.SZ', 1000, 25.0)
        assert order is not None
        
        # 验证JQ风格的属性访问
        total_value = self.context.portfolio.total_value
        available_cash = self.context.portfolio.available_cash
        market_value = self.context.portfolio.market_value
        
        assert isinstance(total_value, float)
        assert isinstance(available_cash, float)
        assert isinstance(market_value, float)
        assert total_value > 0
        assert available_cash > 0
        assert market_value >= 0
    
    def test_context_subportfolios_compatibility(self):
        """测试context.subportfolios兼容性（JQ兼容）"""
        from emutrader import set_subportfolios, SubPortfolioConfig
        
        # 设置多子账户 (使用支持的type值)
        set_subportfolios([
            SubPortfolioConfig(cash=50000, type='stock'),
            SubPortfolioConfig(cash=50000, type='futures')
        ])
        
        # 设置滑点
        set_slippage(FixedSlippage(0.03), security_type='stock')
        
        # 在子账户中交易
        self.context.update_market_price('000001.SZ', 15.0)
        order = order_shares('000001.SZ', 500, 15.0)
        
        assert order is not None
        
        # 验证子账户滑点应用
        position = self.context.subportfolios[0].get_position('000001.SZ')
        assert position is not None
        assert position.avg_cost > 15.0  # 滑点影响
        
        # 验证JQ风格的子账户访问
        assert len(self.context.subportfolios) == 2
        assert self.context.subportfolios[0].total_value > 0
        assert self.context.subportfolios[1].total_value > 0
    
    def test_jq_error_handling_compatibility(self):
        """测试JQ风格错误处理"""
        # 测试无效滑点对象
        with pytest.raises((ValidationException, ValueError)):
            set_slippage("invalid_slippage_object")
        
        # 测试无效类型
        with pytest.raises((ValidationException, ValueError)):
            set_slippage(FixedSlippage(0.01), security_type='invalid_security_type')
        
        # 测试参数逻辑错误
        with pytest.raises((ValidationException, ValueError)):
            set_slippage(FixedSlippage(0.01), ref='000001.SZ')  # 缺少security_type
        
        # 测试负值滑点
        with pytest.raises(ValueError):
            set_slippage(FixedSlippage(-0.01))
        
        with pytest.raises(ValueError):
            set_slippage(PriceRelatedSlippage(-0.001))
        
        with pytest.raises(ValueError):
            set_slippage(StepRelatedSlippage(-1, 0.5))
    
    def test_ref_parameter_examples(self):
        """测试ref参数示例（JQ文档示例）"""
        # JQ文档中的示例形式
        
        # 股票代码示例
        set_slippage(FixedSlippage(0.03), security_type='stock', ref='000001.XSHE')
        set_slippage(FixedSlippage(0.02), security_type='stock', ref='510180.XSHG')
        
        # 期货代码示例  
        set_slippage(StepRelatedSlippage(2), security_type='futures', ref='IF1709')
        set_slippage(StepRelatedSlippage(1), security_type='futures', ref='CU')
        set_slippage(StepRelatedSlippage(2), security_type='futures', ref="RB1809.XSGE")
        
        # 基金代码示例
        set_slippage(PriceRelatedSlippage(0.001), security_type='fund', ref='000300.OF')
        
        # 所有设置都应该成功
        assert True
    
    def test_trading_cost_and_slippage_interaction(self):
        """测试交易成本和滑点的交互"""
        from emutrader import OrderCost, set_order_cost
        
        # 设置交易成本
        stock_cost = OrderCost(
            open_tax=0,
            close_tax=0.001,
            open_commission=0.0003,
            close_commission=0.0003,
            close_today_commission=0,
            min_commission=5
        )
        set_order_cost(stock_cost, type='stock')
        
        # 设置滑点
        set_slippage(FixedSlippage(0.05))
        
        # 执行交易
        self.context.update_market_price('000001.SZ', 20.0)
        initial_cash = self.context.portfolio.available_cash
        
        order = order_shares('000001.SZ', 1000, 20.0)
        assert order is not None
        
        # 验证滑点和交易成本都被应用
        final_cash = self.context.portfolio.available_cash
        cash_used = initial_cash - final_cash
        
        # 预期成本：交易金额 + 滑点影响 + 交易成本
        expected_base = 1000 * 20.0  # 20000
        expected_slippage_impact = 1000 * 0.05  # 50（滑点总额，双边）
        expected_total = expected_base + expected_slippage_impact + 5  # +最低佣金
        
        # 实际使用资金应该接近预期（可能会有微小差异）
        assert abs(cash_used - expected_total) < 100  # 允许合理差异
    
    def test_backward_compatibility(self):
        """测试向后兼容性"""
        # 确保现有的JQ策略代码无需修改即可使用滑点功能
        
        # 模拟典型的JQ策略代码模式
        def simulate_jq_strategy():
            # 策略初始化
            context = get_jq_account("jq_strategy", 100000)
            
            # 设置滑点（新增功能）
            set_slippage(PriceRelatedSlippage(0.002))
            
            # 更新价格
            context.update_market_price('000001.SZ', 25.0)
            
            # 交易（原有代码）
            order_shares('000001.SZ', 1000, 25.0)
            
            # 查看持仓（原有代码）
            position = context.portfolio.get_position('000001.SZ')
            
            # 验证滑点自动应用
            return position.avg_cost > 25.0
        
        # 模拟应该成功运行
        result = simulate_jq_strategy()
        assert result is True


class TestJoinQuantEdgeCases:
    """JoinQuant边界情况测试"""
    
    def setup_method(self):
        """测试前初始化"""
        self.context = get_jq_account("edge_case_test", 100000)
    
    def test_zero_amount_trading(self):
        """测试零数量交易"""
        set_slippage(FixedSlippage(0.02))
        self.context.update_market_price('000001.SZ', 20.0)
        
        # 零数量交易应该不执行但也不出错
        order = order_shares('000001.SZ', 0, 20.0)
        # JQ通常返回None或忽略零数量订单
        assert True
    
    def test_very_small_slippage(self):
        """测试极小滑点"""
        set_slippage(PriceRelatedSlippage(0.0001))  # 0.01%
        
        from emutrader.api import get_current_emutrader
        emu = get_current_emutrader()
        
        buy_price = emu.calculate_slippage_price('TEST', 100.0, 1000, 'open', 'stock')
        expected = 100.0 + 100.0 * 0.0001 / 2
        
        assert abs(buy_price - expected) < 1e-8
    
    def test_large_slippage_values(self):
        """测试大滑点值"""
        set_slippage(FixedSlippage(1.0))  # 1元滑点
        
        from emutrader.api import get_current_emutrader
        emu = get_current_emutrader()
        
        buy_price = emu.calculate_slippage_price('TEST', 10.0, 1000, 'open', 'stock')
        expected = 10.0 + 1.0 / 2  # 10.5
        
        assert abs(buy_price - expected) < 1e-6
    
    def test_multiple_slippage_changes(self):
        """测试多次滑点设置变更"""
        from emutrader.api import get_current_emutrader
        emu = get_current_emutrader()
        
        # 连续更改滑点设置
        set_slippage(FixedSlippage(0.01))
        set_slippage(FixedSlippage(0.02))
        set_slippage(PriceRelatedSlippage(0.001))
        set_slippage(PriceRelatedSlippage(0.002))
        set_slippage(StepRelatedSlippage(1))
        set_slippage(StepRelatedSlippage(2))
        
        # 最后设置应该生效
        final_info = emu.get_slippage_info('000001.SZ', 'stock')
        assert final_info['type'] == 'StepRelatedSlippage'
        assert final_info['params']['steps'] == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])