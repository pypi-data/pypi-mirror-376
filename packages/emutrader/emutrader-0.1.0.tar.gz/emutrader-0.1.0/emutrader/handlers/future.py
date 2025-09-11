# -*- coding: utf-8 -*-
"""
期货账户处理器
"""

from .base import BaseAccountHandler
from ..core.models import AccountState
from ..constants import AccountTypes


class FutureAccountHandler(BaseAccountHandler):
    """期货账户处理器"""
    
    def _get_account_type(self):
        return AccountTypes.FUTURE
    
    def get_account_state(self):
        """获取期货账户状态"""
        # 模拟实现
        return AccountState(
            total_value=200000.0,
            available_cash=200000.0,
            positions_value=0.0
        )
    
    def send_order(self, security, amount, price, order_type="limit"):
        """发送期货订单"""
        # 模拟实现
        import uuid
        order_id = f"FUTURE_{uuid.uuid4().hex[:8]}"
        print(f"期货订单: {security} {amount}@{price}")
        return order_id