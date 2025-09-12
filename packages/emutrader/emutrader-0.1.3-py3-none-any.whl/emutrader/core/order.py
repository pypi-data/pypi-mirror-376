# -*- coding: utf-8 -*-
"""
订单相关类和枚举

定义订单类型、状态等常量，以及订单相关的便利函数。
"""

from enum import Enum
from typing import Dict, Any

# 从models模块导入Order类，这里主要定义枚举和工具函数
from .models import Order as OrderModel


class OrderType(Enum):
    """
    订单类型枚举 (JoinQuant兼容)
    """
    MARKET = "market"           # 市价单
    LIMIT = "limit"             # 限价单
    STOP = "stop"               # 停损单
    STOP_LIMIT = "stop_limit"   # 停损限价单


class OrderStatus(Enum):
    """
    订单状态枚举 (JoinQuant兼容)
    """
    NEW = "new"                 # 新建
    OPEN = "open"               # 未成交
    FILLED = "filled"           # 已成交
    CANCELLED = "cancelled"     # 已撤销
    REJECTED = "rejected"       # 已拒绝
    HELD = "held"              # 暂停


class OrderSide(Enum):
    """
    订单方向枚举
    """
    BUY = "buy"                # 买入
    SELL = "sell"              # 卖出


# 为了兼容性，提供Order类的别名
Order = OrderModel


def create_order(order_id, security, amount, price=None, order_type="market"):
    """
    创建订单的便利函数
    
    Args:
        order_id (str): 订单ID
        security (str): 证券代码
        amount (int): 数量
        price (float, optional): 价格
        order_type (str): 订单类型
        
    Returns:
        Order: 订单对象
    """
    return OrderModel(
        order_id=order_id,
        security=security,
        amount=amount,
        price=price,
        style=order_type
    )


def is_buy_order(order):
    """
    判断是否为买单
    
    Args:
        order (Order): 订单对象
        
    Returns:
        bool: 是否为买单
    """
    return order.amount > 0


def is_sell_order(order):
    """
    判断是否为卖单
    
    Args:
        order (Order): 订单对象
        
    Returns:
        bool: 是否为卖单
    """
    return order.amount < 0


def get_order_side(order):
    """
    获取订单方向
    
    Args:
        order (Order): 订单对象
        
    Returns:
        OrderSide: 订单方向
    """
    return OrderSide.BUY if is_buy_order(order) else OrderSide.SELL


def format_order_info(order):
    """
    格式化订单信息
    
    Args:
        order (Order): 订单对象
        
    Returns:
        str: 格式化后的订单信息
    """
    side = "买入" if is_buy_order(order) else "卖出"
    price_str = f"@{order.price:.3f}" if order.price else "@市价"
    
    return f"[{order.order_id[:8]}] {side} {order.security} {abs(order.amount)}股 {price_str} ({order.status})"


# JoinQuant兼容性常量
ORDER_TYPE_MARKET = OrderType.MARKET.value
ORDER_TYPE_LIMIT = OrderType.LIMIT.value

ORDER_STATUS_NEW = OrderStatus.NEW.value
ORDER_STATUS_OPEN = OrderStatus.OPEN.value
ORDER_STATUS_FILLED = OrderStatus.FILLED.value
ORDER_STATUS_CANCELLED = OrderStatus.CANCELLED.value
ORDER_STATUS_REJECTED = OrderStatus.REJECTED.value
ORDER_STATUS_HELD = OrderStatus.HELD.value