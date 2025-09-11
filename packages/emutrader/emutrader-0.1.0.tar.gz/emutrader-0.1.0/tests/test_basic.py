"""
Basic tests to verify package import and version.
"""

import pytest
import emutrader


def test_package_import():
    """Test that the package can be imported."""
    assert emutrader.__version__
    assert emutrader.__author__


def test_version_format():
    """Test that version follows semantic versioning."""
    version = emutrader.__version__
    parts = version.split('.')
    assert len(parts) >= 2  # Major.Minor at minimum
    for part in parts:
        assert part.isdigit()


def test_public_api_available():
    """Test that main public API components are available."""
    # These should be importable once implemented
    expected_exports = [
        'EmuTrader',
        'Strategy', 
        'Account',
        'Order',
        'OrderType',
        'OrderStatus',
        'DataProvider',
        'TechnicalIndicators',
        'PerformanceAnalyzer'
    ]
    
    for export in expected_exports:
        assert export in emutrader.__all__