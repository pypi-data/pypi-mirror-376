"""
账户处理器工厂

根据账户类型创建相应的处理器实例
"""

from typing import Dict, Type, Optional

from .base import BaseAccountHandler
from .stock import StockAccountHandler
from .future import FutureAccountHandler
from .credit import CreditAccountHandler
from ..exceptions import ValidationException


class AccountHandlerFactory:
    """
    账户处理器工厂类
    
    负责根据账户类型创建对应的处理器实例
    """
    
    # 账户类型到处理器类的映射
    _handlers = {
        'STOCK': StockAccountHandler,
        'FUTURE': FutureAccountHandler,
        'CREDIT': CreditAccountHandler,
        # 'OPTION': OptionAccountHandler,  # 待实现
        # 'CRYPTO': CryptoAccountHandler,  # 待实现
    }
    
    @classmethod
    def create_handler(cls, account_type, strategy_name, account_id, initial_cash=100000):
        """
        创建账户处理器
        
        Args:
            account_type (str): 账户类型 (STOCK/FUTURE/CREDIT/OPTION/CRYPTO)
            strategy_name (str): 策略名称
            account_id (int): 账户ID
            initial_cash (float): 初始资金
            
        Returns:
            BaseAccountHandler: 对应的账户处理器实例
            
        Raises:
            ValidationException: 不支持的账户类型
        """
        if account_type not in cls._handlers:
            raise ValidationException(
                f"不支持的账户类型: {account_type}",
                field_name="account_type",
                field_value=account_type,
                suggestions=[f"支持的类型: {list(cls._handlers.keys())}"]
            )
        
        handler_class = cls._handlers[account_type]
        
        # 根据处理器类型传递参数
        if account_type == 'STOCK':
            return handler_class(strategy_name, account_id, initial_cash)
        else:
            # 其他处理器暂时使用原有接口
            return handler_class(strategy_name, account_id)
    
    @classmethod
    def get_supported_types(cls):
        """获取支持的账户类型列表"""
        return list(cls._handlers.keys())
    
    @classmethod
    def register_handler(cls, account_type, handler_class):
        """
        注册新的账户处理器
        
        Args:
            account_type (str): 账户类型
            handler_class (Type[BaseAccountHandler]): 处理器类
        """
        if not issubclass(handler_class, BaseAccountHandler):
            raise TypeError("处理器类必须继承自 BaseAccountHandler")
        
        cls._handlers[account_type] = handler_class
    
    @classmethod
    def is_supported(cls, account_type):
        """检查账户类型是否被支持"""
        return account_type in cls._handlers
    
    @classmethod
    def get_handler_info(cls):
        """获取所有处理器的详细信息"""
        info = {}
        for account_type, handler_class in cls._handlers.items():
            info[account_type] = {
                'class_name': handler_class.__name__,
                'module': handler_class.__module__,
                'description': getattr(handler_class, '__doc__', '').split('\n')[0].strip()
            }
        return info


# 便利函数
def create_account_handler(account_type, strategy_name, account_id):
    """
    创建账户处理器的便利函数
    
    Args:
        account_type (str): 账户类型
        strategy_name (str): 策略名称  
        account_id (int): 账户ID
        
    Returns:
        BaseAccountHandler: 账户处理器实例
    """
    return AccountHandlerFactory.create_handler(account_type, strategy_name, account_id)


def get_account_types():
    """获取所有支持的账户类型"""
    return AccountHandlerFactory.get_supported_types()


# 使用示例
def demo_usage():
    """演示如何使用账户处理器工厂"""
    print("=== 账户处理器工厂使用示例 ===")
    
    # 1. 查看支持的账户类型
    supported_types = get_account_types()
    print("支持的账户类型:", supported_types)
    
    # 2. 创建不同类型的处理器
    stock_handler = create_account_handler("STOCK", "test_strategy", 0)
    future_handler = create_account_handler("FUTURE", "test_strategy", 1)
    credit_handler = create_account_handler("CREDIT", "test_strategy", 2)
    
    print("股票处理器:", type(stock_handler).__name__)
    print("期货处理器:", type(future_handler).__name__)
    print("信用处理器:", type(credit_handler).__name__)
    
    # 3. 查看处理器详细信息
    handler_info = AccountHandlerFactory.get_handler_info()
    for account_type, info in handler_info.items():
        print("账户类型 {}: {} - {}".format(
            account_type, info['class_name'], info['description']))


if __name__ == '__main__':
    demo_usage()