# -*- coding: utf-8 -*-
"""
JoinQuant 兼容API

提供与JoinQuant平台100%兼容的API接口。
"""

from typing import Optional, Dict, Any
from .core.account import Account
from .exceptions import ValidationException


def get_jq_account(strategy_name: str, initial_cash: float = 100000, 
                   account_type: str = "STOCK") -> Account:
    """
    获取JoinQuant兼容的账户对象
    
    这是EmuTrader的核心API，提供与JoinQuant完全兼容的账户接口。
    
    Args:
        strategy_name (str): 策略名称
        initial_cash (float): 初始资金，默认10万
        account_type (str): 账户类型，支持 STOCK/FUTURE/CREDIT
        
    Returns:
        Account: JoinQuant兼容的账户对象
        
    Example:
        >>> account = get_jq_account("my_strategy", 100000, "STOCK")
        >>> print(account.account_info.total_value)
        100000.0
        >>> order_id = account.order_shares("000001.SZ", 1000)
    """
    # 参数验证
    if not strategy_name:
        raise ValidationException("策略名称不能为空")
    
    if initial_cash <= 0:
        raise ValidationException("初始资金必须大于0")
    
    supported_types = ["STOCK", "FUTURE", "CREDIT"]
    if account_type not in supported_types:
        raise ValidationException(
            f"不支持的账户类型: {account_type}",
            field_name="account_type",
            field_value=account_type,
            suggestions=[f"支持的类型: {supported_types}"]
        )
    
    # 创建账户实例
    account = Account(
        strategy_name=strategy_name,
        initial_cash=initial_cash,
        account_type=account_type
    )
    
    return account


# JoinQuant兼容的全局函数（模拟JQ环境）
def order_shares(security: str, amount: int, price: Optional[float] = None) -> str:
    """
    JoinQuant兼容的下单函数
    
    注意：这个函数需要在策略上下文中使用，或者需要设置全局账户。
    建议使用 account.order_shares() 方法。
    
    Args:
        security (str): 证券代码
        amount (int): 股票数量
        price (float, optional): 价格
        
    Returns:
        str: 订单ID
    """
    # 这里需要访问当前策略的账户上下文
    # 实际使用中建议直接使用 account.order_shares()
    raise NotImplementedError(
        "请使用 account.order_shares() 方法，或在策略上下文中调用"
    )


def order_value(security: str, value: float, price: Optional[float] = None) -> str:
    """
    JoinQuant兼容的按金额下单函数
    
    Args:
        security (str): 证券代码
        value (float): 交易金额
        price (float, optional): 价格
        
    Returns:
        str: 订单ID
    """
    raise NotImplementedError(
        "请使用 account.order_value() 方法，或在策略上下文中调用"
    )


# 兼容性别名
create_jq_account = get_jq_account  # 别名