# -*- coding: utf-8 -*-
"""
结构化异常处理测试
"""

import pytest
from emutrader.exceptions import (
    EmuTraderException, TradingException, InsufficientFundsException,
    InsufficientPositionException, InvalidSecurityException, ContextException,
    SubPortfolioException, PortfolioException, ConfigurationException
)
from emutrader.constants import ErrorCodes
from emutrader.api import get_jq_account, order_shares, set_current_context, set_strict_mode
from emutrader.testing import enable_test_mode, disable_test_mode, TestMode


class TestExceptionHierarchy:
    """测试异常类层次结构"""
    
    def test_base_exception_creation(self):
        """测试基础异常创建"""
        exception = EmuTraderException(
            "测试异常消息",
            error_code=ErrorCodes.UNKNOWN_ERROR,
            details={'test_key': 'test_value'},
            suggestions=["建议1", "建议2"]
        )
        
        assert exception.message == "测试异常消息"
        assert exception.error_code == ErrorCodes.UNKNOWN_ERROR
        assert exception.details['test_key'] == 'test_value'
        assert len(exception.suggestions) == 2
        assert "建议1" in exception.suggestions
    
    def test_exception_string_formatting(self):
        """测试异常字符串格式化"""
        exception = EmuTraderException(
            "测试消息",
            error_code=ErrorCodes.VALIDATION_ERROR,
            details={'field': 'test_field'},
            suggestions=["检查输入"]
        )
        
        str_repr = str(exception)
        assert str(ErrorCodes.VALIDATION_ERROR) in str_repr
        assert "测试消息" in str_repr
        assert "检查输入" in str_repr
    
    def test_exception_to_dict(self):
        """测试异常转换为字典"""
        exception = TradingException(
            "交易失败",
            security="000001.SZ",
            amount=1000,
            price=12.5
        )
        
        exception_dict = exception.to_dict()
        
        assert exception_dict['message'] == "交易失败"
        assert exception_dict['error_code'] == ErrorCodes.TRADING_ERROR
        assert exception_dict['exception_type'] == 'TradingException'
        assert exception_dict['details']['security'] == "000001.SZ"
        assert exception_dict['details']['amount'] == 1000
        assert exception_dict['details']['price'] == 12.5


class TestTradingExceptions:
    """测试交易相关异常"""
    
    def setup_method(self):
        """每个测试前的设置"""
        enable_test_mode(TestMode.UNIT_TEST, mock_price_enabled=True)
        set_strict_mode(True)  # 启用严格模式以测试异常抛出
    
    def teardown_method(self):
        """每个测试后的清理"""
        disable_test_mode()
        set_strict_mode(False)  # 禁用严格模式
        # 清理全局上下文
        from emutrader.api import _current_context
        global _current_context
        _current_context = None
    
    def test_insufficient_funds_exception(self):
        """测试资金不足异常"""
        exception = InsufficientFundsException(10000, 5000, "000001.SZ")
        
        assert exception.error_code == ErrorCodes.INSUFFICIENT_FUNDS
        assert exception.details['required_amount'] == 10000
        assert exception.details['available_amount'] == 5000
        assert exception.details['shortage'] == 5000
        assert exception.details['security'] == "000001.SZ"
        assert "减少交易数量" in exception.suggestions
    
    def test_insufficient_position_exception(self):
        """测试持仓不足异常"""
        exception = InsufficientPositionException(1000, 500, "000002.SZ")
        
        assert exception.error_code == ErrorCodes.INSUFFICIENT_POSITION
        assert exception.details['required_amount'] == 1000
        assert exception.details['available_amount'] == 500
        assert exception.details['security'] == "000002.SZ"
        assert "减少卖出数量" in exception.suggestions
    
    def test_invalid_security_exception(self):
        """测试无效证券代码异常"""
        exception = InvalidSecurityException("INVALID_CODE")
        
        assert exception.error_code == ErrorCodes.INVALID_SECURITY
        assert exception.details['security'] == "INVALID_CODE"
        assert "检查证券代码格式" in exception.suggestions[0]
    
    def test_context_not_set_exception(self):
        """测试上下文未设置异常"""
        # 确保没有设置上下文
        set_current_context(None)
        with pytest.raises(ContextException) as exc_info:
            order_shares("000001.SZ", 1000)
        
        exception = exc_info.value
        assert exception.error_code == ErrorCodes.CONTEXT_ERROR
        assert "策略上下文未设置" in exception.message
        assert "get_jq_account()" in str(exception.suggestions)
    
    def test_invalid_security_in_order(self):
        """测试下单时无效证券代码"""
        # 创建上下文
        context = get_jq_account("test", 100000)
        set_current_context(context)
        
        # 测试无效证券代码
        with pytest.raises(InvalidSecurityException) as exc_info:
            order_shares("INVALID", 1000)
        
        exception = exc_info.value
        assert exception.error_code == ErrorCodes.INVALID_SECURITY
        assert "INVALID" in exception.details['security']
    
    def test_insufficient_funds_in_order(self):
        """测试下单时资金不足"""
        # 创建小额资金账户
        context = get_jq_account("test", 1000)  # 只有1000元
        set_current_context(context)
        
        # 尝试买入超出资金的股票
        with pytest.raises(InsufficientFundsException) as exc_info:
            order_shares("000001.SZ", 1000)  # 需要10000元
        
        exception = exc_info.value
        assert exception.error_code == ErrorCodes.INSUFFICIENT_FUNDS
        assert exception.details['required_amount'] > 1000
        assert exception.details['available_amount'] == 1000


class TestContextExceptions:
    """测试策略上下文异常"""
    
    def test_context_exception_creation(self):
        """测试上下文异常创建"""
        exception = ContextException(
            "上下文错误",
            context_name="test_context"
        )
        
        assert exception.error_code == ErrorCodes.CONTEXT_ERROR
        assert exception.details['context_name'] == "test_context"
        assert "确保在交易前设置策略上下文" in exception.suggestions


class TestSubPortfolioExceptions:
    """测试子账户异常"""
    
    def test_subportfolio_exception_creation(self):
        """测试子账户异常创建"""
        exception = SubPortfolioException(
            "子账户不存在",
            subportfolio_index=0,
            subportfolio_type="STOCK"
        )
        
        assert exception.error_code == ErrorCodes.SUBPORTFOLIO_ERROR
        assert exception.details['subportfolio_index'] == 0
        assert exception.details['subportfolio_type'] == "STOCK"
        assert "检查子账户配置" in exception.suggestions[0]


class TestConfigurationExceptions:
    """测试配置异常"""
    
    def test_configuration_exception_creation(self):
        """测试配置异常创建"""
        exception = ConfigurationException(
            "配置参数错误",
            config_key="database_url",
            config_value="invalid_url"
        )
        
        assert exception.error_code == ErrorCodes.CONFIGURATION_ERROR
        assert exception.details['config_key'] == "database_url"
        assert exception.details['config_value'] == "invalid_url"
        assert "检查配置文件" in exception.suggestions[0]


class TestExceptionUtilities:
    """测试异常处理工具函数"""
    
    def test_format_exception_for_logging(self):
        """测试异常格式化用于日志"""
        from emutrader.exceptions import format_exception_for_logging
        
        # 测试EmuTrader异常
        emutrader_exception = TradingException("测试交易异常")
        formatted = format_exception_for_logging(emutrader_exception)
        
        assert formatted['error_code'] == ErrorCodes.TRADING_ERROR
        assert formatted['message'] == "测试交易异常"
        assert formatted['exception_type'] == 'TradingException'
        
        # 测试普通异常
        normal_exception = ValueError("普通错误")
        formatted = format_exception_for_logging(normal_exception)
        
        assert formatted['error_code'] == ErrorCodes.UNKNOWN_ERROR
        assert formatted['message'] == "普通错误"
        assert formatted['exception_type'] == 'ValueError'
        assert "查看详细日志信息" in formatted['suggestions']
    
    def test_exception_decorator(self):
        """测试异常处理装饰器"""
        from emutrader.exceptions import handle_exceptions
        
        @handle_exceptions(TradingException, "交易操作失败")
        def risky_trading_operation():
            raise ValueError("底层错误")
        
        with pytest.raises(TradingException) as exc_info:
            risky_trading_operation()
        
        exception = exc_info.value
        assert "交易操作失败" in exception.message
        assert "底层错误" in exception.details['original_exception']


class TestExceptionIntegration:
    """测试异常处理集成"""
    
    def setup_method(self):
        enable_test_mode(TestMode.UNIT_TEST, mock_price_enabled=True)
        set_strict_mode(True)  # 启用严格模式以测试异常抛出
    
    def teardown_method(self):
        disable_test_mode()
        set_strict_mode(False)  # 禁用严格模式
    
    def test_complete_error_workflow(self):
        """测试完整的错误处理工作流"""
        # 0. 确保上下文被清理
        set_current_context(None)
        
        # 1. 测试上下文未设置错误
        with pytest.raises(ContextException):
            order_shares("000001.SZ", 1000)
        
        # 2. 创建上下文
        context = get_jq_account("error_test", 5000)
        set_current_context(context)
        
        # 3. 测试无效证券代码
        with pytest.raises(InvalidSecurityException):
            order_shares("INVALID", 100)
        
        # 4. 测试资金不足
        with pytest.raises(InsufficientFundsException):
            order_shares("000001.SZ", 1000)  # 需要10000元，只有5000元
        
        # 5. 成功交易
        order = order_shares("000001.SZ", 100)  # 使用100股确保不超过资金
        assert order is not None
        assert order.security == "000001.SZ"
        assert order.amount == 100


if __name__ == "__main__":
    # 运行一些基本测试
    print("测试异常处理功能...")
    
    # 测试基础异常
    exc = TradingException("测试", security="000001.SZ")
    print(f"异常信息: {exc}")
    print(f"异常字典: {exc.to_dict()}")
    
    # 测试特定异常
    funds_exc = InsufficientFundsException(10000, 5000, "000001.SZ")
    print(f"资金不足异常: {funds_exc}")
    
    print("异常处理测试完成！")