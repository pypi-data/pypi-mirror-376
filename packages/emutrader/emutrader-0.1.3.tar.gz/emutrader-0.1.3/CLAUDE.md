# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**EmuTrader** 是一个专为量化交易设计的Python账户管理库，专注于提供高性能的账户状态管理和实时盈亏计算功能。项目核心特色是**100%兼容JoinQuant API**，为QSM等策略系统提供强大的账户管理能力。

### 🎯 重构完成状态（2025年1月）

✅ **专业账户管理库架构**
- AccountContext类：专注账户数据管理，移除策略相关属性
- EmuTrader主类：为QSM提供完整的账户管理接口
- Portfolio/Position类：实时盈亏计算和状态管理
- 数据持久化：load_from_db, save_to_db接口

✅ **QSM集成接口**
- 价格更新：update_market_price(), batch_update_prices()
- 交易执行：execute_trade()方法
- 账户访问：get_portfolio(), get_subportfolios()
- 行情订阅：get_all_securities()方法

✅ **JQ兼容API保持**
- get_jq_account()：返回EmuTrader实例，提供JQ兼容接口
- 交易函数：order_shares(), order_value(), order_target_percent()
- 子账户：set_subportfolios(), transfer_cash()

## Development Commands

### Setup and Installation
```bash
# 安装项目依赖
pip install -r requirements.txt

# 开发模式安装
pip install -e .

# 安装开发依赖
pip install -e ".[dev]"
```

### Testing
```bash
# 运行所有测试
pytest

# 运行测试并生成覆盖率报告
pytest --cov=emutrader

# 运行特定测试文件
pytest tests/test_specific.py

# 运行特定测试函数
pytest tests/test_specific.py::test_function_name
```

### Code Quality
```bash
# 代码格式化
black .

# 代码检查
flake8 emutrader tests

# 类型检查
mypy emutrader
```

### Building and Distribution
```bash
# 构建包
python -m build

# 安装到本地
pip install .
```

## Architecture Overview - 重构后架构

### 新架构核心设计

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

### 重构后项目结构

```
emutrader/
├── __init__.py                    # ✅ 导出重构后的API
├── api.py                        # ✅ 适配新架构的JQ兼容函数
├── core/                         # ✅ 核心模块（重构完成）
│   ├── context.py                # ✅ AccountContext（专注账户管理）
│   ├── trader.py                 # ✅ EmuTrader主类（QSM接口）
│   ├── portfolio.py              # ✅ Portfolio投资组合
│   ├── position.py               # ✅ Position持仓对象
│   ├── subportfolio.py           # ✅ SubPortfolio子账户
│   ├── account.py                # ✅ Account账户（向后兼容）
│   ├── models.py                 # ✅ 数据模型
│   ├── order.py                  # ✅ 订单对象
│   └── strategy.py               # 🔄 Strategy基类（可选）
├── handlers/                     # 🔄 处理器层（可选扩展）
├── utils/                        # 🔄 工具模块（可选扩展）
├── exceptions.py                 # ✅ 异常定义
└── tests/                        # 📋 测试目录
```

### 重构后的核心架构组件

#### ✅ 专业账户管理层（重构完成）
- `AccountContext`: 专注账户数据管理，不含策略相关属性
- `EmuTrader`: 账户管理主类，为QSM提供完整接口
- `Portfolio`: 投资组合管理（total_value, available_cash, 实时盈亏）
- `Position`: 持仓对象（total_amount, avg_cost, pnl, 价格更新）

#### ✅ QSM集成接口层（新增）
- 价格更新：`update_market_price()`, `batch_update_prices()`
- 交易执行：`execute_trade()`账户状态更新
- 数据持久化：`load_from_db()`, `save_to_db()`
- 行情订阅：`get_all_securities()`获取持仓列表

#### ✅ JQ兼容API层（保持兼容）
- `get_jq_account()`: 返回EmuTrader实例，提供JQ兼容属性
- 交易函数：`order_shares()`, `order_value()`, `order_target_percent()`
- 子账户：`set_subportfolios()`, `transfer_cash()`

#### ✅ 数据模型层（保持稳定）
- `Order`: 订单模型和工厂方法
- `SubPortfolio`: 子账户支持4种类型
- `SubPortfolioConfig`: 子账户配置

### Key Dependencies
**核心依赖（必需）**:
- **基础数据处理**: numpy, pandas
- **配置管理**: pyyaml (配置), loguru (日志)
- **类型检查**: typing-extensions

**可选依赖（按需安装）**:
- **analysis**: matplotlib, scipy (数据可视化和分析)

**数据获取（用户单独安装）**:
- 建议用户根据需要单独安装数据源：akshare、yfinance、tushare等
- EmuTrader专注于账户管理，不绑定特定数据源

## Development Notes

### 重构完成状态（2025年1月重大升级！）
✅ **专业账户管理库重构完成**
- 职责清晰：EmuTrader专注账户管理，QSM专注策略逻辑
- 数据闭环：DB加载 → 内存实时更新 → 定期保存
- 性能优化：内存计算 + 批量操作 + QSM控制保存时机
- JQ兼容：现有策略代码无需修改，context.portfolio = EmuTrader.get_portfolio()

### 核心功能实现状态

✅ **重构完成的关键特性**
1. **AccountContext重构** - 移除策略属性，专注账户数据
2. **EmuTrader主类** - 提供完整的QSM集成接口
3. **价格更新机制** - 支持单个和批量价格更新
4. **交易执行接口** - execute_trade()方法处理账户状态更新
5. **数据持久化** - load_from_db(), save_to_db()方法
6. **JQ API保持兼容** - get_jq_account()返回EmuTrader实例

🔄 **下个版本规划**
1. 数据库性能优化和高级查询支持
2. 更多交易品种和复杂订单类型
3. 账户状态监控和告警机制
4. 多策略账户隔离和资源管理

### 架构重构优势
1. ✅ **职责分离** - EmuTrader账户管理，QSM策略执行
2. ✅ **性能优化** - 内存实时计算，定期批量保存
3. ✅ **扩展性强** - 支持多种策略系统接入
4. ✅ **向后兼容** - JQ策略代码无需修改

### Code Style
- 使用Black进行代码格式化 (line-length: 88)
- 支持Python 3.8+
- 启用类型注释 (mypy配置已设置)
- 使用pytest作为测试框架

### File Naming Conventions
- 测试文件: `test_*.py` 或 `*_test.py`
- 配置遵循pyproject.toml中的设置
- 包含中文注释和文档字符串支持

## Performance Targets

根据重构后的新性能目标：

| 指标 | 目标 | 实现方式 |
|------|------|----------|
| 价格更新响应时间 | < 5ms | 内存操作 |
| 盈亏计算时间 | < 10ms | 实时计算 |
| 交易执行时间 | < 50ms | 账户状态更新 |
| 批量价格更新 | > 1000/s | 批量操作优化 |
| 内存占用 | < 50MB | 轻量级设计 |
| 数据库保存 | < 100ms | SQLite优化 |

## API Compatibility - 重构后兼容性

### ✅ 100% JoinQuant API兼容性（保持不变）
- **完全兼容**现有JQ策略代码，零修改迁移
- **EmuTrader对象**：context = get_jq_account()返回EmuTrader实例
- **Portfolio访问**：context.portfolio = emutrader.get_portfolio()
- **子账户访问**：context.subportfolios = emutrader.get_subportfolios()
- **全局交易函数**：order_shares(), order_value(), order_target_percent()
- **子账户系统**：set_subportfolios(), transfer_cash()

### ✅ 使用示例（重构后）

#### JQ兼容使用（无需修改）
```python
# 1. 创建JQ兼容的账户管理对象
from emutrader import get_jq_account, set_subportfolios, SubPortfolioConfig
from emutrader import order_shares, order_target_percent, transfer_cash

# context实际是EmuTrader实例，但提供JQ兼容接口
context = get_jq_account("my_strategy", 100000, "STOCK")

# 2. 100%兼容JQ的账户访问
print(f"总资产: {context.portfolio.total_value}")
print(f"可用资金: {context.portfolio.available_cash}")  
print(f"持仓市值: {context.portfolio.market_value}")

# 3. 交易操作 - 与JQ完全相同
order_shares('000001.SZ', 1000)
order_target_percent('600519.SH', 0.3)
```

#### QSM策略系统集成
```python
# 1. QSM创建EmuTrader实例
emutrader = get_jq_account("my_strategy", 100000)
emutrader.load_from_db("account.db")  # 加载初始状态

# 2. QSM创建自己的策略上下文
class QSMStrategyContext:
    def __init__(self, emutrader):
        self.current_dt = datetime.now()  # QSM管理时间
        self._emutrader = emutrader       # 引用账户管理器
    
    @property
    def portfolio(self):
        return self._emutrader.get_portfolio()

# 3. QSM运行时集成
context = QSMStrategyContext(emutrader)

# 订阅行情
securities = emutrader.get_all_securities()
market_data.subscribe(securities)

# 处理tick数据
def on_tick(security, price):
    emutrader.update_market_price(security, price)

# 策略交易
def qsm_order_shares(security, amount):
    price = get_current_price(security)
    return emutrader.execute_trade(security, amount, price)

# 定期保存
emutrader.save_to_db()
```

### ✅ 重构后兼容性对照表

| JoinQuant API | EmuTrader 重构后实现 | 兼容性 |
|---------------|---------------------|--------|
| `context = get_jq_account()` | 返回EmuTrader实例 | 100% |
| `context.portfolio.total_value` | emutrader.get_portfolio().total_value | 100% |
| `context.portfolio.available_cash` | emutrader.get_portfolio().available_cash | 100% |
| `context.subportfolios[i]` | emutrader.get_subportfolios()[i] | 100% |
| `order_shares('000001.SZ', 1000)` | 内部调用emutrader.execute_trade() | 100% |
| `order_value()`, `order_target_percent()` | 完全兼容 | 100% |
| `set_subportfolios()` | 设置emutrader的子账户 | 100% |
| `transfer_cash()` | emutrader.transfer_cash() | 100% |

### 🚀 新增QSM专用接口

| QSM需求 | EmuTrader接口 | 说明 |
|---------|---------------|------|
| tick数据推送 | `update_market_price()` | 单个价格更新 |
| 批量价格更新 | `batch_update_prices()` | 高性能批量操作 |
| 交易执行 | `execute_trade()` | 账户状态更新 |
| 数据持久化 | `load_from_db()`, `save_to_db()` | QSM控制保存时机 |
| 行情订阅 | `get_all_securities()` | 获取持仓证券列表 |

## 📊 Portfolio与SubPortfolio关系说明

### 🎯 核心关系
```
总账户 (Portfolio)    ←→    子账户列表 (SubPortfolio[0], SubPortfolio[1], ...)
     │                          │
     ├── 总资产: 100万           ├── 子账户0: 60万 (股票)
     ├── 可用资金: 30万           ├── 子账户1: 40万 (期货)  
     └── 所有持仓汇总            └── 子账户2: 0万 (融资融券)
```

### 🔍 关键区别

#### Portfolio (总账户)
- **汇总视图**：所有子账户的聚合信息
- **默认行为**：如果没有设置SubPortfolioConfig，只有一个SubPortfolio[0]
- **属性计算**：`total_value` = 所有子账户总和
- **持仓访问**：`context.portfolio.positions` 实际指向 `context.subportfolios[0].positions`
- **向下兼容**：现有策略代码无需修改

#### SubPortfolio (子账户)  
- **独立单元**：每个子账户有独立的资金、持仓、类型
- **多仓位支持**：可设置多个不同类型的子账户（股票、期货、融资融券等）
- **资金隔离**：子账户之间需要转账操作
- **类型专属**：每个子账户有特定的账户类型

### 💡 实际使用场景

```python
# 场景1：简单使用（默认）
context = get_jq_account("strategy", 100000)
# 实际上：context.portfolio ≈ context.subportfolios[0]

# 场景2：多仓位管理
set_subportfolios([
    SubPortfolioConfig(cash=60000, type='stock'),      # 股票账户
    SubPortfolioConfig(cash=40000, type='futures')    # 期货账户
])

# 访问方式
print(f"总资产: {context.portfolio.total_value}")
print(f"股票账户: {context.subportfolios[0].total_value}")  
print(f"期货账户: {context.subportfolios[1].total_value}")
```

### 🔄 设计意图
1. **向下兼容**：现有策略代码无需修改
2. **扩展能力**：支持多账户、多品种策略
3. **风险隔离**：不同类型交易在不同子账户进行
4. **清晰核算**：每个子账户独立计算盈亏

### ⚠️ 重要说明
Portfolio本质上是SubPortfolio的聚合视图，这就是为什么它们的属性几乎相同的原因。在简单使用场景下，`context.portfolio`和`context.subportfolios[0]`是等价的。

## 重构文档

详细的重构过程和架构设计请参考：
- [docs/ARCHITECTURE_REFACTOR.md](docs/ARCHITECTURE_REFACTOR.md) - 完整重构文档
- [README.md](README.md) - 最新的项目介绍

## important-instruction-reminders
Do what has been asked; nothing more, nothing less.
NEVER create files unless they're absolutely necessary for achieving your goal.
ALWAYS prefer editing an existing file to creating a new one.
NEVER proactively create documentation files (*.md) or README files. Only create documentation files if explicitly requested by the User.