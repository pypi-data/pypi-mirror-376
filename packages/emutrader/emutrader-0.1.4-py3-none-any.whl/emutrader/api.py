# -*- coding: utf-8 -*-
"""
JoinQuant 兼容API

提供与JoinQuant平台100%兼容的API接口。
"""

from typing import Optional, Dict, Any, List, Union
from .core.account import Account
from .core.context import AccountContext
from .core.trader import EmuTrader
from .core.order import Order
from .core.models import OrderCost
from .core.subportfolio import SubPortfolioConfig
from .exceptions import (
    ValidationException, ContextException, TradingException,
    InsufficientFundsException, InsufficientPositionException,
    InvalidSecurityException, SubPortfolioException
)


# 全局变量存储当前EmuTrader实例（为QSM提供账户管理）
_current_emutrader: Optional[EmuTrader] = None
# 全局严格模式标志（用于测试）
_strict_mode: bool = False


def set_current_emutrader(emutrader: EmuTrader):
    """设置当前EmuTrader实例（内部使用）"""
    global _current_emutrader
    _current_emutrader = emutrader


def get_current_emutrader() -> Optional[EmuTrader]:
    """获取当前EmuTrader实例（内部使用）"""
    return _current_emutrader


# 向后兼容函数
def set_current_context(context):
    """设置当前策略上下文（向后兼容）"""
    # 如果传入的是EmuTrader，直接设置
    if isinstance(context, EmuTrader):
        set_current_emutrader(context)
    else:
        # 如果是其他类型，暂时保留兼容性
        global _current_emutrader
        _current_emutrader = context


def set_sub_context(context):
    """设置子账户上下文（向后兼容）"""
    # 这个函数在重构后主要用于向后兼容
    # 实际上sub context现在通过subportfolios管理
    set_current_context(context)


def get_current_context():
    """获取当前策略上下文（向后兼容）"""
    return _current_emutrader


def get_current_emutrader():
    """获取当前策略上下文（向后兼容）"""
    return _current_emutrader


def set_strict_mode(enabled: bool = True):
    """设置严格模式（用于测试）"""
    global _strict_mode
    _strict_mode = enabled


def is_strict_mode() -> bool:
    """检查是否为严格模式"""
    return _strict_mode


def get_jq_account(strategy_name: str, initial_cash: float = 100000, 
                   account_type: str = "stock"):
    """
    获取JoinQuant兼容的策略上下文对象
    
    现在返回EmuTrader实例，它提供portfolio和subportfolios属性，
    100%兼容JoinQuant的context对象使用方式。
    
    Args:
        strategy_name (str): 策略名称（只能使用英文+数字+下划线）
        initial_cash (float): 初始资金，默认10万
        account_type (str): 账户类型，支持 stock/futures（推荐小写）
        
    Returns:
        EmuTrader: JoinQuant兼容的账户管理对象
        
    Example:
        >>> context = get_jq_account("my_strategy_001", 100000, "stock")
        >>> print(context.portfolio.total_value)
        100000.0
        >>> print(context.portfolio.available_cash)
        100000.0
        >>> # 访问子账户
        >>> print(len(context.subportfolios))
        0
        
    QSM使用方式:
        >>> emutrader = get_jq_account("my_strategy", 100000, "stock")
        >>> emutrader.update_market_price('000001.SZ', 12.5)
        >>> success = emutrader.execute_trade('000001.SZ', 1000, 12.5)
        >>> emutrader.save_to_db('account.db')
    """
    # 导入账户类型常量
    from .constants import AccountTypes
    
    # 参数验证
    if not strategy_name:
        raise ValidationException("策略名称不能为空")
    
    if initial_cash <= 0:
        raise ValidationException("初始资金必须大于0")
    
    # 支持的账户类型（包括新旧格式）
    supported_types = AccountTypes.IMPLEMENTED + list(AccountTypes.LEGACY_MAPPING.keys())
    
    # 账户类型标准化（支持向后兼容）
    normalized_type = AccountTypes.LEGACY_MAPPING.get(account_type, account_type)
    
    if normalized_type not in AccountTypes.IMPLEMENTED:
        raise ValidationException(
            f"不支持的账户类型: {account_type}",
            field_name="account_type", 
            field_value=account_type,
            suggestions=[f"支持的类型: {supported_types}"]
        )
    
    # 使用标准化的账户类型
    account_type = normalized_type
    
    # 创建EmuTrader实例
    emutrader = EmuTrader(
        initial_capital=initial_cash,
        account_type=account_type,
        strategy_name=strategy_name
    )
    
    # 设置为当前实例
    set_current_emutrader(emutrader)
    
    return emutrader


def get_account(strategy_name: str, initial_cash: float = 100000, 
               account_type: str = "stock") -> Account:
    """
    获取Account账户对象（向后兼容）
    
    如果需要直接访问Account对象而不是Context，可以使用此函数。
    
    Args:
        strategy_name (str): 策略名称（只能使用英文+数字+下划线）
        initial_cash (float): 初始资金，默认10万
        account_type (str): 账户类型，支持 stock/futures（推荐小写）
        
    Returns:
        Account: 账户对象（内置Context和Portfolio）
        
    Example:
        >>> account = get_account("my_strategy_001", 100000, "stock")
        >>> print(account.portfolio.total_value)
        100000.0
        >>> print(len(account.subportfolios))
        0
    """
    # 导入账户类型常量
    from .constants import AccountTypes
    
    # 参数验证
    if not strategy_name:
        raise ValidationException("策略名称不能为空")
    
    if initial_cash <= 0:
        raise ValidationException("初始资金必须大于0")
    
    # 支持的账户类型（包括新旧格式）
    supported_types = AccountTypes.IMPLEMENTED + list(AccountTypes.LEGACY_MAPPING.keys())
    
    # 账户类型标准化（支持向后兼容）
    normalized_type = AccountTypes.LEGACY_MAPPING.get(account_type, account_type)
    
    if normalized_type not in AccountTypes.IMPLEMENTED:
        raise ValidationException(
            f"不支持的账户类型: {account_type}",
            field_name="account_type", 
            field_value=account_type,
            suggestions=[f"支持的类型: {supported_types}"]
        )
    
    # 使用标准化的账户类型
    account_type = normalized_type
    
    # 创建账户实例
    account = Account(
        strategy_name=strategy_name,
        initial_cash=initial_cash,
        account_type=account_type
    )
    
    return account


# ===============================
# 交易API实现
# ===============================

def set_order_cost(cost: OrderCost, type: str, ref: Optional[str] = None):
    """
    设置交易成本 - JoinQuant兼容函数
    
    指定每笔交易要收取的手续费, 系统会根据用户指定的费率计算每笔交易的手续费
    
    Args:
        cost: OrderCost 对象，包含交易成本配置
        type: 交易品种类型，支持：
            - 'stock': 股票
            - 'fund': 场内基金  
            - 'mmf': 场内交易的货币基金
            - 'fja': 分级A基金
            - 'fjb': 分级B基金
            - 'fjm': 分级母基金
            - 'index_futures': 金融期货
            - 'futures': 期货
            - 'bond_fund': 债券基金
            - 'stock_fund': 股票基金
            - 'QDII_fund': QDII基金
            - 'mixture_fund': 混合基金
        ref: 参考代码，支持股票代码/基金代码/期货合约代码，以及期货的品种
            如 '000001.XSHE'/'510180.XSHG'/'IF1709'/'IF'/'000300.OF'
            
    注意：针对特定的交易品种类别设置手续费时，必须将ref设为None；
         若针对特定的交易品种或者标的，需要将type设置为对应的交易品种类别，
         将ref设置为对应的交易品种或者标的
    
    Raises:
        ValidationException: 当参数无效时
        ContextException: 当策略上下文未设置时
    """
    if _current_emutrader is None:
        raise ContextException("策略上下文未设置", suggestions=[
            "使用 get_jq_account() 创建策略上下文",
            "调用 set_current_emutrader() 设置上下文"
        ])
    
    # 验证参数
    if not isinstance(cost, OrderCost):
        raise ValidationException("cost参数必须是OrderCost对象")
    
    # 验证type参数
    valid_types = {
        'stock', 'fund', 'mmf', 'fja', 'fjb', 'fjm', 
        'index_futures', 'futures', 'bond_fund', 'stock_fund', 
        'QDII_fund', 'mixture_fund'
    }
    
    if type not in valid_types:
        raise ValidationException(f"无效的交易品种类型: {type}，支持的类型: {valid_types}")
    
    # 验证ref参数逻辑
    if ref is not None and not isinstance(ref, str):
        raise ValidationException("ref参数必须是字符串或None")
    
    # 调用EmuTrader的交易成本设置方法
    _current_emutrader.set_order_cost(cost, type, ref)


def _get_current_price(security: str) -> float:
    """获取当前价格（内部使用）"""
    # 检查是否启用了测试模式
    try:
        from .testing.test_mode import is_test_mode, get_test_config
        from .testing.mock_data import get_mock_price
        
        if is_test_mode() and get_test_config('mock_price_enabled', False):
            return get_mock_price(security)
    except ImportError:
        pass  # 测试模块未安装，使用默认价格
    
    # 模拟价格，实际应用中需要连接数据源
    return 10.0


def _validate_security(security: str) -> bool:
    """验证证券代码（内部使用）"""
    if not security or not isinstance(security, str):
        return False
    
    # 简单的证券代码格式检查
    if '.' not in security:
        return False
    
    return True


def _validate_and_raise_security_error(security: str):
    """验证证券代码并抛出异常"""
    if not _validate_security(security):
        raise InvalidSecurityException(security)


def _execute_order_on_portfolio(portfolio, security: str, amount: int, price: float) -> Optional[Order]:
    """在指定的组合上执行订单（内部使用）"""
    if amount == 0:
        return None
    
    # 创建订单对象
    order_obj = Order.create_market_order(security, amount, price)
    
    if amount > 0:  # 买入
        total_cost = amount * price
        if portfolio.available_cash < total_cost:
            raise InsufficientFundsException(
                total_cost, portfolio.available_cash, security
            )
        
        # 执行买入
        portfolio.reduce_cash(total_cost)
        portfolio.add_position(security, amount, price)
        order_obj.status = "filled"
        order_obj.filled = amount
        
    else:  # 卖出
        sell_amount = abs(amount)
        position = portfolio.get_position(security)
        available = position.closeable_amount if position else 0
        
        if available < sell_amount:
            raise InsufficientPositionException(
                sell_amount, available, security
            )
        
        # 执行卖出
        portfolio.reduce_position(security, sell_amount)
        total_value = sell_amount * price
        portfolio.add_cash(total_value)
        order_obj.status = "filled"
        order_obj.filled = amount  # 负数表示卖出
        
    return order_obj


def order_with_price(security: str, amount: int, price: float, side: str = 'long') -> Optional[Order]:
    """按指定价格下单（内部使用）"""
    if _current_emutrader is None:
        raise ContextException("策略上下文未设置", suggestions=[
            "使用 get_jq_account() 创建策略上下文",
            "调用 set_current_emutrader() 设置上下文"
        ])
    
    # 验证证券代码
    _validate_and_raise_security_error(security)
    
    if amount == 0:
        return None
    
    # 验证股数必须是100的整数倍（A股规则）
    if amount % 100 != 0:
        return None  # 非100整数倍返回None
    
    if side != 'long':
        raise TradingException("暂仅支持多头持仓", security=security, 
                             suggestions=["当前版本只支持做多交易"])
    
    # 使用EmuTrader的execute_trade方法
    success = _current_emutrader.execute_trade(security, amount, price)
    
    if success:
        # 创建订单对象（向后兼容）
        order_obj = Order.create_market_order(security, amount, price)
        order_obj.status = "filled"
        order_obj.filled = amount
        return order_obj
    else:
        # 根据错误原因抛出相应异常
        portfolio = _current_emutrader.get_portfolio()
        if amount > 0:  # 买入失败
            total_cost = amount * price
            if portfolio.available_cash < total_cost:
                raise InsufficientFundsException(total_cost, portfolio.available_cash, security)
        else:  # 卖出失败
            sell_amount = abs(amount)
            position = portfolio.get_position(security)
            available = position.closeable_amount if position else 0
            if available < sell_amount:
                raise InsufficientPositionException(sell_amount, available, security)
        
        return None


def order(security: str, amount: int, style=None, side: str = 'long') -> Optional[Order]:
    """
    按股数下单 - JoinQuant兼容全局函数
    
    Args:
        security: 证券代码
        amount: 股数 (正数买入，负数卖出)
        style: 下单方式 (None=市价单，暂不支持其他类型)
        side: 持仓方向 ('long', 'short')，暂仅支持long
        
    Returns:
        Order对象，失败时返回None
        
    Raises:
        ContextException: 当策略上下文未设置时
        InvalidSecurityException: 当证券代码无效时
        TradingException: 当交易参数无效时
        SubPortfolioException: 当子账户不存在时
    """
    if _current_emutrader is None:
        raise ContextException("策略上下文未设置", suggestions=[
            "使用 get_jq_account() 创建策略上下文",
            "调用 set_current_emutrader() 设置上下文"
        ])
    
    # 验证证券代码
    _validate_and_raise_security_error(security)
    
    if amount == 0:
        return None
    
    # 验证股数必须是100的整数倍（A股规则）
    if amount % 100 != 0:
        return None  # 非100整数倍返回None
    
    if side != 'long':
        raise TradingException("暂仅支持多头持仓", security=security, 
                             suggestions=["当前版本只支持做多交易"])
    
    if style is not None:
        raise TradingException("暂仅支持市价单", security=security,
                             suggestions=["请使用 style=None 进行市价交易"])
    
    # 获取当前价格
    price = _get_current_price(security)
    
    # 使用EmuTrader的execute_trade方法
    success = _current_emutrader.execute_trade(security, amount, price)
    
    if success:
        # 创建订单对象（向后兼容）
        order_obj = Order.create_market_order(security, amount, price)
        order_obj.status = "filled"
        order_obj.filled = amount
        return order_obj
    else:
        # 根据错误原因抛出相应异常
        portfolio = _current_emutrader.get_portfolio()
        if amount > 0:  # 买入失败
            total_cost = amount * price
            if portfolio.available_cash < total_cost:
                raise InsufficientFundsException(total_cost, portfolio.available_cash, security)
        else:  # 卖出失败
            sell_amount = abs(amount)
            position = portfolio.get_position(security)
            available = position.closeable_amount if position else 0
            if available < sell_amount:
                raise InsufficientPositionException(sell_amount, available, security)
        
        return None


def order_shares(security: str, amount: int, price: Optional[float] = None):
    """
    JoinQuant兼容的下单函数
    
    注意：这个函数需要在策略上下文中使用。
    建议在initialize()中设置全局上下文后使用。
    
    Args:
        security (str): 证券代码
        amount (int): 股票数量
        price (float, optional): 价格
        
    Returns:
        Order: 订单对象，错误时返回None（JQ兼容模式）或抛出异常（严格模式）
    """
    try:
        if price is not None:
            # 直接使用EmuTrader的execute_trade方法，确保使用传入的价格
            if _current_emutrader is None:
                raise ContextException("策略上下文未设置", suggestions=[
                    "使用 get_jq_account() 创建策略上下文",
                    "调用 set_current_emutrader() 设置上下文"
                ])
            
            # 验证证券代码
            _validate_and_raise_security_error(security)
            
            if amount == 0:
                return None
            
            # 验证股数必须是100的整数倍（A股规则）
            if amount % 100 != 0:
                return None  # 非100整数倍返回None
            
            # 使用EmuTrader的execute_trade方法，传入指定价格
            success = _current_emutrader.execute_trade(security, amount, price)
            
            if success:
                # 创建订单对象（向后兼容）
                order_obj = Order.create_market_order(security, amount, price)
                order_obj.status = "filled"
                order_obj.filled = amount
                return order_obj
            else:
                # 根据错误原因抛出相应异常
                portfolio = _current_emutrader.get_portfolio()
                if amount > 0:  # 买入失败
                    total_cost = amount * price
                    if portfolio.available_cash < total_cost:
                        raise InsufficientFundsException(total_cost, portfolio.available_cash, security)
                else:  # 卖出失败
                    sell_amount = abs(amount)
                    position = portfolio.get_position(security)
                    available = position.closeable_amount if position else 0
                    if available < sell_amount:
                        raise InsufficientPositionException(sell_amount, available, security)
                
                return None
        else:
            return order(security, amount, None, 'long')
    except (ContextException, InvalidSecurityException, TradingException, 
            InsufficientFundsException, InsufficientPositionException, 
            SubPortfolioException) as e:
        # 严格模式下抛出异常，JQ兼容模式下返回None
        if _strict_mode:
            raise
        return None


def order_value(security: str, value: float, price: Optional[float] = None) -> Optional[Order]:
    """
    按金额下单 - JoinQuant兼容全局函数
    
    Args:
        security: 证券代码
        value: 金额 (正数买入，负数卖出)
        price: 指定价格 (None=使用当前价格)
        
    Returns:
        Order对象，失败时返回None（JQ兼容模式）或抛出异常（严格模式）
    """
    try:
        if abs(value) < 0.01:  # 金额太小
            return None
        
        # 获取价格
        if price is None:
            price = _get_current_price(security)
        
        # 计算股数
        if value > 0:  # 买入
            amount = int(value / price)
            # 确保是100股的整数倍
            amount = (amount // 100) * 100
        else:  # 卖出
            sell_value = abs(value)
            amount = -int(sell_value / price)
            # 确保是100股的整数倍
            amount = -((abs(amount) // 100) * 100)
        
        if amount == 0:
            return None
        
        return order_with_price(security, amount, price)
    except (ContextException, InvalidSecurityException, TradingException, 
            InsufficientFundsException, InsufficientPositionException, 
            SubPortfolioException) as e:
        if _strict_mode:
            raise
        return None


def order_target_percent(security: str, percent: float, style=None) -> Optional[Order]:
    """
    调整到目标仓位比例 - JoinQuant兼容全局函数
    
    Args:
        security: 证券代码
        percent: 目标比例 (0.1 = 10%)
        style: 下单方式
        
    Returns:
        Order对象，失败时返回None（JQ兼容模式）或抛出异常（严格模式）
    """
    try:
        if _current_emutrader is None:
            if _strict_mode:
                raise ContextException("策略上下文未设置", suggestions=[
                    "使用 get_jq_account() 创建策略上下文",
                    "调用 set_current_emutrader() 设置上下文"
                ])
            return None  # JQ兼容模式：无上下文时返回None
        
        if abs(percent) < 0.0001:  # 比例太小，相当于清仓
            return order_target(security, 0, style)
        
        # 获取总价值
        if not _current_emutrader.get_subportfolios():
            total_value = _current_emutrader.get_portfolio().total_value
        else:
            # 从子账户中寻找股票账户
            stock_subportfolio = None
            for sub in _current_emutrader.get_subportfolios():
                if hasattr(sub, 'type') and sub.type == 'STOCK':
                    stock_subportfolio = sub
                    break
            
            if stock_subportfolio is None:
                if _strict_mode:
                    raise SubPortfolioException("没有找到股票子账户", subportfolio_type='STOCK',
                                               suggestions=[
                                                   "确保子账户配置中包含股票账户",
                                                   "检查子账户类型设置是否正确"
                                               ])
                return None  # 无股票子账户时返回None
            total_value = stock_subportfolio.total_value
        
        # 计算目标金额
        target_value = total_value * percent
        
        return order_target_value(security, target_value, style)
    except (ContextException, InvalidSecurityException, TradingException, 
            InsufficientFundsException, InsufficientPositionException, 
            SubPortfolioException) as e:
        if _strict_mode:
            raise
        return None


def order_target(security: str, amount: int, style=None) -> Optional[Order]:
    """
    调整到目标股数 - JoinQuant兼容全局函数
    
    Args:
        security: 证券代码
        amount: 目标股数
        style: 下单方式
        
    Returns:
        Order对象，失败时返回None
    """
    if _current_emutrader is None:
        raise ContextException("策略上下文未设置", suggestions=[
            "使用 get_jq_account() 创建策略上下文",
            "调用 set_current_emutrader() 设置上下文"
        ])
    
    # 获取当前持仓
    if not _current_emutrader.get_subportfolios():
        current_position = _current_emutrader.get_portfolio().get_position(security)
    else:
        # 从子账户中寻找股票账户
        stock_subportfolio = None
        for sub in _current_emutrader.get_subportfolios():
            if hasattr(sub, 'type') and sub.type == 'STOCK':
                stock_subportfolio = sub
                break
        
        if stock_subportfolio is None:
            raise SubPortfolioException("没有找到股票子账户", subportfolio_type='STOCK',
                                       suggestions=[
                                           "确保子账户配置中包含股票账户",
                                           "检查子账户类型设置是否正确"
                                       ])
        current_position = stock_subportfolio.get_position(security)
    
    current_amount = current_position.total_amount if current_position else 0
    
    # 计算需要调整的数量
    adjust_amount = amount - current_amount
    
    if adjust_amount == 0:
        return None
    
    return order(security, adjust_amount, style)


def order_target_value(security: str, value: float, style=None) -> Optional[Order]:
    """
    调整到目标金额 - JoinQuant兼容全局函数
    
    Args:
        security: 证券代码
        value: 目标金额
        style: 下单方式
        
    Returns:
        Order对象，失败时返回None
    """
    if abs(value) < 0.01:  # 目标金额太小，相当于清仓
        return order_target(security, 0, style)
    
    # 获取当前价格
    price = _get_current_price(security)
    
    # 计算目标股数
    target_amount = int(value / price)
    # 确保是100股的整数倍
    target_amount = (target_amount // 100) * 100
    
    return order_target(security, target_amount, style)


# ===============================
# 子账户API实现
# ===============================

def set_subportfolios(configs: List[SubPortfolioConfig]):
    """
    设置子账户配置 - JoinQuant兼容全局函数
    
    Args:
        configs: 子账户配置列表
        
    Raises:
        ValueError: 当配置无效时
        RuntimeError: 当策略上下文未设置时
    """
    if _current_emutrader is None:
        raise RuntimeError("策略上下文未设置，请在initialize()函数中调用")
    
    if not configs:
        raise ValueError("子账户配置不能为空")
    
    if len(configs) > 100:
        raise ValueError("子账户数量不能超过100个")
    
    # 验证总资金是否匹配主账户
    total_sub_cash = sum(config.cash for config in configs)
    main_portfolio_cash = _current_emutrader.get_portfolio().available_cash
    
    if abs(total_sub_cash - main_portfolio_cash) > 0.01:  # 允许1分钱误差
        raise ValueError(f"子账户总资金({total_sub_cash:.2f})与主账户资金({main_portfolio_cash:.2f})不匹配")
    
    # 通过AccountContext进行子账户管理
    account_context = _current_emutrader._account_context
    
    # 清空现有子账户
    account_context._subportfolios.clear()
    
    # 创建新的子账户
    from .core.subportfolio import SubPortfolio
    for i, config in enumerate(configs):
        subportfolio = SubPortfolio(
            type=config.to_account_type(),
            initial_cash=config.cash,
            index=i
        )
        account_context.add_subportfolio(subportfolio)
    
    # 更新主账户资金（因为资金已分配到子账户）
    account_context._portfolio._available_cash = 0.0


def transfer_cash(from_pindex: int, to_pindex: int, cash: float) -> bool:
    """
    子账户间资金转移 - JoinQuant兼容全局函数
    
    Args:
        from_pindex: 源子账户索引
        to_pindex: 目标子账户索引
        cash: 转移金额
        
    Returns:
        是否转移成功
        
    Raises:
        RuntimeError: 当策略上下文未设置时
        ValueError: 当参数无效时
    """
    if _current_emutrader is None:
        raise RuntimeError("策略上下文未设置")
    
    if cash <= 0:
        raise ValueError("转移金额必须大于0")
    
    if from_pindex == to_pindex:
        raise ValueError("源账户和目标账户不能相同")
    
    # 获取子账户
    from_subportfolio = _current_emutrader.get_subportfolio(from_pindex)
    to_subportfolio = _current_emutrader.get_subportfolio(to_pindex)
    
    if from_subportfolio is None:
        raise ValueError(f"源子账户索引无效: {from_pindex}")
    
    if to_subportfolio is None:
        raise ValueError(f"目标子账户索引无效: {to_pindex}")
    
    # 执行转移
    return from_subportfolio.transfer_cash_to(to_subportfolio, cash)


# ===============================
# 滑点设置API
# ===============================

def set_slippage(slippage_object, security_type=None, ref=None):
    """
    设定滑点，回测/模拟时有效
    
    当您下单后，真实的成交价格与下单时预期的价格总会有一定偏差，
    因此我们加入了滑点模式来帮您更好的模拟真实市场的表现。
    我们也支持为交易品种和特定的交易标的设置滑点。
    
    Args:
        slippage_object: 滑点对象，支持以下类型：
            - FixedSlippage(fixed_value): 固定值滑点
            - PriceRelatedSlippage(percentage): 百分比滑点  
            - StepRelatedSlippage(steps): 跳数滑点（期货专用）
        type: 交易品种类型，支持：
            - 'stock': 股票
            - 'fund': 场内基金
            - 'mmf': 场内交易的货币基金
            - 'fja': 分级A基金
            - 'fjb': 分级B基金
            - 'fjm': 分级母基金
            - 'index_futures': 金融期货
            - 'futures': 期货
            - 'bond_fund': 债券基金
            - 'stock_fund': 股票基金
            - 'QDII_fund': QDII基金
            - 'mixture_fund': 混合基金
            - 'money_market_fund': 货币基金
            为None时则应用于全局。当type被设定而ref为None时，
            表示将滑点应用于交易品种为type的所有交易标的。
        ref: 标的代码。如要为特定交易标的单独设置滑点，
            必须同时设置type为交易标的的交易品种。
            如 '000001.XSHE'/'510180.XSHG'/'IF1709'/'IF'/'000300.OF'
    
    Examples:
        # 为全部交易品种设定固定值滑点
        set_slippage(FixedSlippage(0.02))
        
        # 为股票设定滑点为百分比滑点
        set_slippage(PriceRelatedSlippage(0.002), type='stock')
        
        # 设置CU品种的滑点为跳数滑点2
        set_slippage(StepRelatedSlippage(2), type='futures', ref='CU')
        
        # 为螺纹钢RB1809设定滑点为跳数滑点
        set_slippage(StepRelatedSlippage(2), type='futures', ref="RB1809.XSGE")
    
    Raises:
        ContextException: 当策略上下文未设置时
        ValidationException: 当参数无效时
    
    Note:
        (1) 如果您没有调用 set_slippage 函数, 系统默认的滑点是 PriceRelatedSlippage(0.00246)；
        (2) 所有类型为 "mmf"与"money_market_fund"的标的滑点默认为0，且调用set_slippage重新设置也不会生效。
    """
    if _current_emutrader is None:
        raise ContextException("策略上下文未设置", suggestions=[
            "使用 get_jq_account() 创建策略上下文",
            "调用 set_current_emutrader() 设置上下文"
        ])
    
    # 导入滑点相关类
    from .core.slippage import SlippageBase
    
    # 验证滑点对象类型
    if not isinstance(slippage_object, SlippageBase):
        obj_type = type(slippage_object)
        field_value = getattr(obj_type, '__name__', str(obj_type))
        raise ValidationException(
            "slippage_object必须是滑点对象",
            field_name="slippage_object",
            field_value=field_value,
            suggestions=[
                "使用 FixedSlippage(fixed_value) 创建固定值滑点",
                "使用 PriceRelatedSlippage(percentage) 创建百分比滑点",
                "使用 StepRelatedSlippage(steps) 创建跳数滑点"
            ]
        )
    
    # 验证security_type参数
    valid_types = {
        'stock', 'fund', 'mmf', 'fja', 'fjb', 'fjm',
        'index_futures', 'futures', 'bond_fund', 'stock_fund',
        'QDII_fund', 'mixture_fund', 'money_market_fund'
    }
    
    if security_type is not None and security_type not in valid_types:
        raise ValidationException(
            f"无效的交易品种类型: {security_type}",
            field_name="type",
            field_value=security_type,
            suggestions=[f"支持的类型: {valid_types}"]
        )
    
    # 验证ref参数逻辑
    if ref is not None and not isinstance(ref, str):
        raise ValidationException("ref参数必须是字符串或None")
    
    if ref is not None and security_type is None:
        raise ValidationException("设置具体标的滑点时必须指定type参数")
    
    # 调用EmuTrader的滑点设置方法
    _current_emutrader.set_slippage(slippage_object, security_type, ref)


# 兼容性别名
create_jq_account = get_jq_account  # 别名