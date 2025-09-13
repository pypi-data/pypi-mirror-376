#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
EmuTrader 滑点功能测试

测试滑点设置、计算和交易执行的正确性。
"""

import pytest
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from emutrader import (
    get_jq_account, FixedSlippage, PriceRelatedSlippage, StepRelatedSlippage,
    order_shares, set_slippage
)
from emutrader.core.slippage import SlippageManager


class TestSlippageBasic:
    """基础滑点功能测试"""
    
    def setup_method(self):
        """测试前初始化"""
        self.context = get_jq_account("slippage_test", 100000)
        self.security = '000001.SZ'
        self.price = 10.0
        self.amount = 1000
    
    def test_fixed_slippage_creation(self):
        """测试固定滑点创建"""
        # 正常创建
        slippage = FixedSlippage(0.02)
        assert slippage.fixed_value == 0.02
        
        # 测试计算
        slippage_value = slippage.calculate_slippage(self.price, self.amount)
        assert slippage_value == 0.02
        
        # 测试负值异常
        with pytest.raises(ValueError, match="固定滑点值不能为负数"):
            FixedSlippage(-0.01)
    
    def test_price_related_slippage_creation(self):
        """测试百分比滑点创建"""
        # 正常创建
        slippage = PriceRelatedSlippage(0.002)
        assert slippage.percentage == 0.002
        
        # 测试计算
        slippage_value = slippage.calculate_slippage(self.price, self.amount)
        expected = self.price * 0.002  # 10.0 * 0.002 = 0.02
        assert abs(slippage_value - expected) < 1e-6
        
        # 测试负值异常
        with pytest.raises(ValueError, match="百分比滑点不能为负数"):
            PriceRelatedSlippage(-0.001)
    
    def test_step_related_slippage_creation(self):
        """测试跳数滑点创建"""
        # 正常创建
        slippage = StepRelatedSlippage(2, 0.5)
        assert slippage.steps == 2
        assert slippage.price_step == 0.5
        
        # 测试计算：2跳滑点，单边1跳，双边2跳
        slippage_value = slippage.calculate_slippage(self.price, self.amount)
        expected = 1 * 0.5 * 2  # floor(2/2) * 0.5 * 2 = 1.0
        assert slippage_value == expected
        
        # 测试3跳滑点：单边1跳，双边2跳
        slippage3 = StepRelatedSlippage(3, 0.5)
        slippage_value3 = slippage3.calculate_slippage(self.price, self.amount)
        expected3 = 1 * 0.5 * 2  # floor(3/2) * 0.5 * 2 = 1.0
        assert slippage_value3 == expected3
        
        # 测试异常值
        with pytest.raises(ValueError, match="跳数必须为正数"):
            StepRelatedSlippage(0, 0.5)
        with pytest.raises(ValueError, match="价格步长必须为正数"):
            StepRelatedSlippage(2, 0)


class TestSlippageManager:
    """滑点管理器测试"""
    
    def setup_method(self):
        """测试前初始化"""
        self.manager = SlippageManager()
    
    def test_default_slippage(self):
        """测试默认滑点"""
        # 默认应该是PriceRelatedSlippage(0.00246)
        default_slippage = self.manager.default_slippage
        assert isinstance(default_slippage, PriceRelatedSlippage)
        assert abs(default_slippage.percentage - 0.00246) < 1e-6
    
    def test_set_global_slippage(self):
        """测试全局滑点设置"""
        fixed_slippage = FixedSlippage(0.05)
        self.manager.set_slippage(fixed_slippage)
        
        # 获取适用滑点应该是刚设置的固定滑点
        applicable = self.manager.get_applicable_slippage('000001.SZ', 'stock')
        assert applicable is fixed_slippage
    
    def test_set_type_slippage(self):
        """测试按类型设置滑点"""
        stock_slippage = PriceRelatedSlippage(0.001)
        self.manager.set_slippage(stock_slippage, type='stock')
        
        # 股票类型应该使用特定滑点
        stock_applicable = self.manager.get_applicable_slippage('000001.SZ', 'stock')
        assert stock_applicable is stock_slippage
        
        # 期货类型应该使用默认滑点
        futures_applicable = self.manager.get_applicable_slippage('IF2312', 'futures')
        assert futures_applicable is self.manager.default_slippage
    
    def test_set_specific_slippage(self):
        """测试按具体标的设置滑点"""
        specific_slippage = FixedSlippage(0.03)
        self.manager.set_slippage(specific_slippage, type='stock', ref='000001.SZ')
        
        # 具体标的应该使用特定滑点
        specific_applicable = self.manager.get_applicable_slippage('000001.SZ', 'stock')
        assert specific_applicable is specific_slippage
        
        # 其他股票应该使用类型滑点或默认滑点
        other_applicable = self.manager.get_applicable_slippage('000002.SZ', 'stock')
        assert other_applicable is not specific_slippage
    
    def test_priority_order(self):
        """测试滑点优先级：具体标的 > 类型 > 全局"""
        # 设置全局滑点
        global_slippage = FixedSlippage(0.01)
        self.manager.set_slippage(global_slippage)
        
        # 设置股票类型滑点
        type_slippage = PriceRelatedSlippage(0.002)
        self.manager.set_slippage(type_slippage, type='stock')
        
        # 设置具体标的滑点
        specific_slippage = FixedSlippage(0.05)
        self.manager.set_slippage(specific_slippage, type='stock', ref='000001.SZ')
        
        # 测试优先级
        assert self.manager.get_applicable_slippage('000001.SZ', 'stock') is specific_slippage
        assert self.manager.get_applicable_slippage('000002.SZ', 'stock') is type_slippage
        assert self.manager.get_applicable_slippage('IF2312', 'futures') is global_slippage
    
    def test_money_market_fund_zero_slippage(self):
        """测试货币基金零滑点"""
        # 货币基金滑点应该强制为0
        mmf_slippage = self.manager.get_applicable_slippage('511880.SH', 'mmf')
        assert isinstance(mmf_slippage, FixedSlippage)
        assert mmf_slippage.fixed_value == 0.0
        
        # 即使设置了滑点也应该被覆盖为0
        self.manager.set_slippage(FixedSlippage(0.1), type='mmf')
        mmf_slippage2 = self.manager.get_applicable_slippage('511880.SH', 'mmf')
        assert mmf_slippage2.fixed_value == 0.0
    
    def test_execution_price_calculation(self):
        """测试执行价格计算"""
        # 设置固定滑点0.1
        self.manager.set_slippage(FixedSlippage(0.1))
        
        # 买入：预期价 + 滑点/2
        buy_price = self.manager.calculate_execution_price(
            '000001.SZ', 10.0, 1000, 'open', 'stock'
        )
        assert buy_price == 10.05  # 10.0 + 0.1/2
        
        # 卖出：预期价 - 滑点/2  
        sell_price = self.manager.calculate_execution_price(
            '000001.SZ', 10.0, 1000, 'close', 'stock'
        )
        assert sell_price == 9.95  # 10.0 - 0.1/2
        
        # 测试最低价格限制
        low_price = self.manager.calculate_execution_price(
            '000001.SZ', 0.01, 1000, 'close', 'stock'
        )
        assert low_price == 0.01  # 不会低于0.01


class TestSlippageIntegration:
    """滑点集成测试"""
    
    def setup_method(self):
        """测试前初始化"""
        self.context = get_jq_account("slippage_integration_test", 100000)
    
    def test_set_slippage_api(self):
        """测试set_slippage API"""
        # 测试固定滑点
        fixed_slippage = FixedSlippage(0.02)
        set_slippage(fixed_slippage)
        
        # 验证设置生效
        from emutrader.api import get_current_emutrader
        emu = get_current_emutrader()
        slippage_info = emu.get_slippage_info('000001.SZ', 'stock')
        assert slippage_info['type'] == 'FixedSlippage'
        assert slippage_info['params']['fixed_value'] == 0.02
    
    def test_slippage_in_trading(self):
        """测试交易中的滑点应用"""
        # 设置百分比滑点0.01
        set_slippage(PriceRelatedSlippage(0.01))
        
        # 更新价格
        self.context.update_market_price('000001.SZ', 10.0)
        
        # 买入1000股
        initial_cash = self.context.portfolio.available_cash
        order_result = order_shares('000001.SZ', 1000, 10.0)
        
        assert order_result is not None
        
        # 检查成交价应该包含滑点
        position = self.context.portfolio.get_position('000001.SZ')
        assert position is not None
        assert position.total_amount == 1000
        
        # 预期价格：10.0 + 10.0*0.01/2 = 10.05
        # 由于还有交易成本，平均成本会略高于10.05
        assert position.avg_cost > 10.0
    
    def test_different_securities_different_slippage(self):
        """测试不同证券不同滑点"""
        # 为股票设置0.1%滑点
        set_slippage(PriceRelatedSlippage(0.001), type='stock')
        
        # 为期货设置2跳滑点
        set_slippage(StepRelatedSlippage(2, 0.2), type='futures')
        
        from emutrader.api import get_current_emutrader
        emu = get_current_emutrader()
        
        # 验证股票滑点
        stock_slippage = emu.get_slippage_info('000001.SZ', 'stock')
        assert stock_slippage['type'] == 'PriceRelatedSlippage'
        assert stock_slippage['params']['percentage'] == 0.001
        
        # 验证期货滑点
        futures_slippage = emu.get_slippage_info('IF2312', 'futures')
        assert futures_slippage['type'] == 'StepRelatedSlippage'
        assert futures_slippage['params']['steps'] == 2
        assert futures_slippage['params']['price_step'] == 0.2


def run_basic_tests():
    """运行基础测试"""
    print("=== 运行滑点基础功能测试 ===\n")
    
    # 1. 基础滑点类测试
    print("1. 测试基础滑点类...")
    test_basic = TestSlippageBasic()
    test_basic.setup_method()
    
    # 固定滑点测试
    try:
        test_basic.test_fixed_slippage_creation()
        print("[PASS] 固定滑点创建测试通过")
    except Exception as e:
        print(f"[FAIL] 固定滑点创建测试失败: {e}")
    
    # 百分比滑点测试
    try:
        test_basic.test_price_related_slippage_creation()
        print("[PASS] 百分比滑点创建测试通过")
    except Exception as e:
        print(f"[FAIL] 百分比滑点创建测试失败: {e}")
    
    # 跳数滑点测试
    try:
        test_basic.test_step_related_slippage_creation()
        print("[PASS] 跳数滑点创建测试通过")
    except Exception as e:
        print(f"[FAIL] 跳数滑点创建测试失败: {e}")
    
    print()
    
    # 2. 滑点管理器测试
    print("2. 测试滑点管理器...")
    test_manager = TestSlippageManager()
    test_manager.setup_method()
    
    try:
        test_manager.test_default_slippage()
        print("[PASS] 默认滑点测试通过")
    except Exception as e:
        print(f"[FAIL] 默认滑点测试失败: {e}")
    
    try:
        test_manager.test_priority_order()
        print("[PASS] 滑点优先级测试通过")
    except Exception as e:
        print(f"[FAIL] 滑点优先级测试失败: {e}")
    
    try:
        test_manager.test_execution_price_calculation()
        print("[PASS] 执行价格计算测试通过")
    except Exception as e:
        print(f"[FAIL] 执行价格计算测试失败: {e}")
    
    print()
    
    # 3. 集成测试
    print("3. 测试滑点集成...")
    test_integration = TestSlippageIntegration()
    test_integration.setup_method()
    
    try:
        test_integration.test_set_slippage_api()
        print("[PASS] set_slippage API测试通过")
    except Exception as e:
        print(f"[FAIL] set_slippage API测试失败: {e}")
    
    try:
        test_integration.test_slippage_in_trading()
        print("[PASS] 交易滑点应用测试通过")
    except Exception as e:
        print(f"[FAIL] 交易滑点应用测试失败: {e}")
    
    print("\n=== 基础测试完成 ===")


def run_advanced_example():
    """运行高级示例"""
    print("\n=== 运行滑点高级示例 ===\n")
    
    # 创建账户
    context = get_jq_account("advanced_slippage_example", 200000)
    print(f"初始资金: {context.portfolio.available_cash:.2f}元")
    
    # 1. 设置不同类型滑点
    print("\n1. 设置不同类型滑点...")
    
    # 全局固定滑点
    set_slippage(FixedSlippage(0.02))
    print("[OK] 设置全局固定滑点0.02元")
    
    # 股票百分比滑点
    set_slippage(PriceRelatedSlippage(0.002), type='stock')
    print("[OK] 设置股票百分比滑点0.2%")
    
    # 特定股票固定滑点
    set_slippage(FixedSlippage(0.05), type='stock', ref='000001.SZ')
    print("[OK] 设置000001.SZ固定滑点0.05元")
    
    # 期货跳数滑点
    set_slippage(StepRelatedSlippage(2, 0.5), type='futures')
    print("[OK] 设置期货跳数滑点(2跳，步长0.5)")
    
    # 2. 查看滑点配置
    print("\n2. 滑点配置信息:")
    from emutrader.api import get_current_emutrader
    emu = get_current_emutrader()
    
    # 获取所有配置
    all_configs = emu.get_all_slippage_configurations()
    print(f"全局滑点: {all_configs['default']}")
    print(f"类型配置: {all_configs['type_configs']}")
    print(f"特定配置: {all_configs['specific_configs']}")
    
    # 3. 测试不同证券的滑点计算
    print("\n3. 滑点计算演示:")
    test_price = 100.0
    test_amount = 100
    
    securities = [
        ('000001.SZ', 'stock', '平安银行(特定滑点)'),
        ('000002.SZ', 'stock', '万科A(股票默认滑点)'),
        ('IF2312', 'futures', '沪深300期货(期货滑点)'),
        ('511880.SH', 'mmf', '银华日利(货币基金零滑点)')
    ]
    
    for security, sec_type, desc in securities:
        slippage_info = emu.get_slippage_info(security, sec_type)
        buy_price = emu.calculate_slippage_price(security, test_price, test_amount, 'open', sec_type)
        sell_price = emu.calculate_slippage_price(security, test_price, test_amount, 'close', sec_type)
        
        print(f"\n{desc}:")
        print(f"  滑点类型: {slippage_info['type']}")
        print(f"  滑点参数: {slippage_info['params']}")
        print(f"  买入价格: {buy_price:.4f} (预期: {test_price})")
        print(f"  卖出价格: {sell_price:.4f} (预期: {test_price})")
    
    # 4. 实际交易测试
    print("\n4. 实际交易测试:")
    
    # 更新价格
    context.update_market_price('000001.SZ', 20.0)
    context.update_market_price('000002.SZ', 30.0)
    
    # 买入测试
    print("\n执行买入交易:")
    initial_cash = context.portfolio.available_cash
    
    # 买入000001.SZ (有特定滑点)
    order1 = order_shares('000001.SZ', 1000, 20.0)
    if order1:
        position1 = context.portfolio.get_position('000001.SZ')
        print(f"000001.SZ买入1000股")
        print(f"  平均成本: {position1.avg_cost:.4f}")
        print(f"  预期价格: 20.00, 滑点后: ~20.025")
    
    # 买入000002.SZ (默认股票滑点)
    order2 = order_shares('000002.SZ', 1000, 30.0)
    if order2:
        position2 = context.portfolio.get_position('000002.SZ')
        print(f"000002.SZ买入1000股")
        print(f"  平均成本: {position2.avg_cost:.4f}")
        print(f"  预期价格: 30.00, 滑点后: ~30.03")
    
    final_cash = context.portfolio.available_cash
    cash_used = initial_cash - final_cash
    print(f"\n总共使用资金: {cash_used:.2f}元")
    print(f"剩余资金: {final_cash:.2f}元")
    
    print("\n=== 高级示例完成 ===")


if __name__ == "__main__":
    """主函数"""
    print("EmuTrader 滑点功能测试")
    print("=" * 50)
    
    # 运行基础测试
    run_basic_tests()
    
    # 运行高级示例
    run_advanced_example()
    
    print("\n" + "=" * 50)
    print("所有测试完成！")