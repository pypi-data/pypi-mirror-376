# -*- coding: utf-8 -*-
"""
JoinQuant平台适配器
"""

from .base import BaseAdapter
from ..core.models import AccountState


class JQAdapter(BaseAdapter):
    """JoinQuant平台适配器"""
    
    def get_account_info(self):
        """获取JQ账户信息"""
        # 模拟实现
        return {
            'total_value': 100000.0,
            'available_cash': 100000.0,
            'positions_value': 0.0
        }
    
    def get_positions(self):
        """获取JQ持仓"""
        return {}
    
    def send_order(self, security, amount, price, order_type="limit"):
        """发送JQ订单"""
        import uuid
        return f"JQ_{uuid.uuid4().hex[:8]}"
    
    def close(self):
        """关闭JQ适配器"""
        pass