# -*- coding: utf-8 -*-
"""
测试模式管理模块

提供测试模式开关、配置管理等功能。
"""

import threading
from typing import Dict, Any, Optional
from datetime import datetime
from enum import Enum


class TestMode(Enum):
    """测试模式枚举"""
    DISABLED = "disabled"        # 关闭测试模式
    UNIT_TEST = "unit_test"      # 单元测试模式
    INTEGRATION_TEST = "integration_test"  # 集成测试模式
    PERFORMANCE_TEST = "performance_test"  # 性能测试模式
    MOCK_TRADING = "mock_trading"  # 模拟交易模式


class TestConfig:
    """测试配置类"""
    
    def __init__(self):
        self.mode = TestMode.DISABLED
        self.mock_price_enabled = False
        self.mock_data_seed = None
        self.fast_time_simulation = False  # 快速时间模拟
        self.debug_logging = False
        self.performance_tracking = False
        self.custom_settings = {}
        
        # 线程锁保证线程安全
        self._lock = threading.RLock()
    
    def enable_test_mode(self, mode: TestMode = TestMode.UNIT_TEST, **kwargs):
        """
        启用测试模式
        
        Args:
            mode: 测试模式
            **kwargs: 其他配置参数
        """
        with self._lock:
            self.mode = mode
            
            # 根据测试模式设置默认配置
            if mode == TestMode.UNIT_TEST:
                self.mock_price_enabled = True
                self.fast_time_simulation = True
                self.debug_logging = False
                
            elif mode == TestMode.INTEGRATION_TEST:
                self.mock_price_enabled = True
                self.fast_time_simulation = False
                self.debug_logging = True
                
            elif mode == TestMode.PERFORMANCE_TEST:
                self.mock_price_enabled = True
                self.fast_time_simulation = True
                self.performance_tracking = True
                self.debug_logging = False
                
            elif mode == TestMode.MOCK_TRADING:
                self.mock_price_enabled = True
                self.fast_time_simulation = False
                self.debug_logging = True
            
            # 应用自定义配置
            for key, value in kwargs.items():
                if hasattr(self, key):
                    setattr(self, key, value)
                else:
                    self.custom_settings[key] = value
    
    def disable_test_mode(self):
        """关闭测试模式"""
        with self._lock:
            self.mode = TestMode.DISABLED
            self.mock_price_enabled = False
            self.fast_time_simulation = False
            self.debug_logging = False
            self.performance_tracking = False
            self.custom_settings.clear()
    
    def is_test_mode(self) -> bool:
        """检查是否处于测试模式"""
        return self.mode != TestMode.DISABLED
    
    def get_config(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        with self._lock:
            if hasattr(self, key):
                return getattr(self, key)
            return self.custom_settings.get(key, default)
    
    def set_config(self, key: str, value: Any):
        """设置配置值"""
        with self._lock:
            if hasattr(self, key):
                setattr(self, key, value)
            else:
                self.custom_settings[key] = value
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        with self._lock:
            return {
                'mode': self.mode.value,
                'mock_price_enabled': self.mock_price_enabled,
                'mock_data_seed': self.mock_data_seed,
                'fast_time_simulation': self.fast_time_simulation,
                'debug_logging': self.debug_logging,
                'performance_tracking': self.performance_tracking,
                'custom_settings': self.custom_settings.copy()
            }


# 全局测试配置实例
_test_config = TestConfig()


def enable_test_mode(mode: TestMode = TestMode.UNIT_TEST, **kwargs):
    """
    启用测试模式 - 全局函数
    
    Args:
        mode: 测试模式
        **kwargs: 其他配置参数
        
    Example:
        >>> enable_test_mode(TestMode.UNIT_TEST, mock_data_seed=12345)
        >>> enable_test_mode(TestMode.MOCK_TRADING, debug_logging=True)
    """
    _test_config.enable_test_mode(mode, **kwargs)


def disable_test_mode():
    """关闭测试模式 - 全局函数"""
    _test_config.disable_test_mode()


def is_test_mode() -> bool:
    """检查是否处于测试模式 - 全局函数"""
    return _test_config.is_test_mode()


def get_test_mode() -> TestMode:
    """获取当前测试模式"""
    return _test_config.mode


def get_test_config(key: str, default: Any = None) -> Any:
    """获取测试配置值"""
    return _test_config.get_config(key, default)


def set_test_config(key: str, value: Any):
    """设置测试配置值"""
    _test_config.set_config(key, value)


def get_all_test_config() -> Dict[str, Any]:
    """获取所有测试配置"""
    return _test_config.to_dict()


# 测试模式装饰器
def with_test_mode(mode: TestMode = TestMode.UNIT_TEST, **config_kwargs):
    """
    测试模式装饰器
    
    Args:
        mode: 测试模式
        **config_kwargs: 测试配置参数
    
    Example:
        >>> @with_test_mode(TestMode.UNIT_TEST, mock_data_seed=123)
        ... def test_trading():
        ...     # 测试代码
        ...     pass
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            # 保存原始状态
            original_mode = _test_config.mode
            original_config = _test_config.to_dict()
            
            try:
                # 启用测试模式
                enable_test_mode(mode, **config_kwargs)
                
                # 执行函数
                result = func(*args, **kwargs)
                
                return result
                
            finally:
                # 恢复原始状态
                if original_mode == TestMode.DISABLED:
                    disable_test_mode()
                else:
                    _test_config.enable_test_mode(original_mode, **original_config.get('custom_settings', {}))
        
        return wrapper
    return decorator


# 测试上下文管理器
class TestModeContext:
    """测试模式上下文管理器"""
    
    def __init__(self, mode: TestMode = TestMode.UNIT_TEST, **config_kwargs):
        self.mode = mode
        self.config_kwargs = config_kwargs
        self.original_mode = None
        self.original_config = None
    
    def __enter__(self):
        # 保存原始状态
        self.original_mode = _test_config.mode
        self.original_config = _test_config.to_dict()
        
        # 启用测试模式
        enable_test_mode(self.mode, **self.config_kwargs)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        # 恢复原始状态
        if self.original_mode == TestMode.DISABLED:
            disable_test_mode()
        else:
            _test_config.enable_test_mode(
                self.original_mode, 
                **self.original_config.get('custom_settings', {})
            )


# 便利函数
def test_mode_context(mode: TestMode = TestMode.UNIT_TEST, **config_kwargs):
    """
    创建测试模式上下文管理器
    
    Example:
        >>> with test_mode_context(TestMode.UNIT_TEST, mock_data_seed=123):
        ...     # 测试代码
        ...     account = create_test_account()
    """
    return TestModeContext(mode, **config_kwargs)