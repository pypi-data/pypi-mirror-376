# -*- coding: utf-8 -*-
"""
EmuTrader 测试模式支持

提供测试模式配置、Mock数据生成、测试辅助工具等功能。
"""

from .test_mode import TestMode, enable_test_mode, disable_test_mode, is_test_mode
from .mock_data import MockDataProvider, MockPriceProvider, get_mock_price
from .test_utils import create_test_account, create_test_context, reset_test_environment

__all__ = [
    # 测试模式管理
    'TestMode',
    'enable_test_mode', 
    'disable_test_mode',
    'is_test_mode',
    
    # Mock数据提供
    'MockDataProvider',
    'MockPriceProvider',
    'get_mock_price',
    
    # 测试工具
    'create_test_account',
    'create_test_context', 
    'reset_test_environment',
]