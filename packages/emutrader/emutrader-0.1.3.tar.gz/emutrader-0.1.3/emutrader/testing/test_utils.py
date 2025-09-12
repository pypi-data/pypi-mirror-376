# -*- coding: utf-8 -*-
"""
测试工具模块

提供测试用的便利函数和工具。
"""

from typing import List, Dict, Any, Optional
from datetime import datetime

from ..core.context import AccountContext
from ..core.account import Account
from ..core.subportfolio import SubPortfolioConfig
from .test_mode import is_test_mode, get_test_config
from .mock_data import get_mock_provider


def create_test_account(strategy_name: str = "test_strategy", 
                       initial_cash: float = 100000,
                       account_type: str = "STOCK") -> Account:
    """
    创建测试用账户
    
    Args:
        strategy_name: 策略名称
        initial_cash: 初始资金
        account_type: 账户类型
        
    Returns:
        Account对象
        
    Example:
        >>> from emutrader.testing import enable_test_mode, TestMode, create_test_account
        >>> enable_test_mode(TestMode.UNIT_TEST)
        >>> account = create_test_account("test", 50000)
        >>> print(account.portfolio.total_value)
        50000.0
    """
    account = Account.create_simple(strategy_name, initial_cash, account_type)
    
    # 如果在测试模式下，应用测试配置
    if is_test_mode():
        # 设置快速时间模拟
        if get_test_config('fast_time_simulation', False):
            account.context._current_dt = datetime(2023, 1, 1, 9, 30, 0)  # 交易开始时间
        
        # 启用调试日志
        if get_test_config('debug_logging', False):
            print(f"[TEST] 创建测试账户: {strategy_name}, 资金: {initial_cash}, 类型: {account_type}")
    
    return account


def create_test_context(strategy_name: str = "test_strategy",
                       initial_cash: float = 100000,
                       account_type: str = "STOCK") -> AccountContext:
    """
    创建测试用策略上下文
    
    Args:
        strategy_name: 策略名称
        initial_cash: 初始资金
        account_type: 账户类型
        
    Returns:
        AccountContext对象
    """
    context = AccountContext(
        initial_cash=initial_cash,
        account_type=account_type,
        strategy_name=strategy_name
    )
    
    # 如果在测试模式下，应用测试配置
    if is_test_mode():
        if get_test_config('fast_time_simulation', False):
            context._current_dt = datetime(2023, 1, 1, 9, 30, 0)
            
        if get_test_config('debug_logging', False):
            print(f"[TEST] 创建测试上下文: {strategy_name}")
    
    return context


def create_test_subportfolios(total_cash: float = 300000) -> List[SubPortfolioConfig]:
    """
    创建测试用子账户配置
    
    Args:
        total_cash: 总资金
        
    Returns:
        子账户配置列表
    """
    configs = [
        SubPortfolioConfig(cash=total_cash * 0.6, type='stock'),      # 股票账户60%
        SubPortfolioConfig(cash=total_cash * 0.3, type='futures'),    # 期货账户30%
        SubPortfolioConfig(cash=total_cash * 0.1, type='index_futures'), # 金融期货10%
    ]
    
    if is_test_mode() and get_test_config('debug_logging', False):
        print(f"[TEST] 创建测试子账户配置: 总资金 {total_cash}, 分配: {[c.cash for c in configs]}")
    
    return configs


def setup_test_portfolio_with_positions(account: Account, 
                                       securities: List[str] = None,
                                       amounts: List[int] = None) -> Account:
    """
    为测试账户设置持仓
    
    Args:
        account: 账户对象
        securities: 证券代码列表
        amounts: 持仓数量列表
        
    Returns:
        设置了持仓的账户
    """
    if securities is None:
        securities = ['000001.SZ', '000002.SZ', '600519.SH']
    
    if amounts is None:
        amounts = [1000, 500, 100]
    
    mock_provider = get_mock_provider()
    
    # 添加持仓
    for security, amount in zip(securities, amounts):
        price = mock_provider.get_price(security)
        account.portfolio.add_position(security, amount, price)
        
        if is_test_mode() and get_test_config('debug_logging', False):
            print(f"[TEST] 添加测试持仓: {security} {amount}股 @{price:.2f}")
    
    return account


def simulate_trading_activity(account: Account, operations: List[Dict[str, Any]]):
    """
    模拟交易活动
    
    Args:
        account: 账户对象
        operations: 操作列表，每个操作包含 {'action': 'buy'|'sell', 'security': str, 'amount': int}
    """
    from ..api import set_current_context, order_shares
    
    # 设置当前上下文
    set_current_context(account.context)
    
    mock_provider = get_mock_provider()
    
    for op in operations:
        action = op['action']
        security = op['security']
        amount = op['amount']
        
        # 执行交易
        if action == 'buy':
            order = order_shares(security, amount)
        elif action == 'sell':
            order = order_shares(security, -amount)
        else:
            continue
            
        if is_test_mode() and get_test_config('debug_logging', False):
            price = mock_provider.get_price(security)
            print(f"[TEST] 模拟交易: {action} {security} {amount}股 @{price:.2f}")


def reset_test_environment():
    """
    重置测试环境
    
    清理所有测试状态，恢复初始状态。
    """
    from .mock_data import reset_mock_provider
    from ..api import _current_context
    
    # 重置Mock数据提供者
    reset_mock_provider()
    
    # 清理全局上下文（如果有的话）
    global _current_context
    _current_context = None
    
    if is_test_mode() and get_test_config('debug_logging', False):
        print("[TEST] 重置测试环境完成")


def assert_portfolio_state(account: Account,
                          expected_total_value: Optional[float] = None,
                          expected_cash: Optional[float] = None,
                          expected_positions_count: Optional[int] = None,
                          tolerance: float = 1.0):
    """
    断言投资组合状态 - 测试辅助函数
    
    Args:
        account: 账户对象
        expected_total_value: 期望总资产
        expected_cash: 期望现金
        expected_positions_count: 期望持仓数量
        tolerance: 容错范围
    """
    portfolio = account.portfolio
    
    if expected_total_value is not None:
        actual = portfolio.total_value
        assert abs(actual - expected_total_value) <= tolerance, \
            f"总资产不匹配: 期望 {expected_total_value}, 实际 {actual}"
    
    if expected_cash is not None:
        actual = portfolio.available_cash
        assert abs(actual - expected_cash) <= tolerance, \
            f"可用现金不匹配: 期望 {expected_cash}, 实际 {actual}"
    
    if expected_positions_count is not None:
        actual = len([p for p in portfolio.positions.values() if p.total_amount > 0])
        assert actual == expected_positions_count, \
            f"持仓数量不匹配: 期望 {expected_positions_count}, 实际 {actual}"


def create_performance_test_data(securities_count: int = 100, 
                                operations_count: int = 1000) -> Dict[str, Any]:
    """
    创建性能测试数据
    
    Args:
        securities_count: 证券数量
        operations_count: 操作数量
        
    Returns:
        性能测试数据集
    """
    mock_provider = get_mock_provider()
    
    # 生成测试证券
    securities = mock_provider.generate_test_securities(securities_count)
    
    # 生成测试操作
    import random
    operations = []
    for i in range(operations_count):
        op = {
            'action': random.choice(['buy', 'sell']),
            'security': random.choice(securities),
            'amount': random.choice([100, 200, 500, 1000]),
            'timestamp': datetime.now()
        }
        operations.append(op)
    
    return {
        'securities': securities,
        'operations': operations,
        'total_securities': securities_count,
        'total_operations': operations_count
    }


def measure_execution_time(func, *args, **kwargs) -> Dict[str, Any]:
    """
    测量执行时间
    
    Args:
        func: 要测量的函数
        *args: 函数参数
        **kwargs: 函数关键字参数
        
    Returns:
        执行结果和时间信息
    """
    import time
    
    start_time = time.time()
    start_perf = time.perf_counter()
    
    try:
        result = func(*args, **kwargs)
        success = True
        error = None
    except Exception as e:
        result = None
        success = False
        error = str(e)
    
    end_time = time.time()
    end_perf = time.perf_counter()
    
    return {
        'result': result,
        'success': success,
        'error': error,
        'execution_time_seconds': end_time - start_time,
        'execution_time_perf': end_perf - start_perf,
        'start_time': start_time,
        'end_time': end_time
    }


# 便利的测试装饰器
def test_with_mock_data(securities_count: int = 5):
    """
    使用Mock数据的测试装饰器
    
    Args:
        securities_count: Mock证券数量
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            if not is_test_mode():
                raise RuntimeError("请先启用测试模式")
            
            # 创建Mock数据
            mock_provider = get_mock_provider()
            securities = mock_provider.generate_test_securities(securities_count)
            
            # 将Mock数据作为参数传递
            kwargs['mock_securities'] = securities
            kwargs['mock_provider'] = mock_provider
            
            return func(*args, **kwargs)
        
        return wrapper
    return decorator