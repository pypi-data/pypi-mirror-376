#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
滑点集成测试

测试滑点功能与EmuTrader主类的集成。
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
from emutrader.core.slippage import SlippageManager
from emutrader.exceptions import ValidationException


class TestSlippageIntegration:
    """滑点集成测试"""
    
    def setup_method(self):
        """测试前初始化"""
        self.context = get_jq_account("slippage_integration_test", 200000)
        self.security = '000001.SZ'
        self.price = 20.0
        self.amount = 1000
    
    def test_set_slippage_api_integration(self):
        """测试set_slippage API集成"""
        # 测试固定滑点
        fixed_slippage = FixedSlippage(0.02)
        set_slippage(fixed_slippage)
        
        # 验证设置生效
        from emutrader.api import get_current_emutrader
        emu = get_current_emutrader()
        slippage_info = emu.get_slippage_info(self.security, 'stock')
        
        assert slippage_info['type'] == 'FixedSlippage'
        assert slippage_info['params']['fixed_value'] == 0.02
    
    def test_emutrader_slippage_methods(self):
        """测试EmuTrader的滑点方法"""
        from emutrader.api import get_current_emutrader
        emu = get_current_emutrader()
        
        # 测试设置滑点
        slippage = PriceRelatedSlippage(0.002)
        emu.set_slippage(slippage, security_type='stock')
        
        # 测试获取滑点信息
        info = emu.get_slippage_info(self.security, 'stock')
        assert info['type'] == 'PriceRelatedSlippage'
        assert info['params']['percentage'] == 0.002
        
        # 测试价格计算
        buy_price = emu.calculate_slippage_price(self.security, 10.0, 1000, 'open', 'stock')
        sell_price = emu.calculate_slippage_price(self.security, 10.0, 1000, 'close', 'stock')
        
        assert buy_price > 10.0  # 买入价应该高于预期
        assert sell_price < 10.0  # 卖出价应该低于预期
        
        # 测试获取所有配置
        configs = emu.get_all_slippage_configurations()
        assert 'default' in configs
        assert 'type_configs' in configs
        assert 'specific_configs' in configs
    
    def test_slippage_in_order_execution(self):
        """测试交易执行中的滑点应用"""
        # 设置百分比滑点0.2%
        set_slippage(PriceRelatedSlippage(0.002))
        
        # 更新价格
        self.context.update_market_price(self.security, self.price)
        
        # 记录初始状态
        initial_cash = self.context.portfolio.available_cash
        
        # 执行买入交易
        order_result = order_shares(self.security, self.amount, self.price)
        
        assert order_result is not None
        
        # 验证滑点影响
        position = self.context.portfolio.get_position(self.security)
        assert position is not None
        assert position.total_amount == self.amount
        
        # 平均成本应该高于预期价格（因为买入滑点）
        expected_price_without_slippage = self.price
        assert position.avg_cost > expected_price_without_slippage
        
        # 计算预期滑点影响
        expected_slippage_impact = self.price * 0.002 / 2  # 买入滑点影响
        expected_avg_cost = self.price + expected_slippage_impact
        
        # 考虑交易成本，实际成本应该接近预期
        cost_difference = abs(position.avg_cost - expected_avg_cost)
        assert cost_difference < 0.1  # 差异应该在合理范围内
    
    def test_different_securities_different_slippage(self):
        """测试不同证券的不同滑点"""
        # 为股票设置0.1%滑点
        set_slippage(PriceRelatedSlippage(0.001), security_type='stock')
        
        # 为期货设置2跳滑点
        set_slippage(StepRelatedSlippage(2, 0.5), security_type='futures')
        
        # 为特定股票设置固定滑点
        set_slippage(FixedSlippage(0.05), security_type='stock', ref=self.security)
        
        from emutrader.api import get_current_emutrader
        emu = get_current_emutrader()
        
        # 验证不同证券的滑点配置
        specific_slippage = emu.get_slippage_info(self.security, 'stock')
        other_stock_slippage = emu.get_slippage_info('000002.SZ', 'stock')
        futures_slippage = emu.get_slippage_info('IF2312', 'futures')
        
        assert specific_slippage['type'] == 'FixedSlippage'
        assert specific_slippage['params']['fixed_value'] == 0.05
        
        assert other_stock_slippage['type'] == 'PriceRelatedSlippage'
        assert other_stock_slippage['params']['percentage'] == 0.001
        
        assert futures_slippage['type'] == 'StepRelatedSlippage'
        assert futures_slippage['params']['steps'] == 2
    
    def test_multiple_order_types_with_slippage(self):
        """测试不同下单函数的滑点应用"""
        # 设置固定滑点0.1
        set_slippage(FixedSlippage(0.1))
        
        # 更新两个证券的价格
        self.context.update_market_price('000001.SZ', 20.0)
        self.context.update_market_price('000002.SZ', 30.0)
        
        initial_cash = self.context.portfolio.available_cash
        
        # 测试order_shares
        order1 = order_shares('000001.SZ', 1000, 20.0)
        assert order1 is not None
        
        # 测试order_value
        order2 = order_value('000002.SZ', 30000)  # 按金额买入
        assert order2 is not None
        
        # 验证两个订单都应用了滑点
        position1 = self.context.portfolio.get_position('000001.SZ')
        position2 = self.context.portfolio.get_position('000002.SZ')
        
        assert position1.avg_cost > 20.0  # 买入滑点
        # order_value按金额买入，实际成交价可能因滑点而高于预期价格
        # position2.avg_cost应该反映包含滑点的实际成交价格
        assert position2.total_amount > 0  # 确保有持仓
        # 买入总成本应该超过订单金额（滑点影响）
        total_cost = position2.total_amount * position2.avg_cost
        assert total_cost > 30000  # 滑点使得总成本高于订单金额
        
        # 测试order_target_percent（调整仓位）
        order3 = order_target_percent('000001.SZ', 0.1)  # 调整到10%仓位
        assert order3 is not None
    
    def test_slippage_with_subportfolios(self):
        """测试子账户中的滑点应用"""
        from emutrader import set_subportfolios, SubPortfolioConfig
        
        # 设置多子账户
        set_subportfolios([
            SubPortfolioConfig(cash=100000, type='stock'),
            SubPortfolioConfig(cash=100000, type='futures')
        ])
        
        # 设置股票滑点
        set_slippage(FixedSlippage(0.05), security_type='stock')
        
        # 更新价格并在子账户0交易
        self.context.update_market_price('000001.SZ', 15.0)
        
        initial_cash = self.context.subportfolios[0].available_cash
        order_result = order_shares('000001.SZ', 500, 15.0)
        
        assert order_result is not None
        
        # 验证子账户中的滑点应用
        position = self.context.subportfolios[0].get_position('000001.SZ')
        assert position is not None
        assert position.avg_cost > 15.0  # 应用买入滑点
    
    def test_money_market_fund_zero_slippage_enforcement(self):
        """测试货币基金零滑点强制执行"""
        # 尝试设置货币基金滑点
        set_slippage(FixedSlippage(0.1), security_type='mmf')
        
        from emutrader.api import get_current_emutrader
        emu = get_current_emutrader()
        
        # 验证货币基金实际滑点为0
        mmf_slippage = emu.get_slippage_info('511880.SH', 'mmf')
        assert mmf_slippage['type'] == 'FixedSlippage'
        assert mmf_slippage['params']['fixed_value'] == 0.0
        
        # 测试价格计算确实为0滑点
        buy_price = emu.calculate_slippage_price('511880.SH', 100.0, 1000, 'open', 'mmf')
        sell_price = emu.calculate_slippage_price('511880.SH', 100.0, 1000, 'close', 'mmf')
        
        assert buy_price == 100.0
        assert sell_price == 100.0
    
    def test_slippage_configuration_persistence(self):
        """测试滑点配置的持久性"""
        # 设置复杂的多层滑点配置
        set_slippage(FixedSlippage(0.02))  # 全局
        set_slippage(PriceRelatedSlippage(0.001), security_type='stock')  # 股票类型
        set_slippage(FixedSlippage(0.03), security_type='stock', ref='000001.SZ')  # 特定股票
        set_slippage(StepRelatedSlippage(2, 0.5), security_type='futures')  # 期货类型
        
        from emutrader.api import get_current_emutrader
        emu = get_current_emutrader()
        
        # 验证所有配置都保持正确
        all_configs = emu.get_all_slippage_configurations()
        
        # 验证全局配置
        assert all_configs['default']['type'] == 'FixedSlippage'
        assert all_configs['default']['params']['fixed_value'] == 0.02
        
        # 验证类型配置
        assert 'stock' in all_configs['type_configs']
        assert 'futures' in all_configs['type_configs']
        assert all_configs['type_configs']['stock']['type'] == 'PriceRelatedSlippage'
        assert all_configs['type_configs']['futures']['type'] == 'StepRelatedSlippage'
        
        # 验证特定配置
        assert '000001.SZ' in all_configs['specific_configs']
        assert all_configs['specific_configs']['000001.SZ']['params']['fixed_value'] == 0.03
    
    def test_slippage_clear_methods(self):
        """测试滑点清除方法"""
        from emutrader.api import get_current_emutrader
        emu = get_current_emutrader()
        
        # 设置多种配置
        emu.set_slippage(FixedSlippage(0.02))
        emu.set_slippage(PriceRelatedSlippage(0.001), security_type='stock')
        emu.set_slippage(FixedSlippage(0.03), security_type='stock', ref='000001.SZ')
        
        # 测试清除特定标的
        emu.clear_slippage(security_type='stock', ref='000001.SZ')
        specific_after_clear = emu.get_slippage_info('000001.SZ', 'stock')
        
        # 应该回退到类型配置
        assert specific_after_clear['type'] == 'PriceRelatedSlippage'
        
        # 测试清除类型
        emu.clear_slippage(security_type='stock')
        stock_after_clear = emu.get_slippage_info('000001.SZ', 'stock')
        
        # 应该回退到全局配置
        assert stock_after_clear['type'] == 'FixedSlippage'
        assert stock_after_clear['params']['fixed_value'] == 0.02
        
        # 测试清除所有
        emu.clear_slippage()
        default_after_clear = emu.get_slippage_info('000001.SZ', 'stock')
        
        # 应该恢复系统默认
        assert default_after_clear['type'] == 'PriceRelatedSlippage'
        assert abs(default_after_clear['params']['percentage'] - 0.00246) < 1e-6
    
    def test_slippage_error_handling(self):
        """测试滑点错误处理"""
        from emutrader.api import get_current_emutrader
        emu = get_current_emutrader()
        
        # 测试无效滑点对象
        with pytest.raises(ValueError, match="slippage必须是滑点对象"):
            emu.set_slippage("invalid_object")
        
        # 测试无效类型
        with pytest.raises(ValueError, match="不支持的交易品种类型"):
            emu.set_slippage(FixedSlippage(0.01), security_type='invalid_type')
        
        # 测试缺少type参数
        with pytest.raises(ValueError, match="设置具体标的滑点时必须指定type参数"):
            emu.set_slippage(FixedSlippage(0.01), ref='000001.SZ')
    
    def test_large_volume_slippage_calculation(self):
        """测试大额交易的滑点计算"""
        # 设置百分比滑点
        set_slippage(PriceRelatedSlippage(0.002))
        
        # 测试大额交易
        large_price = 500.0
        large_amount = 10000  # 500万交易
        
        from emutrader.api import get_current_emutrader
        emu = get_current_emutrader()
        
        buy_price = emu.calculate_slippage_price('TEST', large_price, large_amount, 'open', 'stock')
        sell_price = emu.calculate_slippage_price('TEST', large_price, large_amount, 'close', 'stock')
        
        expected_slippage = large_price * 0.002
        expected_buy = large_price + expected_slippage / 2
        expected_sell = large_price - expected_slippage / 2
        
        assert abs(buy_price - expected_buy) < 1e-6
        assert abs(sell_price - expected_sell) < 1e-6
    
    def test_extreme_price_slippage(self):
        """测试极端价格的滑点处理"""
        set_slippage(FixedSlippage(0.1))
        
        from emutrader.api import get_current_emutrader
        emu = get_current_emutrader()
        
        # 测试极低价格卖出（应该有最低价格保护）
        very_low_sell_price = emu.calculate_slippage_price('TEST', 0.005, 1000, 'close', 'stock')
        assert very_low_sell_price == 0.01  # 不应该低于0.01
        
        # 测试极高价格
        very_high_buy_price = emu.calculate_slippage_price('TEST', 10000.0, 1000, 'open', 'stock')
        expected_high = 10000.0 + 0.1 / 2
        assert abs(very_high_buy_price - expected_high) < 1e-6


if __name__ == "__main__":
    pytest.main([__file__, "-v"])