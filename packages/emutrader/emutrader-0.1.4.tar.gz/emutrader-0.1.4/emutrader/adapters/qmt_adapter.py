# -*- coding: utf-8 -*-
"""
QMT平台适配器
"""

from .base import BaseAdapter


class QMTAdapter(BaseAdapter):
    """QMT平台适配器"""
    
    def get_account_info(self):
        """获取QMT账户信息"""
        return {
            'total_value': 100000.0,
            'available_cash': 100000.0,
            'positions_value': 0.0
        }
    
    def get_positions(self):
        """获取QMT持仓"""
        return {}
    
    def send_order(self, security, amount, price, order_type="limit"):
        """发送QMT订单"""
        import uuid
        return f"QMT_{uuid.uuid4().hex[:8]}"
    
    def close(self):
        """关闭QMT适配器"""
        pass