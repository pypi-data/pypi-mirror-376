# -*- coding: utf-8 -*-
"""
数据提供者

为账户管理提供基本的价格数据获取功能。
支持多种数据源，包括Mock、Tushare等。
"""

from typing import Dict, Optional, Any
from datetime import datetime

from ..exceptions import EmuTraderException


class DataProvider:
    """
    数据提供者
    
    为账户管理系统提供基本的价格数据接口。
    支持多种数据源的集成。
    """
    
    def __init__(self, source="mock", adapter=None):
        """
        初始化数据提供者
        
        Args:
            source (str): 数据源类型 (mock, tushare, yfinance)
            adapter: 适配器实例，用于获取实时数据
        """
        self.source = source
        self.adapter = adapter
        
        # 初始化数据源
        if source == "mock":
            self._init_mock_data()
        elif source == "tushare":
            self._init_tushare()
        elif source == "yfinance":
            self._init_yfinance()
    
    def _init_mock_data(self):
        """初始化模拟数据源"""
        # 如果有适配器，优先使用适配器
        if self.adapter and hasattr(self.adapter, 'get_current_price'):
            return
        
        # 默认模拟价格
        self._mock_prices = {
            '000001.XSHE': 10.0,
            '000002.XSHE': 15.0,
            '000003.XSHE': 20.0,
            '600000.XSHG': 8.5,
            '600036.XSHG': 35.0
        }
        
    def _init_tushare(self):
        """初始化Tushare数据源"""
        # 这里可以集成Tushare API
        # import tushare as ts
        # self.ts_pro = ts.pro_api('your_token')
        pass
        
    def _init_yfinance(self):
        """初始化yfinance数据源"""
        # 这里可以集成yfinance
        # import yfinance as yf
        pass
        
    def get_current_price(self, security: str) -> float:
        """
        获取证券当前价格
        
        Args:
            security (str): 证券代码
            
        Returns:
            float: 当前价格
        """
        try:
            # 优先使用适配器获取价格
            if self.adapter and hasattr(self.adapter, 'get_current_price'):
                return self.adapter.get_current_price(security)
            
            # 根据数据源类型获取价格
            if self.source == "mock":
                return self._get_mock_price(security)
            elif self.source == "tushare":
                return self._get_tushare_price(security)
            elif self.source == "yfinance":
                return self._get_yfinance_price(security)
            else:
                return self._get_mock_price(security)
                
        except Exception as e:
            # 如果获取失败，返回模拟价格
            return self._get_mock_price(security)
    
    def _get_mock_price(self, security: str) -> float:
        """获取模拟价格"""
        import random
        
        # 如果有预设价格，在其基础上波动
        if hasattr(self, '_mock_prices') and security in self._mock_prices:
            base_price = self._mock_prices[security]
            fluctuation = random.uniform(-0.02, 0.02)  # ±2%波动
            return round(base_price * (1 + fluctuation), 3)
        
        # 新股票，生成随机价格
        base_price = random.uniform(5.0, 50.0)
        if hasattr(self, '_mock_prices'):
            self._mock_prices[security] = base_price
        return round(base_price, 3)
    
    def _get_tushare_price(self, security: str) -> float:
        """从Tushare获取价格"""
        # TODO: 实现Tushare数据获取
        return self._get_mock_price(security)
    
    def _get_yfinance_price(self, security: str) -> float:
        """从yfinance获取价格"""
        # TODO: 实现yfinance数据获取
        return self._get_mock_price(security)
    
    def get_price_info(self, security: str) -> Dict[str, Any]:
        """
        获取证券价格信息
        
        Args:
            security (str): 证券代码
            
        Returns:
            dict: 价格信息
        """
        current_price = self.get_current_price(security)
        info = {
            "security": security,
            "price": current_price,
            "timestamp": datetime.now(),
            "source": self.source
        }
        
        # 如果有适配器，获取更多市场数据
        if self.adapter and hasattr(self.adapter, 'get_market_data'):
            try:
                market_data = self.adapter.get_market_data(security)
                info.update(market_data)
            except:
                pass
        
        return info
    
    def validate_security(self, security: str) -> bool:
        """
        验证证券代码是否有效
        
        Args:
            security (str): 证券代码
            
        Returns:
            bool: 是否有效
        """
        # 优先使用适配器验证
        if self.adapter and hasattr(self.adapter, 'validate_security'):
            return self.adapter.validate_security(security)
        
        # 简单的证券代码格式验证
        if not security or len(security) < 6:
            return False
        
        # 检查格式：6位数字.交易所代码
        parts = security.split('.')
        if len(parts) != 2:
            return False
        
        code, exchange = parts
        if not code.isdigit() or len(code) != 6:
            return False
        
        if exchange not in ['XSHE', 'XSHG']:  # 深交所和上交所
            return False
        
        return True
    
    def set_adapter(self, adapter):
        """
        设置适配器
        
        Args:
            adapter: 适配器实例
        """
        self.adapter = adapter
    
    def __repr__(self):
        adapter_info = f", adapter={type(self.adapter).__name__}" if self.adapter else ""
        return f"DataProvider(source={self.source}{adapter_info})"