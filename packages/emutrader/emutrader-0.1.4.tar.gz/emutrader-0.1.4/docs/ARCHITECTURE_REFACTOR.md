# EmuTrader 架构重构完成文档

## 📋 重构概述

**重构时间**: 2025年1月

**核心目标**: 将EmuTrader从策略框架重构为纯粹的账户管理库，解决与QSM策略系统的职责冲突问题。

## 🔄 架构对比

### 重构前
```
EmuTrader (策略框架)
├── StrategyContext (策略上下文)
│   ├── current_dt (时间管理)
│   ├── run_params (策略参数)
│   ├── portfolio (账户数据)
│   └── subportfolios (子账户)
├── 交易API (order_shares等)
└── 策略执行引擎
```

### 重构后  
```
QSM策略系统                    EmuTrader账户管理库
├── StrategyContext           ├── AccountContext (账户上下文)
│   ├── current_dt           │   ├── portfolio (投资组合)
│   ├── run_params           │   └── subportfolios (子账户)
│   └── emutrader ────────────┼── EmuTrader主类
├── 行情数据管理               │   ├── 价格更新接口
├── 策略逻辑                  │   ├── 交易执行接口
└── 交易决策                  │   └── 数据持久化接口
                             └── Portfolio/Position核心对象
```

## 🎯 核心变更

### 1. StrategyContext → AccountContext
**变更内容**:
- 重命名: `StrategyContext` → `AccountContext`
- 移除策略相关属性: `current_dt`, `run_params`  
- 专注账户数据管理: `portfolio`, `subportfolios`
- 新增QSM接口: 价格更新、交易执行、数据持久化

**文件路径**: `emutrader/core/context.py`

### 2. EmuTrader主类重构
**变更内容**:
- 成为AccountContext的包装器
- 提供JQ兼容的portfolio/subportfolios属性访问
- 为QSM提供完整的账户管理接口

**文件路径**: `emutrader/core/trader.py`

### 3. API层适配
**变更内容**:
- 全局变量: `_current_context` → `_current_emutrader`
- `get_jq_account()` 返回EmuTrader实例
- 所有交易函数使用EmuTrader接口

**文件路径**: `emutrader/api.py`

## 🔌 QSM集成接口

### 账户数据访问
```python
# QSM的context.portfolio实际是EmuTrader的Portfolio对象
emutrader = get_jq_account("strategy", 100000)
portfolio = emutrader.get_portfolio()  # 返回Portfolio对象
subportfolios = emutrader.get_subportfolios()  # 返回List[SubPortfolio]
```

### 价格数据推送
```python
# QSM推送tick数据到EmuTrader
emutrader.update_market_price('000001.SZ', 12.5)
emutrader.batch_update_prices({
    '000001.SZ': 12.5,
    '000002.SZ': 8.3
})
```

### 交易执行
```python
# QSM调用EmuTrader执行交易
success = emutrader.execute_trade('000001.SZ', 1000, 12.5)  # 买入1000股
success = emutrader.execute_trade('000001.SZ', -500, 12.8)  # 卖出500股
```

### 数据持久化
```python
# QSM管理数据加载和保存
emutrader.load_from_db('account.db')  # 初始化时加载
emutrader.save_to_db()  # 定期保存
```

### 行情订阅支持
```python
# QSM获取需要订阅的证券列表
securities = emutrader.get_all_securities()  # ['000001.SZ', '000002.SZ']
```

## 📊 数据流设计

### 完整的数据闭环
```
1. 初始化阶段:
   DB文件 → EmuTrader.load_from_db() → 内存中的账户状态

2. 运行时阶段:
   QSM.get_all_securities() → 订阅行情
   行情tick → QSM.update_market_price() → 实时盈亏计算
   策略决策 → QSM.execute_trade() → 账户状态更新

3. 持久化阶段:
   内存状态 → EmuTrader.save_to_db() → DB文件更新
```

### 实时计算机制
- **价格更新**: 内存中立即更新Position.last_price
- **盈亏计算**: 基于最新价格实时计算Portfolio.market_value和Position.pnl  
- **批量保存**: QSM定期调用save_to_db()确保数据持久化

## 🎯 使用示例

### QSM策略系统集成
```python
# QSM中的完整使用流程
class QSMStrategyContext:
    def __init__(self):
        # QSM管理策略相关属性
        self.current_dt = datetime.now()
        self.run_params = {'initial_cash': 100000}
        
        # EmuTrader管理账户数据
        self._emutrader = get_jq_account("my_strategy", 100000)
        self._emutrader.load_from_db("accounts.db")
    
    @property
    def portfolio(self):
        """QSM的context.portfolio = EmuTrader的Portfolio"""
        return self._emutrader.get_portfolio()
    
    @property
    def subportfolios(self):
        """QSM的context.subportfolios = EmuTrader的SubPortfolios"""
        return self._emutrader.get_subportfolios()

# QSM策略运行
def qsm_strategy_loop():
    context = QSMStrategyContext()
    
    # 1. 订阅行情
    securities = context._emutrader.get_all_securities()
    market_data.subscribe(securities)
    
    # 2. 处理tick数据
    def on_tick(security, price):
        context._emutrader.update_market_price(security, price)
    
    # 3. 策略逻辑
    def handle_data():
        if context.portfolio.available_cash > 10000:
            # 使用QSM自己的order函数，内部调用emutrader
            qsm_order_shares('000001.SZ', 1000)
    
    # 4. 定期保存
    def save_data():
        context._emutrader.save_to_db()

# QSM的交易函数示例
def qsm_order_shares(security, amount):
    price = get_current_price(security)  # QSM获取价格
    success = context._emutrader.execute_trade(security, amount, price)
    return success
```

### 100% JQ兼容使用
```python
# 现有JQ策略代码无需修改
context = get_jq_account("my_strategy", 100000)

# context实际是EmuTrader实例，但提供JQ兼容接口
print(context.portfolio.total_value)  # 100000.0
print(context.portfolio.available_cash)  # 100000.0
print(len(context.subportfolios))  # 0

# 交易API保持不变
order_shares('000001.SZ', 1000)
order_target_percent('000001.SZ', 0.3)
```

## ✅ 重构验证

### 职责边界验证
- ✅ **EmuTrader**: 专注账户数据管理，不包含策略逻辑
- ✅ **QSM**: 专注策略执行，通过接口操作账户
- ✅ **数据流**: 清晰的输入输出，无循环依赖

### 性能验证  
- ✅ **内存计算**: 价格更新和盈亏计算在内存中完成
- ✅ **批量操作**: 支持批量价格更新，减少函数调用开销
- ✅ **持久化控制**: QSM控制保存时机，避免频繁IO

### 兼容性验证
- ✅ **JQ API**: `get_jq_account()`, `order_shares()`等保持不变
- ✅ **Portfolio访问**: `context.portfolio.total_value`等属性正常
- ✅ **子账户**: `context.subportfolios[0]`访问正常

## 🚀 架构优势

### 1. 职责清晰
- **EmuTrader**: 账户状态 + 数据持久化
- **QSM**: 策略逻辑 + 行情管理 + 交易决策

### 2. 性能优化
- 内存实时计算，避免频繁数据库查询
- 批量价格更新，减少函数调用开销
- QSM控制保存时机，优化IO性能

### 3. 扩展性强
- QSM可以接入多种数据源
- EmuTrader支持多种策略系统
- 接口设计支持未来功能扩展

### 4. 维护简单
- 模块化设计，职责单一
- 接口清晰，便于测试和调试
- 文档完整，便于理解和维护

## 📝 重构总结

**重构成功**: EmuTrader从策略框架成功转型为专业的账户管理库

**核心价值**: 
- 为QSM等策略系统提供强大的账户管理能力
- 保持100% JoinQuant API兼容性
- 实现高性能的实时盈亏计算
- 提供灵活的数据持久化方案

**适用场景**:
- 量化策略回测和实盘交易
- 多账户资金管理
- 实时盈亏监控
- 交易记录管理

重构完成，EmuTrader现在是一个专业、高效、易用的账户管理库！