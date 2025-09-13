"""
Unit tests for SQLite storage implementation.
"""

import pytest
from datetime import datetime
from emutrader.storage.sqlite import SQLiteStorage
from emutrader.core.models import AccountState, Position, Transaction, Order
from emutrader.constants import AccountTypes, OrderStatus
from emutrader.exceptions import StorageException


class TestSQLiteStorage:
    """Test SQLiteStorage implementation."""
    
    @pytest.mark.storage
    def test_storage_initialization(self, clean_temp_db):
        """Test SQLiteStorage initialization."""
        storage = SQLiteStorage(clean_temp_db)
        assert storage.db_path.exists()
        assert storage._connection is not None
        storage.close()
    
    @pytest.mark.storage
    def test_save_and_load_account_state(self, sqlite_storage, sample_account_state):
        """Test saving and loading account state."""
        strategy_name = "test_strategy"
        account_id = 1
        
        # 保存账户状态
        sqlite_storage.save_account_state(
            strategy_name, account_id, sample_account_state, AccountTypes.STOCK
        )
        
        # 加载账户状态
        loaded_state = sqlite_storage.load_account_state(strategy_name, account_id)
        
        assert loaded_state is not None
        assert loaded_state.total_value == sample_account_state.total_value
        assert loaded_state.available_cash == sample_account_state.available_cash
        assert loaded_state.positions_value == sample_account_state.positions_value
        assert loaded_state.frozen_cash == sample_account_state.frozen_cash
        assert loaded_state.transferable_cash == sample_account_state.transferable_cash
    
    @pytest.mark.storage
    def test_load_nonexistent_account_state(self, sqlite_storage):
        """Test loading non-existent account state."""
        loaded_state = sqlite_storage.load_account_state("nonexistent", 999)
        assert loaded_state is None
    
    @pytest.mark.storage
    def test_save_and_load_position(self, sqlite_storage, sample_position):
        """Test saving and loading single position."""
        strategy_name = "test_strategy"
        account_id = 1
        security = sample_position.security
        
        # 保存持仓
        sqlite_storage.save_position(strategy_name, account_id, security, sample_position)
        
        # 加载持仓
        positions = sqlite_storage.load_positions(strategy_name, account_id)
        
        assert security in positions
        loaded_position = positions[security]
        assert loaded_position.security == sample_position.security
        assert loaded_position.total_amount == sample_position.total_amount
        assert loaded_position.avg_cost == sample_position.avg_cost
        assert loaded_position.closeable_amount == sample_position.closeable_amount
    
    @pytest.mark.storage
    def test_save_and_load_multiple_positions(self, sqlite_storage):
        """Test saving and loading multiple positions."""
        strategy_name = "test_strategy"
        account_id = 1
        
        # 创建多个持仓
        positions = {
            "000001.XSHE": Position("000001.XSHE", 1000, 10.0, 10.5),
            "000002.XSHE": Position("000002.XSHE", 500, 15.0, 15.2),
            "600000.XSHG": Position("600000.XSHG", 2000, 8.0, 8.1)
        }
        
        # 批量保存持仓
        sqlite_storage.save_positions(strategy_name, account_id, positions)
        
        # 加载持仓
        loaded_positions = sqlite_storage.load_positions(strategy_name, account_id)
        
        assert len(loaded_positions) == 3
        for security, position in positions.items():
            assert security in loaded_positions
            loaded_position = loaded_positions[security]
            assert loaded_position.total_amount == position.total_amount
            assert loaded_position.avg_cost == position.avg_cost
    
    @pytest.mark.storage
    def test_save_positions_clears_existing(self, sqlite_storage):
        """Test that save_positions clears existing positions."""
        strategy_name = "test_strategy"
        account_id = 1
        
        # 保存初始持仓
        initial_positions = {
            "000001.XSHE": Position("000001.XSHE", 1000, 10.0, 10.5),
            "000002.XSHE": Position("000002.XSHE", 500, 15.0, 15.2)
        }
        sqlite_storage.save_positions(strategy_name, account_id, initial_positions)
        
        # 保存新持仓（应该覆盖旧的）
        new_positions = {
            "600000.XSHG": Position("600000.XSHG", 2000, 8.0, 8.1)
        }
        sqlite_storage.save_positions(strategy_name, account_id, new_positions)
        
        # 验证只有新持仓
        loaded_positions = sqlite_storage.load_positions(strategy_name, account_id)
        assert len(loaded_positions) == 1
        assert "600000.XSHG" in loaded_positions
        assert "000001.XSHE" not in loaded_positions
        assert "000002.XSHE" not in loaded_positions
    
    @pytest.mark.storage
    def test_save_zero_amount_positions_are_excluded(self, sqlite_storage):
        """Test that positions with zero amount are not saved."""
        strategy_name = "test_strategy"
        account_id = 1
        
        positions = {
            "000001.XSHE": Position("000001.XSHE", 1000, 10.0, 10.5),
            "000002.XSHE": Position("000002.XSHE", 0, 15.0, 15.2),  # 零持仓
            "600000.XSHG": Position("600000.XSHG", 500, 8.0, 8.1)
        }
        
        sqlite_storage.save_positions(strategy_name, account_id, positions)
        loaded_positions = sqlite_storage.load_positions(strategy_name, account_id)
        
        # 只应该有非零持仓
        assert len(loaded_positions) == 2
        assert "000001.XSHE" in loaded_positions
        assert "600000.XSHG" in loaded_positions
        assert "000002.XSHE" not in loaded_positions
    
    @pytest.mark.storage
    def test_save_and_load_transaction(self, sqlite_storage, sample_transaction):
        """Test saving and loading transaction."""
        strategy_name = "test_strategy"
        account_id = 1
        
        # 保存交易记录
        sqlite_storage.save_transaction(strategy_name, account_id, sample_transaction)
        
        # 加载交易记录
        transactions = sqlite_storage.load_transactions(strategy_name, account_id, limit=10)
        
        assert len(transactions) == 1
        tx_row = transactions[0]
        assert tx_row[1] == strategy_name  # strategy_name column
        assert tx_row[2] == account_id     # account_id column
        assert tx_row[3] == sample_transaction.security  # security column
        assert tx_row[4] == sample_transaction.amount    # amount column
        assert tx_row[5] == sample_transaction.price     # price column
    
    @pytest.mark.storage
    def test_save_and_load_order(self, sqlite_storage, sample_order):
        """Test saving and loading order."""
        strategy_name = "test_strategy"
        account_id = 1
        
        # 保存订单
        sqlite_storage.save_order(strategy_name, account_id, sample_order)
        
        # 加载订单
        orders = sqlite_storage.load_orders(strategy_name, account_id)
        
        assert len(orders) == 1
        order_row = orders[0]
        assert order_row[1] == strategy_name  # strategy_name column
        assert order_row[2] == account_id     # account_id column
        assert order_row[3] == sample_order.security  # security column
        assert order_row[4] == sample_order.amount    # amount column
        assert order_row[5] == sample_order.price     # price column
    
    @pytest.mark.storage
    def test_load_orders_with_status_filter(self, sqlite_storage):
        """Test loading orders with status filter."""
        strategy_name = "test_strategy"
        account_id = 1
        
        # 创建不同状态的订单
        new_order = Order("ORDER_001", "000001.XSHE", 1000, 10.0, status=OrderStatus.NEW)
        filled_order = Order("ORDER_002", "000001.XSHE", 500, 10.5, status=OrderStatus.FILLED)
        
        sqlite_storage.save_order(strategy_name, account_id, new_order)
        sqlite_storage.save_order(strategy_name, account_id, filled_order)
        
        # 加载所有订单
        all_orders = sqlite_storage.load_orders(strategy_name, account_id)
        assert len(all_orders) == 2
        
        # 只加载已成交订单
        filled_orders = sqlite_storage.load_orders(strategy_name, account_id, status=OrderStatus.FILLED)
        assert len(filled_orders) == 1
        assert filled_orders[0][8] == OrderStatus.FILLED  # status column
    
    @pytest.mark.storage
    def test_multiple_accounts_isolation(self, sqlite_storage):
        """Test data isolation between different accounts."""
        # 账户1数据
        account1_state = AccountState(100000.0, 80000.0, 20000.0)
        account1_position = Position("000001.XSHE", 1000, 10.0, 10.5)
        
        # 账户2数据
        account2_state = AccountState(200000.0, 150000.0, 50000.0)
        account2_position = Position("000002.XSHE", 2000, 15.0, 15.5)
        
        # 保存账户1数据
        sqlite_storage.save_account_state("strategy1", 1, account1_state, AccountTypes.STOCK)
        sqlite_storage.save_position("strategy1", 1, "000001.XSHE", account1_position)
        
        # 保存账户2数据
        sqlite_storage.save_account_state("strategy2", 2, account2_state, AccountTypes.STOCK)
        sqlite_storage.save_position("strategy2", 2, "000002.XSHE", account2_position)
        
        # 验证数据隔离
        loaded_state1 = sqlite_storage.load_account_state("strategy1", 1)
        loaded_state2 = sqlite_storage.load_account_state("strategy2", 2)
        
        assert loaded_state1.total_value == 100000.0
        assert loaded_state2.total_value == 200000.0
        
        positions1 = sqlite_storage.load_positions("strategy1", 1)
        positions2 = sqlite_storage.load_positions("strategy2", 2)
        
        assert "000001.XSHE" in positions1
        assert "000001.XSHE" not in positions2
        assert "000002.XSHE" in positions2
        assert "000002.XSHE" not in positions1
    
    @pytest.mark.storage
    def test_database_connection_error_handling(self):
        """Test error handling for database connection issues."""
        # 使用无效路径应该抛出异常
        with pytest.raises(StorageException, match="初始化SQLite失败"):
            SQLiteStorage("/invalid/path/test.db")
    
    @pytest.mark.storage
    def test_transaction_limit(self, sqlite_storage, sample_account_data):
        """Test transaction loading with limit."""
        strategy_name = sample_account_data["strategy_name"]
        account_id = sample_account_data["account_id"]
        
        # 创建多个交易记录
        for i in range(5):
            transaction = Transaction(
                f"ORDER_{i:03d}",
                f"00000{i+1}.XSHE",
                100,
                10.0 + i,
                "buy"
            )
            sqlite_storage.save_transaction(strategy_name, account_id, transaction)
        
        # 测试限制数量
        limited_transactions = sqlite_storage.load_transactions(strategy_name, account_id, limit=3)
        assert len(limited_transactions) == 3
        
        # 测试默认限制
        all_transactions = sqlite_storage.load_transactions(strategy_name, account_id)
        assert len(all_transactions) == 5
    
    @pytest.mark.storage
    def test_storage_close(self, clean_temp_db):
        """Test storage connection closing."""
        storage = SQLiteStorage(clean_temp_db)
        assert storage._connection is not None
        
        storage.close()
        assert storage._connection is None
        
        # 再次关闭应该安全
        storage.close()


class TestSQLiteStorageErrorHandling:
    """Test error handling in SQLite storage."""
    
    @pytest.mark.storage
    def test_invalid_account_state_save(self, sqlite_storage):
        """Test error handling for invalid account state."""
        # 模拟数据库错误情况下的异常处理
        with pytest.raises(StorageException):
            sqlite_storage.save_account_state(None, None, None, None)
    
    @pytest.mark.storage
    def test_invalid_position_save(self, sqlite_storage):
        """Test error handling for invalid position."""
        with pytest.raises(StorageException):
            sqlite_storage.save_position(None, None, None, None)
    
    @pytest.mark.storage 
    def test_invalid_transaction_save(self, sqlite_storage):
        """Test error handling for invalid transaction."""
        with pytest.raises(StorageException):
            sqlite_storage.save_transaction(None, None, None)
    
    @pytest.mark.storage
    def test_invalid_order_save(self, sqlite_storage):
        """Test error handling for invalid order."""
        with pytest.raises(StorageException):
            sqlite_storage.save_order(None, None, None)