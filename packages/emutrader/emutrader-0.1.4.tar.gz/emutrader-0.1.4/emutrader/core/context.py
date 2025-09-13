"""
账户上下文模块 - 提供账户数据访问接口

该模块实现了账户上下文对象，专注于账户数据管理：
- portfolio: 投资组合对象  
- subportfolios: 子账户列表
- 价格更新和交易执行接口
- 数据持久化接口
"""

from datetime import datetime
from typing import Dict, List, Any, Optional
from .portfolio import Portfolio
from .subportfolio import SubPortfolio


class AccountContext:
    """
    账户上下文对象 - 专注账户数据管理
    
    提供账户相关的数据访问和操作接口，包括投资组合、子账户、
    价格更新和交易执行等功能。不包含策略相关的时间和参数管理。
    """
    
    def __init__(self, 
                 initial_cash: float = 100000.0,
                 account_type: str = "stock",
                 strategy_name: str = "default"):
        """
        初始化账户上下文
        
        Args:
            initial_cash: 初始资金
            account_type: 账户类型
            strategy_name: 策略名称
        """
        self._portfolio: Portfolio = Portfolio(
            initial_cash=initial_cash,
            account_type=account_type.upper() if isinstance(account_type, str) else account_type,
            strategy_name=strategy_name
        )
        self._subportfolios: List[SubPortfolio] = []
        # 移除策略相关属性：current_dt, run_params
        
    @property
    def portfolio(self) -> Portfolio:
        """投资组合对象 - JoinQuant兼容属性"""
        if self._subportfolios:
            # 如果有子账户，返回聚合视图
            return self._create_aggregated_portfolio()
        return self._portfolio
    
    @property
    def subportfolios(self) -> List[SubPortfolio]:
        """子账户列表 - JoinQuant兼容属性"""
        return self._subportfolios
    
    @subportfolios.setter
    def subportfolios(self, value: List[SubPortfolio]):
        """设置子账户列表"""
        self._subportfolios = value
        
    
                
    def add_subportfolio(self, subportfolio: SubPortfolio):
        """
        添加子账户
        
        Args:
            subportfolio: 子账户对象
        """
        self._subportfolios.append(subportfolio)
        
    def get_subportfolio(self, index: int) -> Optional[SubPortfolio]:
        """
        获取指定索引的子账户
        
        Args:
            index: 子账户索引
            
        Returns:
            子账户对象，如果索引无效则返回None
        """
        if 0 <= index < len(self._subportfolios):
            return self._subportfolios[index]
        return None
    
    def get_subportfolio_by_type(self, account_type: str) -> Optional[SubPortfolio]:
        """
        根据账户类型获取子账户
        
        Args:
            account_type: 账户类型 ('STOCK', 'FUTURE', 'CREDIT'等)
            
        Returns:
            匹配的子账户对象，如果没有找到则返回None
        """
        for subportfolio in self._subportfolios:
            if subportfolio.type == account_type:
                return subportfolio
        return None
    
    def transfer_cash_between_subportfolios(self, 
                                          from_index: int, 
                                          to_index: int, 
                                          amount: float) -> bool:
        """
        在子账户间转移资金
        
        Args:
            from_index: 源子账户索引
            to_index: 目标子账户索引  
            amount: 转移金额
            
        Returns:
            是否转移成功
        """
        from_sub = self.get_subportfolio(from_index)
        to_sub = self.get_subportfolio(to_index)
        
        if from_sub is None or to_sub is None:
            return False
            
        if from_sub.available_cash < amount:
            return False
            
        # 执行转移
        from_sub._available_cash -= amount
        to_sub._available_cash += amount
        
        return True
    
    # ===============================
    # QSM接口：价格更新
    # ===============================
    
    def update_market_price(self, security: str, price: float, timestamp: Optional[datetime] = None):
        """
        更新单个证券的市场价格
        
        Args:
            security: 证券代码
            price: 最新价格
            timestamp: 价格时间戳（可选）
        """
        if timestamp is None:
            timestamp = datetime.now()
            
        # 更新主账户持仓价格
        self._portfolio.update_position_price(security, price)
        
        # 更新所有子账户的持仓价格
        for subportfolio in self._subportfolios:
            if hasattr(subportfolio, 'update_position_price'):
                subportfolio.update_position_price(security, price)
    
    def batch_update_prices(self, price_data: Dict[str, float], timestamp: Optional[datetime] = None):
        """
        批量更新多个证券的市场价格
        
        Args:
            price_data: 证券代码到价格的映射
            timestamp: 价格时间戳（可选）
        """
        if timestamp is None:
            timestamp = datetime.now()
            
        for security, price in price_data.items():
            self.update_market_price(security, price, timestamp)
    
    def get_all_securities(self) -> List[str]:
        """
        获取所有持仓证券代码列表（供QSM订阅行情使用）
        
        Returns:
            证券代码列表
        """
        securities = set()
        
        # 从主账户获取
        securities.update(self._portfolio.positions.keys())
        
        # 从所有子账户获取
        for subportfolio in self._subportfolios:
            if hasattr(subportfolio, 'positions') and subportfolio.positions:
                securities.update(subportfolio.positions.keys())
        
        return list(securities)
    
    # ===============================
    # QSM接口：交易执行
    # ===============================
    
    def execute_trade(self, security: str, amount: int, price: float, 
                     subportfolio_index: Optional[int] = None,
                     total_cost: Optional[float] = None,
                     commission: Optional[float] = None,
                     tax: Optional[float] = None,
                     transfer_fee: Optional[float] = None) -> bool:
        """
        执行交易（供QSM调用）
        
        Args:
            security: 证券代码
            amount: 交易数量（正数买入，负数卖出）
            price: 交易价格
            subportfolio_index: 子账户索引，None表示使用主账户
            total_cost: 总交易成本（可选）
            commission: 佣金费用（可选）
            tax: 印花税费用（可选）
            
        Returns:
            是否执行成功
        """
        if amount == 0:
            return True
            
        # 选择执行账户
        if subportfolio_index is None:
            if not self._subportfolios:
                # 没有子账户，使用主账户
                target_portfolio = self._portfolio
            else:
                # 有子账户但没有指定索引，自动选择股票子账户
                stock_sub = None
                for sub in self._subportfolios:
                    if hasattr(sub, 'type') and sub.type.upper() == 'STOCK':
                        stock_sub = sub
                        break
                if stock_sub is None:
                    return False  # 没有找到股票子账户
                target_portfolio = stock_sub
        else:
            if 0 <= subportfolio_index < len(self._subportfolios):
                target_portfolio = self._subportfolios[subportfolio_index]
            else:
                return False  # 无效的子账户索引
        
        if amount > 0:  # 买入
            trade_value = amount * price
            
            # 计算总成本（包含交易成本）
            if total_cost is not None:
                # 使用传入的交易成本
                total_amount_needed = trade_value + total_cost
            else:
                # 没有传入交易成本，只计算交易价值
                total_amount_needed = trade_value
                total_cost = 0.0
                commission = 0.0
                tax = 0.0
            
            if target_portfolio.available_cash < total_amount_needed:
                return False  # 资金不足
            
            # 执行买入
            target_portfolio.reduce_cash(total_amount_needed)
            # 如果有交易成本，调整持仓成本（包含佣金和过户费）
            if total_cost > 0:
                # A股规则：成本价应包含佣金和过户费，但不包含印花税（买入无印花税）
                transaction_costs = commission + (transfer_fee if transfer_fee else 0)
                avg_price_with_cost = (trade_value + transaction_costs) / amount
                target_portfolio.add_position(security, amount, avg_price_with_cost)
            else:
                target_portfolio.add_position(security, amount, price)
            
        else:  # 卖出
            sell_amount = abs(amount)
            position = target_portfolio.get_position(security)
            available = position.closeable_amount if position else 0
            
            if available < sell_amount:
                return False  # 持仓不足
            
            # 执行卖出
            target_portfolio.reduce_position(security, sell_amount)
            trade_value = sell_amount * price
            
            # 计算实际获得资金（扣除交易成本）
            if total_cost is not None:
                net_proceeds = trade_value - total_cost
            else:
                net_proceeds = trade_value
                total_cost = 0.0
                commission = 0.0
                tax = 0.0
            
            target_portfolio.add_cash(net_proceeds)
        
        return True
    
    # ===============================
    # QSM接口：数据持久化
    # ===============================
    
    def load_from_db(self, db_path: str) -> bool:
        """
        从数据库加载账户状态（供QSM调用）
        
        Args:
            db_path: 数据库文件路径
            
        Returns:
            是否加载成功
        """
        # TODO: 实现数据库加载逻辑
        # 这里先返回True，实际实现时需要：
        # 1. 检查db文件是否存在
        # 2. 读取portfolio和subportfolios数据
        # 3. 重建账户状态
        return True
    
    def save_to_db(self, db_path: Optional[str] = None) -> bool:
        """
        保存账户状态到数据库（供QSM调用）
        
        Args:
            db_path: 数据库文件路径，None表示使用默认路径
            
        Returns:
            是否保存成功
        """
        # TODO: 实现数据库保存逻辑
        # 这里先返回True，实际实现时需要：
        # 1. 序列化portfolio和subportfolios数据
        # 2. 写入数据库文件
        # 3. 确保数据一致性
        return True
    
    def get_context_info(self) -> Dict[str, Any]:
        """
        获取账户完整信息
        
        Returns:
            包含所有账户信息的字典
        """
        return {
            'portfolio': {
                'total_value': self.portfolio.total_value,
                'available_cash': self.portfolio.available_cash,
                'market_value': self.portfolio.market_value,
                'positions_count': len(self.portfolio.positions),
                'pnl': self.portfolio.pnl,
                'returns': self.portfolio.returns,
            },
            'subportfolios_count': len(self.subportfolios),
            'subportfolios': [
                {
                    'index': i,
                    'type': sub.type,
                    'total_value': sub.total_value,
                    'available_cash': sub.available_cash,
                    'positions_count': len(sub.positions) if sub.positions else 0,
                } for i, sub in enumerate(self.subportfolios)
            ],
            'all_securities': self.get_all_securities(),
        }
    
    def __repr__(self) -> str:
        """字符串表示"""
        return (f"AccountContext("
                f"portfolio_value={self.portfolio.total_value:.2f}, "
                f"subportfolios_count={len(self.subportfolios)}, "
                f"securities_count={len(self.get_all_securities())})")
    
    def _create_aggregated_portfolio(self) -> Portfolio:
        """创建聚合所有子账户的Portfolio视图"""
        from .portfolio import Portfolio
        from .position import Position
        
        # 计算聚合的总资产和现金
        total_cash = sum(sub.available_cash for sub in self._subportfolios)
        total_locked_cash = sum(getattr(sub, 'locked_cash', 0) for sub in self._subportfolios)
        
        # 聚合所有持仓
        aggregated_positions = {}
        for sub in self._subportfolios:
            if hasattr(sub, 'positions') and sub.positions:
                for security, position in sub.positions.items():
                    if position.total_amount > 0:
                        if security in aggregated_positions:
                            # 合并同一证券的持仓
                            existing = aggregated_positions[security]
                            total_amount = existing.total_amount + position.total_amount
                            total_cost = (existing.avg_cost * existing.total_amount + 
                                        position.avg_cost * position.total_amount)
                            avg_cost = total_cost / total_amount if total_amount > 0 else 0
                            aggregated_positions[security].total_amount = total_amount
                            aggregated_positions[security].avg_cost = avg_cost
                        else:
                            # 创建新的聚合持仓
                            new_position = Position(
                                security=security,
                                total_amount=position.total_amount,
                                avg_cost=position.avg_cost,
                                last_price=position.last_price
                            )
                            # 设置可卖数量（Position类使用内部属性）
                            new_position._closeable_amount = position.closeable_amount
                            aggregated_positions[security] = new_position
        
        # 创建聚合Portfolio
        aggregated_portfolio = Portfolio(
            account_type=self._portfolio.account_type,
            strategy_name=self._portfolio.strategy_name,
            initial_cash=self._portfolio.initial_cash
        )
        
        # 设置聚合的资金和持仓
        aggregated_portfolio._available_cash = total_cash
        aggregated_portfolio._locked_cash = total_locked_cash
        aggregated_portfolio._positions = aggregated_positions
        
        # 更新聚合的盈亏计算
        aggregated_portfolio.update_daily_pnl()
        
        return aggregated_portfolio