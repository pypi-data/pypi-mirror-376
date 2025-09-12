# -*- coding: utf-8 -*-
"""
EmuTrader 异常处理系统

统一的异常定义和处理机制，提供详细的错误信息和处理建议。
"""

from .constants import ErrorCodes


class EmuTraderException(Exception):
    """
    EmuTrader基础异常类
    
    所有EmuTrader相关异常的基类，提供统一的异常处理接口。
    """
    
    def __init__(self, message, error_code=None, details=None, suggestions=None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code or ErrorCodes.UNKNOWN_ERROR
        self.details = details or {}
        self.suggestions = suggestions or []
        
    def __str__(self):
        """格式化异常信息"""
        parts = [f"[{self.error_code}] {self.message}"]
        
        if self.details:
            parts.append(f"Details: {self.details}")
            
        if self.suggestions:
            parts.append(f"Suggestions: {'; '.join(self.suggestions)}")
            
        return " | ".join(parts)
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            "error_code": self.error_code,
            "message": self.message,
            "details": self.details,
            "suggestions": self.suggestions,
            "exception_type": self.__class__.__name__
        }


class StorageException(EmuTraderException):
    """
    存储相关异常
    
    数据库连接、查询、事务等存储操作失败时抛出。
    """
    
    def __init__(self, message, error_code=None, **kwargs):
        error_code = error_code or ErrorCodes.STORAGE_ERROR
        super().__init__(message, error_code, **kwargs)


class DatabaseException(StorageException):
    """数据库操作异常"""
    
    def __init__(self, message, sql=None, params=None, **kwargs):
        error_code = kwargs.get('error_code', ErrorCodes.DATABASE_ERROR)
        details = kwargs.get('details', {})
        
        if sql:
            details['sql'] = sql
        if params:
            details['params'] = params
            
        suggestions = kwargs.get('suggestions', [
            "检查数据库连接是否正常",
            "验证SQL语法是否正确", 
            "确认数据库表结构是否匹配"
        ])
        
        super().__init__(
            message, 
            error_code=error_code,
            details=details,
            suggestions=suggestions
        )


class ConnectionException(StorageException):
    """数据库连接异常"""
    
    def __init__(self, message, connection_string=None, **kwargs):
        error_code = kwargs.get('error_code', ErrorCodes.CONNECTION_ERROR)
        details = kwargs.get('details', {})
        
        if connection_string:
            details['connection_string'] = connection_string
            
        suggestions = kwargs.get('suggestions', [
            "检查数据库文件路径是否正确",
            "确认数据库文件权限是否足够",
            "验证数据库服务是否正在运行"
        ])
        
        super().__init__(
            message,
            error_code=error_code, 
            details=details,
            suggestions=suggestions
        )


class AdapterException(EmuTraderException):
    """
    适配器相关异常
    
    平台API调用、数据适配、接口不兼容等情况时抛出。
    """
    
    def __init__(self, message, adapter_type=None, platform=None, **kwargs):
        error_code = kwargs.get('error_code', ErrorCodes.ADAPTER_ERROR)
        details = kwargs.get('details', {})
        
        if adapter_type:
            details['adapter_type'] = adapter_type
        if platform:
            details['platform'] = platform
            
        suggestions = kwargs.get('suggestions', [
            "检查平台API是否可用",
            "验证适配器配置是否正确",
            "确认平台版本是否兼容"
        ])
        
        super().__init__(
            message,
            error_code=error_code,
            details=details, 
            suggestions=suggestions
        )


class PlatformException(AdapterException):
    """平台API异常"""
    
    def __init__(self, message, api_method=None, response_code=None, **kwargs):
        error_code = kwargs.get('error_code', ErrorCodes.PLATFORM_ERROR)
        details = kwargs.get('details', {})
        
        if api_method:
            details['api_method'] = api_method
        if response_code:
            details['response_code'] = response_code
            
        suggestions = kwargs.get('suggestions', [
            "检查API接口是否正常",
            "验证API参数是否正确",
            "确认账户权限是否足够"
        ])
        
        super().__init__(
            message,
            error_code=error_code,
            details=details,
            suggestions=suggestions
        )


class ValidationException(EmuTraderException):
    """
    数据验证异常
    
    数据格式错误、参数无效、业务规则违反等情况时抛出。
    """
    
    def __init__(self, message, field_name=None, field_value=None, **kwargs):
        error_code = kwargs.get('error_code', ErrorCodes.VALIDATION_ERROR)
        details = kwargs.get('details', {})
        
        if field_name:
            details['field_name'] = field_name
        if field_value is not None:
            details['field_value'] = field_value
            
        suggestions = kwargs.get('suggestions', [
            "检查输入参数的格式和范围",
            "参考API文档确认参数要求",
            "验证数据是否符合业务规则"
        ])
        
        super().__init__(
            message,
            error_code=error_code,
            details=details,
            suggestions=suggestions
        )


class DataIntegrityException(ValidationException):
    """数据完整性异常"""
    
    def __init__(self, message, **kwargs):
        error_code = kwargs.get('error_code', ErrorCodes.DATA_INTEGRITY_ERROR)
        suggestions = kwargs.get('suggestions', [
            "检查数据是否完整一致",
            "验证关联数据是否存在",
            "确认数据约束是否满足"
        ])
        
        super().__init__(
            message,
            error_code=error_code,
            suggestions=suggestions,
            **kwargs
        )


class CacheException(EmuTraderException):
    """
    缓存相关异常
    
    缓存操作失败、缓存过期、缓存溢出等情况时抛出。
    """
    
    def __init__(self, message, cache_key=None, cache_type=None, **kwargs):
        error_code = kwargs.get('error_code', ErrorCodes.CACHE_ERROR)
        details = kwargs.get('details', {})
        
        if cache_key:
            details['cache_key'] = cache_key
        if cache_type:
            details['cache_type'] = cache_type
            
        suggestions = kwargs.get('suggestions', [
            "检查缓存配置是否正确",
            "验证缓存大小是否合理",
            "考虑清理缓存重新加载"
        ])
        
        super().__init__(
            message,
            error_code=error_code,
            details=details,
            suggestions=suggestions
        )


class CacheMissException(CacheException):
    """缓存未命中异常"""
    
    def __init__(self, message, **kwargs):
        error_code = kwargs.get('error_code', ErrorCodes.CACHE_MISS)
        suggestions = kwargs.get('suggestions', [
            "尝试从存储层重新加载数据",
            "检查缓存过期时间设置",
            "验证缓存键是否正确"
        ])
        
        super().__init__(
            message,
            error_code=error_code,
            suggestions=suggestions,
            **kwargs
        )


class CacheExpiredException(CacheException):
    """缓存过期异常"""
    
    def __init__(self, message, **kwargs):
        error_code = kwargs.get('error_code', ErrorCodes.CACHE_EXPIRED)
        suggestions = kwargs.get('suggestions', [
            "重新加载最新数据",
            "调整缓存过期时间",
            "考虑使用自动刷新机制"
        ])
        
        super().__init__(
            message,
            error_code=error_code,
            suggestions=suggestions,
            **kwargs
        )


class TradingException(EmuTraderException):
    """
    交易相关异常
    
    订单执行失败、资金不足、持仓不足等交易操作异常。
    """
    
    def __init__(self, message, security=None, amount=None, price=None, **kwargs):
        error_code = kwargs.get('error_code', ErrorCodes.TRADING_ERROR)
        details = kwargs.get('details', {})
        
        if security:
            details['security'] = security
        if amount is not None:
            details['amount'] = amount
        if price is not None:
            details['price'] = price
            
        suggestions = kwargs.get('suggestions', [
            "检查账户资金是否充足",
            "验证证券代码是否正确",
            "确认交易时间是否在有效期内"
        ])
        
        super().__init__(
            message,
            error_code=error_code,
            details=details,
            suggestions=suggestions
        )


class InsufficientFundsException(TradingException):
    """资金不足异常"""
    
    def __init__(self, required_amount, available_amount, security=None, **kwargs):
        message = f"资金不足: 需要 {required_amount:.2f}, 可用 {available_amount:.2f}"
        error_code = kwargs.get('error_code', ErrorCodes.INSUFFICIENT_FUNDS)
        
        details = {
            'required_amount': required_amount,
            'available_amount': available_amount,
            'shortage': required_amount - available_amount
        }
        if security:
            details['security'] = security
        
        suggestions = [
            "减少交易数量",
            "增加账户资金",
            "检查其他交易是否占用资金"
        ]
        
        super().__init__(
            message,
            error_code=error_code,
            details=details,
            suggestions=suggestions,
            **kwargs
        )


class InsufficientPositionException(TradingException):
    """持仓不足异常"""
    
    def __init__(self, required_amount, available_amount, security, **kwargs):
        message = f"持仓不足: {security} 需要卖出 {required_amount}, 可卖 {available_amount}"
        error_code = kwargs.get('error_code', ErrorCodes.INSUFFICIENT_POSITION)
        
        details = {
            'required_amount': required_amount,
            'available_amount': available_amount,
            'shortage': required_amount - available_amount,
            'security': security
        }
        
        suggestions = [
            "减少卖出数量",
            "检查持仓是否被冻结",
            "确认持仓数据是否最新"
        ]
        
        super().__init__(
            message,
            error_code=error_code,
            details=details,
            suggestions=suggestions,
            **kwargs
        )


class InvalidSecurityException(TradingException):
    """无效证券代码异常"""
    
    def __init__(self, security, **kwargs):
        message = f"无效的证券代码: {security}"
        error_code = kwargs.get('error_code', ErrorCodes.INVALID_SECURITY)
        
        details = {'security': security}
        
        suggestions = [
            "检查证券代码格式是否正确",
            "确认证券代码是否存在",
            "验证交易所后缀 (.SZ/.SH)"
        ]
        
        super().__init__(
            message,
            security=security,
            error_code=error_code,
            details=details,
            suggestions=suggestions,
            **kwargs
        )


class OrderException(TradingException):
    """订单异常"""
    
    def __init__(self, message, order_id=None, order_status=None, **kwargs):
        error_code = kwargs.get('error_code', ErrorCodes.ORDER_ERROR)
        details = kwargs.get('details', {})
        
        if order_id:
            details['order_id'] = order_id
        if order_status:
            details['order_status'] = order_status
            
        suggestions = kwargs.get('suggestions', [
            "检查订单状态",
            "验证订单参数",
            "确认交易权限"
        ])
        
        super().__init__(
            message,
            error_code=error_code,
            details=details,
            suggestions=suggestions
        )


class ContextException(EmuTraderException):
    """
    策略上下文异常
    
    上下文未设置、上下文状态错误等。
    """
    
    def __init__(self, message, context_name=None, **kwargs):
        error_code = kwargs.get('error_code', ErrorCodes.CONTEXT_ERROR)
        details = kwargs.get('details', {})
        
        if context_name:
            details['context_name'] = context_name
            
        suggestions = kwargs.get('suggestions', [
            "确保在交易前设置策略上下文",
            "使用 get_jq_account() 创建上下文",
            "检查上下文是否已正确初始化"
        ])
        
        super().__init__(
            message,
            error_code=error_code,
            details=details,
            suggestions=suggestions
        )


class SubPortfolioException(EmuTraderException):
    """
    子账户异常
    
    子账户配置错误、资金转移失败等。
    """
    
    def __init__(self, message, subportfolio_index=None, subportfolio_type=None, **kwargs):
        error_code = kwargs.get('error_code', ErrorCodes.SUBPORTFOLIO_ERROR)
        details = kwargs.get('details', {})
        
        if subportfolio_index is not None:
            details['subportfolio_index'] = subportfolio_index
        if subportfolio_type:
            details['subportfolio_type'] = subportfolio_type
            
        suggestions = kwargs.get('suggestions', [
            "检查子账户配置是否正确",
            "验证子账户索引是否有效",
            "确认子账户类型是否支持"
        ])
        
        super().__init__(
            message,
            error_code=error_code,
            details=details,
            suggestions=suggestions
        )


class PortfolioException(EmuTraderException):
    """
    投资组合异常
    
    投资组合状态错误、数据不一致等。
    """
    
    def __init__(self, message, portfolio_type=None, **kwargs):
        error_code = kwargs.get('error_code', ErrorCodes.PORTFOLIO_ERROR)
        details = kwargs.get('details', {})
        
        if portfolio_type:
            details['portfolio_type'] = portfolio_type
            
        suggestions = kwargs.get('suggestions', [
            "检查投资组合数据一致性",
            "验证资金和持仓计算",
            "确认投资组合状态更新"
        ])
        
        super().__init__(
            message,
            error_code=error_code,
            details=details,
            suggestions=suggestions
        )


class ConfigurationException(EmuTraderException):
    """
    配置异常
    
    配置参数错误、配置文件缺失等。
    """
    
    def __init__(self, message, config_key=None, config_value=None, **kwargs):
        error_code = kwargs.get('error_code', ErrorCodes.CONFIGURATION_ERROR)
        details = kwargs.get('details', {})
        
        if config_key:
            details['config_key'] = config_key
        if config_value is not None:
            details['config_value'] = config_value
            
        suggestions = kwargs.get('suggestions', [
            "检查配置文件是否存在",
            "验证配置参数格式",
            "参考文档设置正确的配置值"
        ])
        
        super().__init__(
            message,
            error_code=error_code,
            details=details,
            suggestions=suggestions
        )


# 便利函数：异常处理装饰器
def handle_exceptions(exception_type=EmuTraderException, default_message="操作失败"):
    """
    异常处理装饰器
    
    Args:
        exception_type: 要捕获并转换的异常类型
        default_message: 默认错误消息
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except exception_type:
                # 如果已经是指定的异常类型，直接重新抛出
                raise
            except Exception as e:
                # 转换为指定的异常类型
                raise exception_type(
                    f"{default_message}: {str(e)}",
                    details={'original_exception': str(e)}
                ) from e
        return wrapper
    return decorator


def format_exception_for_logging(exception):
    """
    格式化异常信息用于日志记录
    
    Args:
        exception: 异常实例
        
    Returns:
        dict: 格式化后的异常信息
    """
    if isinstance(exception, EmuTraderException):
        return exception.to_dict()
    else:
        return {
            "error_code": ErrorCodes.UNKNOWN_ERROR,
            "message": str(exception),
            "exception_type": exception.__class__.__name__,
            "details": {},
            "suggestions": ["查看详细日志信息", "联系技术支持"]
        }