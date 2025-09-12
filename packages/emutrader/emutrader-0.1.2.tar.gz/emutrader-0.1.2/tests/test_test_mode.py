# -*- coding: utf-8 -*-
"""
测试模式功能测试
"""

import pytest
from datetime import datetime

from emutrader.testing import (
    TestMode, enable_test_mode, disable_test_mode, is_test_mode,
    create_test_account, create_test_context, reset_test_environment,
    MockDataProvider, get_mock_price
)


class TestTestMode:
    """测试模式基础功能测试"""
    
    def setup_method(self):
        """每个测试方法前的设置"""
        disable_test_mode()  # 确保开始时测试模式关闭
    
    def teardown_method(self):
        """每个测试方法后的清理"""
        disable_test_mode()
        reset_test_environment()
    
    def test_enable_disable_test_mode(self):
        """测试启用/禁用测试模式"""
        # 初始状态
        assert not is_test_mode()
        
        # 启用测试模式
        enable_test_mode(TestMode.UNIT_TEST)
        assert is_test_mode()
        
        # 禁用测试模式
        disable_test_mode()
        assert not is_test_mode()
    
    def test_test_mode_with_config(self):
        """测试带配置的测试模式"""
        enable_test_mode(
            TestMode.UNIT_TEST,
            mock_data_seed=12345,
            debug_logging=True,
            custom_param="test_value"
        )
        
        assert is_test_mode()
        
        from emutrader.testing.test_mode import get_test_config
        assert get_test_config('mock_data_seed') == 12345
        assert get_test_config('debug_logging') is True
        assert get_test_config('custom_param') == "test_value"


class TestMockDataProvider:
    """Mock数据提供者测试"""
    
    def setup_method(self):
        disable_test_mode()
        reset_test_environment()
    
    def teardown_method(self):
        disable_test_mode()
        reset_test_environment()
    
    def test_mock_price_generation(self):
        """测试Mock价格生成"""
        provider = MockDataProvider(seed=123)
        
        # 测试价格生成
        price1 = provider.get_price('000001.SZ')
        price2 = provider.get_price('000002.SZ')
        
        assert isinstance(price1, float)
        assert isinstance(price2, float)
        assert price1 > 0
        assert price2 > 0
        
        # 同一证券多次调用应该有所变化（模拟波动）
        price1_again = provider.get_price('000001.SZ')
        # 注意：由于随机性，这里不能保证价格一定不同，但概率很高
    
    def test_fixed_price_setting(self):
        """测试固定价格设置"""
        provider = MockDataProvider()
        
        # 设置固定价格
        provider.price_provider.set_fixed_price('TEST.SZ', 15.5)
        price = provider.get_price('TEST.SZ')
        
        # 第一次应该是固定价格附近（有波动）
        assert 14.0 < price < 17.0  # 允许一定波动
    
    def test_multiple_securities(self):
        """测试多证券价格获取"""
        provider = MockDataProvider(seed=456)
        securities = ['000001.SZ', '000002.SZ', '600519.SH']
        
        prices = provider.get_multiple_prices(securities)
        
        assert len(prices) == len(securities)
        for security in securities:
            assert security in prices
            assert isinstance(prices[security], float)
            assert prices[security] > 0


class TestTestUtils:
    """测试工具函数测试"""
    
    def setup_method(self):
        disable_test_mode()
        reset_test_environment()
    
    def teardown_method(self):
        disable_test_mode()
        reset_test_environment()
    
    def test_create_test_account(self):
        """测试创建测试账户"""
        enable_test_mode(TestMode.UNIT_TEST, debug_logging=False)
        
        account = create_test_account("test_strategy", 50000, "STOCK")
        
        assert account.strategy_name == "test_strategy"
        assert account.portfolio.total_value == 50000
        assert account.account_type == "STOCK"
    
    def test_create_test_context(self):
        """测试创建测试上下文"""
        enable_test_mode(TestMode.UNIT_TEST)
        
        context = create_test_context("test_context", 80000)
        
        assert context.run_params['strategy_name'] == "test_context"
        assert context.portfolio.total_value == 80000
        assert context.portfolio.account_type == "STOCK"
    
    def test_mock_price_integration(self):
        """测试Mock价格集成"""
        enable_test_mode(TestMode.UNIT_TEST, mock_price_enabled=True, mock_data_seed=789)
        
        # 直接获取Mock价格
        price1 = get_mock_price('000001.SZ')
        price2 = get_mock_price('000002.SZ')
        
        assert isinstance(price1, float)
        assert isinstance(price2, float)
        assert price1 > 0
        assert price2 > 0
        
        # 测试与API集成
        from emutrader.api import _get_current_price
        api_price = _get_current_price('000001.SZ')
        
        # API应该使用Mock价格
        assert isinstance(api_price, float)
        assert api_price > 0


class TestTestModeContextManager:
    """测试模式上下文管理器测试"""
    
    def setup_method(self):
        disable_test_mode()
    
    def teardown_method(self):
        disable_test_mode()
        reset_test_environment()
    
    def test_context_manager(self):
        """测试上下文管理器"""
        from emutrader.testing.test_mode import test_mode_context
        
        # 初始状态
        assert not is_test_mode()
        
        # 使用上下文管理器
        with test_mode_context(TestMode.UNIT_TEST, mock_data_seed=999):
            assert is_test_mode()
            from emutrader.testing.test_mode import get_test_config
            assert get_test_config('mock_data_seed') == 999
        
        # 退出后应该恢复
        assert not is_test_mode()
    
    def test_nested_context_managers(self):
        """测试嵌套上下文管理器"""
        from emutrader.testing.test_mode import test_mode_context
        
        assert not is_test_mode()
        
        with test_mode_context(TestMode.UNIT_TEST):
            assert is_test_mode()
            
            with test_mode_context(TestMode.INTEGRATION_TEST):
                assert is_test_mode()
                # 内层上下文生效
            
            # 恢复到外层上下文
            assert is_test_mode()
        
        # 完全退出后
        assert not is_test_mode()


if __name__ == "__main__":
    # 简单的直接测试
    print("测试测试模式功能...")
    
    # 基本功能测试
    enable_test_mode(TestMode.UNIT_TEST, mock_data_seed=123)
    print(f"测试模式启用: {is_test_mode()}")
    
    # 创建测试账户
    account = create_test_account("demo", 30000)
    print(f"测试账户创建成功: {account.portfolio.total_value}")
    
    # 测试Mock价格
    price = get_mock_price('000001.SZ')
    print(f"Mock价格: 000001.SZ = {price}")
    
    # 清理
    disable_test_mode()
    reset_test_environment()
    print("测试完成")