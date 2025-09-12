"""
Basic tests to verify package import and version.
Testing new JQ-compatible API exports and functionality.
"""

import pytest
import emutrader


def test_package_import():
    """测试包可以正常导入"""
    assert emutrader.__version__
    assert emutrader.__author__


def test_version_format():
    """测试版本格式符合语义化版本规范"""
    version = emutrader.__version__
    parts = version.split('.')
    assert len(parts) >= 2  # Major.Minor at minimum
    for part in parts:
        assert part.isdigit()


def test_jq_compatible_api_available():
    """测试聚宽兼容API组件是否可用"""
    # 核心JQ兼容对象
    jq_core_exports = [
        'get_jq_account',      # 主要创建函数
        'StrategyContext',     # 策略上下文
        'Portfolio',           # 投资组合
        'Position',            # 持仓对象
        'SubPortfolio',        # 子账户
        'SubPortfolioConfig',  # 子账户配置
    ]
    
    for export in jq_core_exports:
        assert hasattr(emutrader, export), f"缺少JQ兼容导出: {export}"
        assert export in emutrader.__all__, f"{export} 未在 __all__ 中导出"


def test_jq_trading_functions_available():
    """测试聚宽兼容交易函数是否可用"""
    # JQ兼容交易函数
    trading_functions = [
        'order_shares',         # 按股数下单
        'order_value',          # 按金额下单
        'order_target_percent', # 调整到目标比例
    ]
    
    for func in trading_functions:
        assert hasattr(emutrader, func), f"缺少交易函数: {func}"
        assert callable(getattr(emutrader, func)), f"{func} 不是可调用函数"
        assert func in emutrader.__all__, f"{func} 未在 __all__ 中导出"


def test_jq_subportfolio_functions_available():
    """测试聚宽兼容子账户函数是否可用"""
    # 子账户管理函数
    subportfolio_functions = [
        'set_subportfolios',  # 设置子账户
        'transfer_cash',      # 资金转移
    ]
    
    for func in subportfolio_functions:
        assert hasattr(emutrader, func), f"缺少子账户函数: {func}"
        assert callable(getattr(emutrader, func)), f"{func} 不是可调用函数"
        assert func in emutrader.__all__, f"{func} 未在 __all__ 中导出"


def test_legacy_api_available():
    """测试传统API组件仍然可用（向后兼容）"""
    # 保留的传统API（向后兼容）
    legacy_exports = [
        'Account',             # 传统账户类
        'Order',               # 订单对象
        'get_account',         # 传统账户创建函数
    ]
    
    for export in legacy_exports:
        assert hasattr(emutrader, export), f"缺少向后兼容导出: {export}"
        assert export in emutrader.__all__, f"{export} 未在 __all__ 中导出"


def test_api_import_functionality():
    """测试导入的API组件可以正常使用"""
    # 测试核心组件可以正常导入和使用
    from emutrader import (
        get_jq_account, StrategyContext, Portfolio, Position,
        order_shares, order_value, order_target_percent,
        set_subportfolios, SubPortfolioConfig, transfer_cash
    )
    
    # 验证所有导入成功
    assert get_jq_account is not None
    assert StrategyContext is not None
    assert Portfolio is not None
    assert Position is not None
    
    # 验证函数可调用
    assert callable(get_jq_account)
    assert callable(order_shares)
    assert callable(order_value)
    assert callable(order_target_percent)
    assert callable(set_subportfolios)
    assert callable(transfer_cash)
    
    # 验证类可实例化（基本检查）
    assert isinstance(SubPortfolioConfig, type)


def test_package_structure_integrity():
    """测试包结构和完整性"""
    # 验证包结构
    assert hasattr(emutrader, '__version__')
    assert hasattr(emutrader, '__author__')
    assert hasattr(emutrader, '__all__')
    
    # 验证__all__是列表且包含预期数量的导出
    assert isinstance(emutrader.__all__, list)
    assert len(emutrader.__all__) >= 12  # 至少包含核心API导出
    
    # 验证所有__all__中的项目都可以从包中访问
    for export_name in emutrader.__all__:
        assert hasattr(emutrader, export_name), f"__all__中的 {export_name} 在包中不存在"


def test_jq_compatibility_quick_test():
    """聚寽API兼容性快速测试"""
    # 快速测试JQ API的基本功能
    try:
        # 测试创建JQ兼容账户
        context = emutrader.get_jq_account("quick_test", 100000, "STOCK")
        
        # 验证返回类型
        assert isinstance(context, emutrader.StrategyContext)
        
        # 验证基本属性存在
        assert hasattr(context, 'portfolio')
        assert hasattr(context, 'subportfolios')
        assert hasattr(context, 'current_dt')
        assert hasattr(context, 'run_params')
        
        # 验证Portfolio属性
        assert isinstance(context.portfolio, emutrader.Portfolio)
        assert context.portfolio.total_value == 100000.0
        
        print("✓ JQ API兼容性快速测试通过")
        
    except Exception as e:
        pytest.fail(f"JQ API兼容性快速测试失败: {e}")


def test_module_docstring():
    """测试模块具有适当的文档字符串"""
    # 验证模块有文档字符串
    assert emutrader.__doc__ is not None
    assert len(emutrader.__doc__.strip()) > 0
    
    # 验证文档字符串包含关键信息
    doc = emutrader.__doc__.lower()
    expected_keywords = ['joinquant', 'quantitative', 'trading', 'portfolio']
    
    for keyword in expected_keywords:
        assert keyword in doc, f"模块文档缺少关键词: {keyword}"