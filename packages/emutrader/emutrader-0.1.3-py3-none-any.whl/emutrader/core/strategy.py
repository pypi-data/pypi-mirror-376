# -*- coding: utf-8 -*-
"""
策略基类

定义交易策略的标准接口。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from datetime import datetime


class Strategy(ABC):
    """
    策略抽象基类
    
    所有交易策略都应该继承这个基类并实现必要的方法。
    """
    
    def __init__(self, name="default_strategy"):
        """
        初始化策略
        
        Args:
            name (str): 策略名称
        """
        self.name = name
        self.context = None  # 策略上下文，在运行时设置
        
    def initialize(self, context):
        """
        策略初始化方法
        
        在策略开始运行前调用，用于设置初始参数。
        
        Args:
            context: 策略运行上下文
        """
        self.context = context
        
    @abstractmethod
    def handle_data(self, context, data):
        """
        数据处理方法 (JoinQuant兼容)
        
        每个交易周期都会调用此方法。
        
        Args:
            context: 策略运行上下文
            data: 市场数据
        """
        pass
    
    def on_bar(self, data):
        """
        K线数据处理方法
        
        Args:
            data: K线数据
        """
        # 默认调用handle_data保持兼容性
        if self.context:
            self.handle_data(self.context, data)
    
    def before_trading_start(self, context, data):
        """
        开盘前处理方法
        
        Args:
            context: 策略运行上下文
            data: 市场数据
        """
        pass
    
    def after_trading_end(self, context, data):
        """
        收盘后处理方法
        
        Args:
            context: 策略运行上下文
            data: 市场数据
        """
        pass
    
    def on_order_response(self, order):
        """
        订单回报处理方法
        
        Args:
            order: 订单对象
        """
        pass
    
    def log_info(self, message):
        """
        记录信息日志
        
        Args:
            message (str): 日志消息
        """
        print(f"[{datetime.now()}] {self.name}: {message}")
    
    def __repr__(self):
        return f"Strategy(name={self.name})"


class SimpleStrategy(Strategy):
    """
    简单策略示例
    
    演示如何继承Strategy基类实现具体策略。
    """
    
    def handle_data(self, context, data):
        """
        简单的移动平均策略示例
        """
        # 这里是示例代码，实际策略逻辑需要根据具体需求实现
        pass