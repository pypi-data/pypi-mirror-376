# -*- coding: utf-8 -*-
"""
信用账户处理器
"""

from .base import BaseAccountHandler
from ..core.models import AccountState
from ..constants import AccountTypes


class CreditAccountHandler(BaseAccountHandler):
    """信用账户处理器"""
    
    def _get_account_type(self):
        return AccountTypes.CREDIT
    
    def get_account_state(self):
        """获取信用账户状态"""
        # 模拟实现
        return AccountState(
            total_value=150000.0,
            available_cash=150000.0,
            positions_value=0.0
        )
    
    def send_order(self, security, amount, price, order_type="limit"):
        """发送信用订单"""
        # 模拟实现
        import uuid
        order_id = f"CREDIT_{uuid.uuid4().hex[:8]}"
        print(f"信用订单: {security} {amount}@{price}")
        return order_id