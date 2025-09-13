#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
滑点核心模块测试

测试滑点类和SlippageManager的核心功能。
"""

import pytest
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from emutrader.core.slippage import (
    SlippageBase, FixedSlippage, PriceRelatedSlippage, StepRelatedSlippage,
    SlippageManager
)


class TestFixedSlippage:
    """固定滑点测试"""
    
    def test_creation_valid(self):
        """测试有效创建"""
        slippage = FixedSlippage(0.02)
        assert slippage.fixed_value == 0.02
    
    def test_creation_zero(self):
        """测试零值创建"""
        slippage = FixedSlippage(0.0)
        assert slippage.fixed_value == 0.0
    
    def test_creation_negative_invalid(self):
        """测试负值创建（应该失败）"""
        with pytest.raises(ValueError, match="固定滑点值不能为负数"):
            FixedSlippage(-0.01)
    
    def test_calculate_slippage(self):
        """测试滑点计算"""
        slippage = FixedSlippage(0.02)
        
        # 不同价格和数量都应该返回相同的固定值
        assert slippage.calculate_slippage(10.0, 1000) == 0.02
        assert slippage.calculate_slippage(100.0, 500) == 0.02
        assert slippage.calculate_slippage(1.0, 100) == 0.02
    
    def test_to_dict(self):
        """测试字典转换"""
        slippage = FixedSlippage(0.05)
        result = slippage.to_dict()
        
        assert result['type'] == 'FixedSlippage'
        assert result['params']['fixed_value'] == 0.05
    
    def test_repr(self):
        """测试字符串表示"""
        slippage = FixedSlippage(0.03)
        result = repr(slippage)
        
        assert 'FixedSlippage' in result
        assert '0.03' in result


class TestPriceRelatedSlippage:
    """百分比滑点测试"""
    
    def test_creation_valid(self):
        """测试有效创建"""
        slippage = PriceRelatedSlippage(0.002)
        assert slippage.percentage == 0.002
    
    def test_creation_zero(self):
        """测试零值创建"""
        slippage = PriceRelatedSlippage(0.0)
        assert slippage.percentage == 0.0
    
    def test_creation_negative_invalid(self):
        """测试负值创建（应该失败）"""
        with pytest.raises(ValueError, match="百分比滑点不能为负数"):
            PriceRelatedSlippage(-0.001)
    
    def test_calculate_slippage(self):
        """测试滑点计算"""
        slippage = PriceRelatedSlippage(0.002)  # 0.2%
        
        # 计算应该基于价格
        assert slippage.calculate_slippage(10.0, 1000) == 10.0 * 0.002  # 0.02
        assert slippage.calculate_slippage(100.0, 500) == 100.0 * 0.002  # 0.2
        assert slippage.calculate_slippage(50.0, 200) == 50.0 * 0.002  # 0.1
    
    def test_calculate_slippage_precision(self):
        """测试计算精度"""
        slippage = PriceRelatedSlippage(0.00246)  # 默认值
        
        result = slippage.calculate_slippage(123.45, 100)
        expected = 123.45 * 0.00246
        
        assert abs(result - expected) < 1e-8
    
    def test_to_dict(self):
        """测试字典转换"""
        slippage = PriceRelatedSlippage(0.003)
        result = slippage.to_dict()
        
        assert result['type'] == 'PriceRelatedSlippage'
        assert result['params']['percentage'] == 0.003
    
    def test_repr(self):
        """测试字符串表示"""
        slippage = PriceRelatedSlippage(0.001)
        result = repr(slippage)
        
        assert 'PriceRelatedSlippage' in result
        assert '0.001' in result


class TestStepRelatedSlippage:
    """跳数滑点测试"""
    
    def test_creation_valid(self):
        """测试有效创建"""
        slippage = StepRelatedSlippage(2, 0.5)
        assert slippage.steps == 2
        assert slippage.price_step == 0.5
    
    def test_creation_default_price_step(self):
        """测试默认价格步长"""
        slippage = StepRelatedSlippage(3)
        assert slippage.steps == 3
        assert slippage.price_step == 1.0
    
    def test_creation_invalid_steps(self):
        """测试无效跳数"""
        with pytest.raises(ValueError, match="跳数必须为正数"):
            StepRelatedSlippage(0, 0.5)
        
        with pytest.raises(ValueError, match="跳数必须为正数"):
            StepRelatedSlippage(-1, 0.5)
    
    def test_creation_invalid_price_step(self):
        """测试无效价格步长"""
        with pytest.raises(ValueError, match="价格步长必须为正数"):
            StepRelatedSlippage(2, 0.0)
        
        with pytest.raises(ValueError, match="价格步长必须为正数"):
            StepRelatedSlippage(2, -0.1)
    
    def test_calculate_slippage_even_steps(self):
        """测试偶数跳数计算"""
        slippage = StepRelatedSlippage(2, 0.5)
        
        # 2跳：单边1跳，双边2跳
        result = slippage.calculate_slippage(100.0, 1000)
        expected = 1 * 0.5 * 2  # 1.0
        
        assert result == expected
    
    def test_calculate_slippage_odd_steps(self):
        """测试奇数跳数计算"""
        slippage = StepRelatedSlippage(3, 0.5)
        
        # 3跳：单边floor(3/2)=1跳，双边2跳
        result = slippage.calculate_slippage(100.0, 1000)
        expected = 1 * 0.5 * 2  # 1.0
        
        assert result == expected
    
    def test_calculate_slippage_different_steps(self):
        """测试不同跳数"""
        test_cases = [
            (1, 0.5, 0.0),  # 1跳：单边0跳，双边0跳
            (2, 0.5, 1.0),  # 2跳：单边1跳，双边2跳
            (3, 0.5, 1.0),  # 3跳：单边1跳，双边2跳
            (4, 0.5, 2.0),  # 4跳：单边2跳，双边4跳
            (5, 0.5, 2.0),  # 5跳：单边2跳，双边4跳
        ]
        
        for steps, price_step, expected in test_cases:
            slippage = StepRelatedSlippage(steps, price_step)
            result = slippage.calculate_slippage(100.0, 1000)
            assert result == expected, f"跳数{steps}失败: 期望{expected}, 实际{result}"
    
    def test_to_dict(self):
        """测试字典转换"""
        slippage = StepRelatedSlippage(2, 0.5)
        result = slippage.to_dict()
        
        assert result['type'] == 'StepRelatedSlippage'
        assert result['params']['steps'] == 2
        assert result['params']['price_step'] == 0.5
    
    def test_repr(self):
        """测试字符串表示"""
        slippage = StepRelatedSlippage(3, 0.2)
        result = repr(slippage)
        
        assert 'StepRelatedSlippage' in result
        assert '3' in result
        assert '0.2' in result


class TestSlippageManager:
    """滑点管理器测试"""
    
    def setup_method(self):
        """测试前初始化"""
        self.manager = SlippageManager()
    
    def test_default_slippage(self):
        """测试默认滑点"""
        default = self.manager.default_slippage
        assert isinstance(default, PriceRelatedSlippage)
        assert abs(default.percentage - 0.00246) < 1e-6
    
    def test_supported_types(self):
        """测试支持的交易类型"""
        expected_types = {
            'stock', 'fund', 'mmf', 'fja', 'fjb', 'fjm',
            'index_futures', 'futures', 'bond_fund', 'stock_fund',
            'QDII_fund', 'mixture_fund', 'money_market_fund'
        }
        assert self.manager.supported_types == expected_types
    
    def test_set_global_slippage(self):
        """测试设置全局滑点"""
        slippage = FixedSlippage(0.05)
        self.manager.set_slippage(slippage)
        
        # 应该改变默认滑点
        assert self.manager.default_slippage is slippage
        
        # 应该适用于所有证券
        applicable = self.manager.get_applicable_slippage('000001.SZ', 'stock')
        assert applicable is slippage
    
    def test_set_type_slippage(self):
        """测试设置类型滑点"""
        slippage = PriceRelatedSlippage(0.001)
        self.manager.set_slippage(slippage, security_type='stock')
        
        # 股票应该使用新滑点
        stock_applicable = self.manager.get_applicable_slippage('000001.SZ', 'stock')
        assert stock_applicable is slippage
        
        # 期货应该使用默认滑点
        futures_applicable = self.manager.get_applicable_slippage('IF2312', 'futures')
        assert futures_applicable is self.manager.default_slippage
    
    def test_set_specific_slippage(self):
        """测试设置特定证券滑点"""
        slippage = FixedSlippage(0.03)
        self.manager.set_slippage(slippage, security_type='stock', ref='000001.SZ')
        
        # 特定证券应该使用特定滑点
        specific_applicable = self.manager.get_applicable_slippage('000001.SZ', 'stock')
        assert specific_applicable is slippage
        
        # 其他证券应该使用默认滑点
        other_applicable = self.manager.get_applicable_slippage('000002.SZ', 'stock')
        assert other_applicable is not slippage
    
    def test_priority_order(self):
        """测试优先级：具体标的 > 类型 > 全局"""
        # 设置全局
        global_slippage = FixedSlippage(0.01)
        self.manager.set_slippage(global_slippage)
        
        # 设置类型
        type_slippage = PriceRelatedSlippage(0.002)
        self.manager.set_slippage(type_slippage, security_type='stock')
        
        # 设置特定
        specific_slippage = FixedSlippage(0.05)
        self.manager.set_slippage(specific_slippage, security_type='stock', ref='000001.SZ')
        
        # 验证优先级
        assert self.manager.get_applicable_slippage('000001.SZ', 'stock') is specific_slippage
        assert self.manager.get_applicable_slippage('000002.SZ', 'stock') is type_slippage
        assert self.manager.get_applicable_slippage('IF2312', 'futures') is global_slippage
    
    def test_money_market_fund_zero_slippage(self):
        """测试货币基金零滑点（最高优先级）"""
        # 尝试设置货币基金滑点
        self.manager.set_slippage(FixedSlippage(0.1), security_type='mmf')
        
        # 应该强制返回零滑点
        mmf_slippage = self.manager.get_applicable_slippage('511880.SH', 'mmf')
        assert isinstance(mmf_slippage, FixedSlippage)
        assert mmf_slippage.fixed_value == 0.0
        
        # 即使尝试设置特定标的也应该被覆盖
        self.manager.set_slippage(FixedSlippage(0.2), security_type='mmf', ref='511880.SH')
        mmf_specific = self.manager.get_applicable_slippage('511880.SH', 'mmf')
        assert mmf_specific.fixed_value == 0.0
    
    def test_execution_price_calculation(self):
        """测试执行价格计算"""
        # 设置固定滑点0.2
        self.manager.set_slippage(FixedSlippage(0.2))
        
        # 买入：预期价 + 滑点/2
        buy_price = self.manager.calculate_execution_price(
            '000001.SZ', 100.0, 1000, 'open', 'stock'
        )
        assert buy_price == 100.1  # 100.0 + 0.2/2
        
        # 卖出：预期价 - 滑点/2
        sell_price = self.manager.calculate_execution_price(
            '000001.SZ', 100.0, 1000, 'close', 'stock'
        )
        assert sell_price == 99.9  # 100.0 - 0.2/2
    
    def test_execution_price_minimum_limit(self):
        """测试执行价格最低限制"""
        # 设置大滑点
        self.manager.set_slippage(FixedSlippage(1.0))
        
        # 测试低价卖出，不应该低于0.01
        low_price = self.manager.calculate_execution_price(
            '000001.SZ', 0.01, 1000, 'close', 'stock'
        )
        assert low_price == 0.01
    
    def test_clear_slippage_all(self):
        """测试清除所有滑点设置"""
        # 设置各种滑点
        self.manager.set_slippage(FixedSlippage(0.1))
        self.manager.set_slippage(PriceRelatedSlippage(0.001), security_type='stock')
        self.manager.set_slippage(FixedSlippage(0.05), security_type='stock', ref='000001.SZ')
        
        # 清除所有
        self.manager.clear_slippage()
        
        # 应该恢复默认
        assert isinstance(self.manager.default_slippage, PriceRelatedSlippage)
        assert abs(self.manager.default_slippage.percentage - 0.00246) < 1e-6
        assert len(self.manager.type_slippage) == 0
        assert len(self.manager.specific_slippage) == 0
    
    def test_clear_slippage_by_type(self):
        """测试按类型清除滑点"""
        # 设置多种类型
        self.manager.set_slippage(PriceRelatedSlippage(0.001), security_type='stock')
        self.manager.set_slippage(FixedSlippage(0.1), security_type='futures')
        
        # 清除股票类型
        self.manager.clear_slippage(security_type='stock')
        
        # 股票应该使用默认，期货应该保持设置
        stock_applicable = self.manager.get_applicable_slippage('000001.SZ', 'stock')
        futures_applicable = self.manager.get_applicable_slippage('IF2312', 'futures')
        
        assert stock_applicable is self.manager.default_slippage
        assert isinstance(futures_applicable, FixedSlippage)
        assert futures_applicable.fixed_value == 0.1
    
    def test_clear_slippage_by_ref(self):
        """测试按标的清除滑点"""
        # 设置多个特定标的
        self.manager.set_slippage(FixedSlippage(0.03), security_type='stock', ref='000001.SZ')
        self.manager.set_slippage(FixedSlippage(0.05), security_type='stock', ref='000002.SZ')
        
        # 清除一个标的
        self.manager.clear_slippage(security_type='stock', ref='000001.SZ')
        
        # 被清除的应该使用类型或默认，其他的应该保持
        applicable1 = self.manager.get_applicable_slippage('000001.SZ', 'stock')
        applicable2 = self.manager.get_applicable_slippage('000002.SZ', 'stock')
        
        assert applicable1 is self.manager.default_slippage
        assert isinstance(applicable2, FixedSlippage)
        assert applicable2.fixed_value == 0.05
    
    def test_get_all_configurations(self):
        """测试获取所有配置"""
        # 设置各种配置
        self.manager.set_slippage(FixedSlippage(0.02))  # 全局
        self.manager.set_slippage(PriceRelatedSlippage(0.001), security_type='stock')  # 类型
        self.manager.set_slippage(FixedSlippage(0.03), security_type='stock', ref='000001.SZ')  # 特定
        
        configs = self.manager.get_all_configurations()
        
        assert 'default' in configs
        assert 'type_configs' in configs
        assert 'specific_configs' in configs
        
        assert configs['default']['type'] == 'FixedSlippage'
        assert configs['type_configs']['stock']['type'] == 'PriceRelatedSlippage'
        assert configs['specific_configs']['000001.SZ']['type'] == 'FixedSlippage'
    
    def test_invalid_type_validation(self):
        """测试无效类型验证"""
        with pytest.raises(ValueError, match="不支持的交易品种类型"):
            self.manager.set_slippage(FixedSlippage(0.01), security_type='invalid_type')
    
    def test_ref_without_type_validation(self):
        """测试ref参数缺少type的验证"""
        with pytest.raises(ValueError, match="设置具体标的滑点时必须指定type参数"):
            self.manager.set_slippage(FixedSlippage(0.01), ref='000001.SZ')
    
    def test_invalid_slippage_object_validation(self):
        """测试无效滑点对象验证"""
        with pytest.raises(ValueError, match="slippage必须是滑点对象"):
            self.manager.set_slippage("invalid_object")
    
    def test_repr(self):
        """测试字符串表示"""
        # 设置一些配置
        self.manager.set_slippage(PriceRelatedSlippage(0.001), security_type='stock')
        self.manager.set_slippage(FixedSlippage(0.03), security_type='stock', ref='000001.SZ')
        
        result = repr(self.manager)
        
        assert 'SlippageManager' in result
        assert 'type_count' in result
        assert 'specific_count' in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])