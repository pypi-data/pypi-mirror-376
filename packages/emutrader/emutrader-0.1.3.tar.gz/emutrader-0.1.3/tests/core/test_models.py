"""
Unit tests for core data models.
"""

import pytest
from datetime import datetime
from emutrader.core.models import AccountState, Position, Order, Transaction
from emutrader.constants import OrderStatus
from emutrader.exceptions import ValidationException


class TestAccountState:
    """Test AccountState model."""
    
    @pytest.mark.unit
    def test_create_valid_account_state(self):
        """Test creating a valid AccountState."""
        state = AccountState(
            total_value=100000.0,
            available_cash=80000.0,
            positions_value=20000.0,
            frozen_cash=0.0
        )
        
        assert state.total_value == 100000.0
        assert state.available_cash == 80000.0
        assert state.positions_value == 20000.0
        assert state.frozen_cash == 0.0
        assert state.transferable_cash == 80000.0  # 默认等于可用现金
        assert isinstance(state.timestamp, datetime)
        assert state.version == "1.0"
    
    @pytest.mark.unit
    def test_account_state_with_custom_transferable_cash(self):
        """Test AccountState with custom transferable cash."""
        state = AccountState(
            total_value=100000.0,
            available_cash=80000.0,
            positions_value=20000.0,
            frozen_cash=0.0,
            transferable_cash=75000.0
        )
        
        assert state.transferable_cash == 75000.0
    
    @pytest.mark.unit
    def test_account_state_data_consistency_validation(self):
        """Test AccountState data consistency validation."""
        # 正常情况应该通过
        AccountState(
            total_value=100000.0,
            available_cash=60000.0,
            positions_value=30000.0,
            frozen_cash=10000.0
        )
        
        # 数据不一致应该失败
        with pytest.raises(ValidationException, match="账户数据不一致"):
            AccountState(
                total_value=100000.0,
                available_cash=60000.0,
                positions_value=30000.0,
                frozen_cash=20000.0  # 60000 + 30000 + 20000 = 110000 != 100000
            )
    
    @pytest.mark.unit
    def test_account_state_negative_values_validation(self):
        """Test AccountState validation for negative values."""
        with pytest.raises(ValidationException, match="总资产不能为负数"):
            AccountState(-1000.0, 80000.0, 20000.0, 0.0)
        
        with pytest.raises(ValidationException, match="可用现金不能为负数"):
            AccountState(100000.0, -80000.0, 20000.0, 0.0)
        
        with pytest.raises(ValidationException, match="持仓市值不能为负数"):
            AccountState(100000.0, 80000.0, -20000.0, 0.0)
        
        with pytest.raises(ValidationException, match="冻结资金不能为负数"):
            AccountState(100000.0, 80000.0, 20000.0, -1000.0)
    
    @pytest.mark.unit
    def test_account_state_to_dict(self):
        """Test AccountState to_dict method."""
        state = AccountState(
            total_value=100000.0,
            available_cash=80000.0,
            positions_value=20000.0,
            frozen_cash=0.0
        )
        
        data = state.to_dict()
        
        assert data['total_value'] == 100000.0
        assert data['available_cash'] == 80000.0
        assert data['positions_value'] == 20000.0
        assert data['frozen_cash'] == 0.0
        assert data['transferable_cash'] == 80000.0
        assert 'timestamp' in data
        assert data['version'] == "1.0"
    
    @pytest.mark.unit
    def test_account_state_from_dict(self):
        """Test AccountState from_dict method."""
        data = {
            'total_value': 100000.0,
            'available_cash': 80000.0,
            'positions_value': 20000.0,
            'frozen_cash': 0.0,
            'transferable_cash': 75000.0,
            'timestamp': '2023-01-01T10:00:00',
            'version': '1.0'
        }
        
        state = AccountState.from_dict(data)
        
        assert state.total_value == 100000.0
        assert state.available_cash == 80000.0
        assert state.positions_value == 20000.0
        assert state.frozen_cash == 0.0
        assert state.transferable_cash == 75000.0
        assert state.version == "1.0"


class TestPosition:
    """Test Position model."""
    
    @pytest.mark.unit
    def test_create_valid_position(self):
        """Test creating a valid Position."""
        position = Position(
            security="000001.XSHE",
            total_amount=1000,
            avg_cost=10.0,
            current_price=10.5
        )
        
        assert position.security == "000001.XSHE"
        assert position.total_amount == 1000
        assert position.avg_cost == 10.0
        assert position.current_price == 10.5
        assert position.closeable_amount == 1000  # 默认等于总量
        assert isinstance(position.init_time, datetime)
        assert position.version == "1.0"
    
    @pytest.mark.unit
    def test_position_calculated_properties(self):
        """Test Position calculated properties."""
        position = Position(
            security="000001.XSHE",
            total_amount=1000,
            avg_cost=10.0,
            current_price=10.5
        )
        
        assert position.value == 10500.0  # 1000 * 10.5
        assert position.cost_value == 10000.0  # 1000 * 10.0
        assert position.pnl == 500.0  # 10500 - 10000
        assert position.pnl_ratio == 0.05  # 500 / 10000
    
    @pytest.mark.unit
    def test_position_zero_cost_pnl_ratio(self):
        """Test Position pnl_ratio when cost is zero."""
        position = Position(
            security="000001.XSHE",
            total_amount=1000,
            avg_cost=0.0,
            current_price=10.5
        )
        
        assert position.pnl_ratio == 0.0  # 避免除零错误
    
    @pytest.mark.unit
    def test_position_update_price(self):
        """Test Position update_price method."""
        position = Position(
            security="000001.XSHE",
            total_amount=1000,
            avg_cost=10.0,
            current_price=10.0
        )
        
        position.update_price(11.0)
        assert position.current_price == 11.0
        assert position.value == 11000.0
        assert position.pnl == 1000.0
    
    @pytest.mark.unit
    def test_position_validation(self):
        """Test Position validation."""
        # 空证券代码
        with pytest.raises(ValidationException, match="证券代码不能为空"):
            Position("", 1000, 10.0, 10.0)
        
        # 负数量
        with pytest.raises(ValidationException, match="持仓数量不能为负数"):
            Position("000001.XSHE", -1000, 10.0, 10.0)
        
        # 负成本
        with pytest.raises(ValidationException, match="平均成本不能为负数"):
            Position("000001.XSHE", 1000, -10.0, 10.0)
        
        # 负价格
        with pytest.raises(ValidationException, match="当前价格不能为负数"):
            Position("000001.XSHE", 1000, 10.0, -10.0)
        
        # 可平仓数量超过总量
        with pytest.raises(ValidationException, match="可平仓数量不能超过总持仓数量"):
            Position("000001.XSHE", 1000, 10.0, 10.0, closeable_amount=1500)
    
    @pytest.mark.unit
    def test_position_to_dict(self):
        """Test Position to_dict method."""
        position = Position(
            security="000001.XSHE",
            total_amount=1000,
            avg_cost=10.0,
            current_price=10.5
        )
        
        data = position.to_dict()
        
        assert data['security'] == "000001.XSHE"
        assert data['total_amount'] == 1000
        assert data['avg_cost'] == 10.0
        assert data['current_price'] == 10.5
        assert data['value'] == 10500.0
        assert data['pnl'] == 500.0
        assert data['pnl_ratio'] == 0.05
        assert 'init_time' in data
        assert data['version'] == "1.0"


class TestOrder:
    """Test Order model."""
    
    @pytest.mark.unit
    def test_create_valid_order(self):
        """Test creating a valid Order."""
        order = Order(
            order_id="TEST_001",
            security="000001.XSHE",
            amount=1000,
            price=10.0,
            status=OrderStatus.NEW
        )
        
        assert order.order_id == "TEST_001"
        assert order.security == "000001.XSHE"
        assert order.amount == 1000
        assert order.price == 10.0
        assert order.status == OrderStatus.NEW
        assert order.filled == 0
        assert order.commission == 0.0
        assert order.tax == 0.0
        assert isinstance(order.created_time, datetime)
        assert order.version == "1.0"
    
    @pytest.mark.unit
    def test_order_properties(self):
        """Test Order calculated properties."""
        # 买单
        buy_order = Order("TEST_001", "000001.XSHE", 1000, 10.0)
        assert buy_order.is_buy is True
        assert buy_order.is_sell is False
        assert buy_order.order_type == "buy"
        
        # 卖单
        sell_order = Order("TEST_002", "000001.XSHE", -1000, 10.0)
        assert sell_order.is_buy is False
        assert sell_order.is_sell is True
        assert sell_order.order_type == "sell"
    
    @pytest.mark.unit
    def test_order_unfilled_amount(self):
        """Test Order unfilled property."""
        order = Order("TEST_001", "000001.XSHE", 1000, 10.0, filled=300)
        assert order.unfilled == 700
    
    @pytest.mark.unit
    def test_order_is_finished(self):
        """Test Order is_finished property."""
        # 新订单
        new_order = Order("TEST_001", "000001.XSHE", 1000, 10.0, status=OrderStatus.NEW)
        assert new_order.is_finished is False
        
        # 已完成订单
        filled_order = Order("TEST_002", "000001.XSHE", 1000, 10.0, status=OrderStatus.FILLED)
        assert filled_order.is_finished is True
        
        # 已取消订单
        cancelled_order = Order("TEST_003", "000001.XSHE", 1000, 10.0, status=OrderStatus.CANCELLED)
        assert cancelled_order.is_finished is True
    
    @pytest.mark.unit
    def test_order_validation(self):
        """Test Order validation."""
        # 空订单ID
        with pytest.raises(ValidationException, match="订单ID不能为空"):
            Order("", "000001.XSHE", 1000, 10.0)
        
        # 空证券代码
        with pytest.raises(ValidationException, match="证券代码不能为空"):
            Order("TEST_001", "", 1000, 10.0)
        
        # 零数量
        with pytest.raises(ValidationException, match="订单数量不能为零"):
            Order("TEST_001", "000001.XSHE", 0, 10.0)
        
        # 负价格
        with pytest.raises(ValidationException, match="订单价格必须大于零"):
            Order("TEST_001", "000001.XSHE", 1000, -10.0)
        
        # 成交数量超过订单数量
        with pytest.raises(ValidationException, match="已成交数量不能超过订单数量"):
            Order("TEST_001", "000001.XSHE", 1000, 10.0, filled=1500)


class TestTransaction:
    """Test Transaction model."""
    
    @pytest.mark.unit
    def test_create_valid_transaction(self):
        """Test creating a valid Transaction."""
        transaction = Transaction(
            order_id="TEST_001",
            security="000001.XSHE",
            amount=1000,
            price=10.0,
            order_type="buy",
            commission=3.0,
            tax=1.0
        )
        
        assert transaction.order_id == "TEST_001"
        assert transaction.security == "000001.XSHE"
        assert transaction.amount == 1000
        assert transaction.price == 10.0
        assert transaction.order_type == "buy"
        assert transaction.commission == 3.0
        assert transaction.tax == 1.0
        assert transaction.status == "filled"
        assert isinstance(transaction.created_at, datetime)
        assert transaction.version == "1.0"
    
    @pytest.mark.unit
    def test_transaction_calculated_values(self):
        """Test Transaction calculated properties."""
        # 买入交易
        buy_transaction = Transaction(
            "TEST_001", "000001.XSHE", 1000, 10.0, "buy", 3.0, 1.0
        )
        
        assert buy_transaction.total_value == 10004.0  # 1000 * 10.0 + 3.0 + 1.0
        assert buy_transaction.net_value == -10004.0  # 买入为负值
        
        # 卖出交易
        sell_transaction = Transaction(
            "TEST_002", "000001.XSHE", -1000, 10.0, "sell", 3.0, 1.0
        )
        
        assert sell_transaction.total_value == 10004.0  # abs(-1000) * 10.0 + 3.0 + 1.0
        assert sell_transaction.net_value == 9996.0  # 10000 - 3.0 - 1.0
    
    @pytest.mark.unit
    def test_transaction_validation(self):
        """Test Transaction validation."""
        # 空订单ID
        with pytest.raises(ValidationException, match="订单ID不能为空"):
            Transaction("", "000001.XSHE", 1000, 10.0, "buy")
        
        # 空证券代码
        with pytest.raises(ValidationException, match="证券代码不能为空"):
            Transaction("TEST_001", "", 1000, 10.0, "buy")
        
        # 零数量
        with pytest.raises(ValidationException, match="交易数量不能为零"):
            Transaction("TEST_001", "000001.XSHE", 0, 10.0, "buy")
        
        # 负价格
        with pytest.raises(ValidationException, match="成交价格必须大于零"):
            Transaction("TEST_001", "000001.XSHE", 1000, -10.0, "buy")
        
        # 无效订单类型
        with pytest.raises(ValidationException, match="订单类型必须为 'buy' 或 'sell'"):
            Transaction("TEST_001", "000001.XSHE", 1000, 10.0, "invalid")
        
        # 负佣金
        with pytest.raises(ValidationException, match="佣金不能为负数"):
            Transaction("TEST_001", "000001.XSHE", 1000, 10.0, "buy", -3.0)
        
        # 负税费
        with pytest.raises(ValidationException, match="税费不能为负数"):
            Transaction("TEST_001", "000001.XSHE", 1000, 10.0, "buy", 3.0, -1.0)