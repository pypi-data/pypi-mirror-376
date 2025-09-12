"""
Pytest configuration and shared fixtures for EmuTrader tests.
简化版配置，专注于新架构的核心测试。
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from typing import Generator
from datetime import datetime

# 添加项目根目录到Python路径
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from emutrader import get_jq_account, EmuTrader, Portfolio, Position, SubPortfolio
from emutrader.core.models import AccountState, Order, Transaction


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


# 基础数据fixtures
@pytest.fixture
def sample_account_data():
    """Sample account data for testing."""
    return {
        "strategy_name": "test_strategy",
        "initial_cash": 100000.0,
        "account_type": "STOCK"
    }


@pytest.fixture
def sample_emutrader():
    """Create a sample EmuTrader for testing."""
    return get_jq_account("test_strategy", 100000, "STOCK")


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
    from emutrader.core.position import Position
    return Position(
        security="000001.SZ",
        total_amount=1000,
        avg_cost=10.0,
        last_price=10.5
    )


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