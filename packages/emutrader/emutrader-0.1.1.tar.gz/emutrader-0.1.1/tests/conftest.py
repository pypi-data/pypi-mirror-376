"""
Pytest configuration and shared fixtures for EmuTrader tests.
"""

import pytest
import tempfile
import shutil
import os
from pathlib import Path
from typing import Generator
from datetime import datetime

# 添加项目根目录到Python路径
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from emutrader.core.models import AccountState, Position, Order, Transaction
from emutrader.handlers.stock import StockAccountHandler
from emutrader.adapters.mock_adapter import MockAdapter
from emutrader.storage.sqlite import SQLiteStorage
from emutrader.storage.cache import CacheManager, AccountCacheManager
from emutrader.utils.data import DataProvider


# 数据库和文件系统fixtures
@pytest.fixture(scope="session")
def temp_db_path() -> Generator[str, None, None]:
    """Create a temporary database file path for testing."""
    temp_dir = tempfile.mkdtemp()
    db_path = Path(temp_dir) / "test_accounts.db"
    yield str(db_path)
    shutil.rmtree(temp_dir)


@pytest.fixture
def clean_temp_db():
    """Create a clean temporary database for each test."""
    temp_dir = tempfile.mkdtemp()
    db_path = Path(temp_dir) / "test_clean.db"
    yield str(db_path)
    shutil.rmtree(temp_dir)


@pytest.fixture
def temp_data_dir():
    """Create a temporary data directory."""
    temp_dir = tempfile.mkdtemp()
    data_path = Path(temp_dir) / "data"
    data_path.mkdir(exist_ok=True)
    yield str(data_path)
    shutil.rmtree(temp_dir)


# 基础数据fixtures
@pytest.fixture
def sample_account_data():
    """Sample account data for testing."""
    return {
        "strategy_name": "test_strategy",
        "account_id": 1,
        "initial_cash": 100000.0,
        "account_type": "STOCK"
    }


@pytest.fixture
def sample_account_state():
    """Create a sample AccountState for testing."""
    return AccountState(
        total_value=100000.0,
        available_cash=80000.0,
        positions_value=20000.0,
        frozen_cash=0.0,
        transferable_cash=80000.0
    )


@pytest.fixture
def sample_position():
    """Create a sample Position for testing."""
    return Position(
        security="000001.XSHE",
        total_amount=1000,
        avg_cost=10.0,
        current_price=10.5,
        closeable_amount=1000,
        init_time=datetime.now(),
        transact_time=datetime.now()
    )


@pytest.fixture
def sample_order():
    """Create a sample Order for testing."""
    from emutrader.constants import OrderStatus
    return Order(
        order_id="TEST_ORDER_001",
        security="000001.XSHE",
        amount=1000,
        price=10.0,
        status=OrderStatus.NEW,
        created_time=datetime.now()
    )


@pytest.fixture
def sample_transaction():
    """Create a sample Transaction for testing."""
    return Transaction(
        order_id="TEST_ORDER_001",
        security="000001.XSHE",
        amount=1000,
        price=10.0,
        order_type="buy",
        commission=3.0,
        tax=0.0,
        filled_at=datetime.now()
    )


# 存储和缓存fixtures
@pytest.fixture
def sqlite_storage(clean_temp_db):
    """Create a SQLite storage instance for testing."""
    storage = SQLiteStorage(clean_temp_db)
    yield storage
    storage.close()


@pytest.fixture
def cache_manager():
    """Create a CacheManager instance for testing."""
    return CacheManager(max_size=100, ttl_seconds=300)


@pytest.fixture
def account_cache_manager():
    """Create an AccountCacheManager instance for testing."""
    return AccountCacheManager(max_size=100, ttl_seconds=300)


# 适配器fixtures
@pytest.fixture
def mock_adapter():
    """Create a MockAdapter instance for testing."""
    adapter = MockAdapter(
        strategy_name="test_strategy",
        account_id=1,
        enable_price_simulation=False,  # 关闭价格模拟便于测试
        volatility=0.01,
        slippage_rate=0.001
    )
    yield adapter
    adapter.close()


@pytest.fixture
def data_provider(mock_adapter):
    """Create a DataProvider with mock adapter."""
    return DataProvider(source="mock", adapter=mock_adapter)


# 处理器fixtures
@pytest.fixture
def stock_handler(clean_temp_db):
    """Create a StockAccountHandler for testing."""
    handler = StockAccountHandler(
        strategy_name="test_strategy",
        account_id=1,
        initial_cash=100000,
        db_path=clean_temp_db,
        enable_cache=True
    )
    yield handler
    # 清理资源


@pytest.fixture
def stock_handler_no_cache(clean_temp_db):
    """Create a StockAccountHandler without cache for testing."""
    handler = StockAccountHandler(
        strategy_name="test_strategy",
        account_id=1,
        initial_cash=100000,
        db_path=clean_temp_db,
        enable_cache=False
    )
    yield handler


# 多账户测试fixtures
@pytest.fixture
def multiple_accounts_data():
    """Generate data for multiple accounts testing."""
    return [
        {"strategy_name": "strategy_1", "account_id": 1, "initial_cash": 100000},
        {"strategy_name": "strategy_2", "account_id": 2, "initial_cash": 200000},
        {"strategy_name": "strategy_3", "account_id": 3, "initial_cash": 150000}
    ]


# 性能测试fixtures
@pytest.fixture
def performance_test_data():
    """Generate large dataset for performance testing."""
    securities = [f"{i:06d}.XSHE" for i in range(1, 101)]  # 100只股票
    orders_data = []
    
    for i, security in enumerate(securities[:10]):  # 前10只股票有订单
        orders_data.extend([
            {"security": security, "amount": 100 * (i + 1), "price": 10.0 + i},
            {"security": security, "amount": -50 * (i + 1), "price": 10.5 + i}
        ])
    
    return {
        "securities": securities,
        "orders": orders_data
    }


# 测试辅助函数
@pytest.fixture
def assert_account_state_valid():
    """Helper function to validate AccountState consistency."""
    def _validate(account_state: AccountState):
        assert account_state.total_value >= 0
        assert account_state.available_cash >= 0
        assert account_state.positions_value >= 0
        assert account_state.frozen_cash >= 0
        
        # 检查数据一致性
        calculated_total = (account_state.available_cash + 
                          account_state.positions_value + 
                          account_state.frozen_cash)
        assert abs(calculated_total - account_state.total_value) < 0.01
        
    return _validate


@pytest.fixture
def assert_position_valid():
    """Helper function to validate Position data."""
    def _validate(position: Position):
        assert position.total_amount >= 0
        assert position.avg_cost >= 0
        assert position.current_price >= 0
        assert position.closeable_amount <= position.total_amount
        assert position.closeable_amount >= 0
        assert position.value == position.total_amount * position.current_price
        
    return _validate


# 错误测试fixtures
@pytest.fixture
def invalid_order_data():
    """Generate invalid order data for error testing."""
    return [
        {"security": "", "amount": 100, "price": 10.0},  # 空证券代码
        {"security": "000001.XSHE", "amount": 0, "price": 10.0},  # 零数量
        {"security": "000001.XSHE", "amount": 50, "price": 10.0},  # 非100整数倍
        {"security": "000001.XSHE", "amount": 100, "price": -10.0},  # 负价格
        {"security": "INVALID", "amount": 100, "price": 10.0},  # 无效代码
    ]


# 并发测试fixtures
@pytest.fixture
def concurrent_test_config():
    """Configuration for concurrent testing."""
    return {
        "num_threads": 5,
        "operations_per_thread": 10,
        "test_duration": 30  # seconds
    }


# 清理fixtures
@pytest.fixture(autouse=True)
def cleanup_test_files():
    """Automatically cleanup test files after each test."""
    yield
    # 清理测试过程中可能创建的文件
    test_files = [
        "test_*.db",
        "test_*.log",
        "*.tmp"
    ]
    
    for pattern in test_files:
        for file in Path(".").glob(pattern):
            try:
                file.unlink()
            except:
                pass