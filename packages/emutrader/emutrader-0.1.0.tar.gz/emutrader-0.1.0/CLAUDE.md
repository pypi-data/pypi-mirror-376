# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**EmuTrader** 是一个专为量化交易设计的Python独立账户管理库，提供强大的模拟交易和回测功能。项目核心特色是100%兼容JoinQuant API，支持多平台无缝集成，并提供高性能数据持久化解决方案。

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

## Architecture Overview

### Current Project Structure
- **emutrader/**: 主要包目录
  - `__init__.py`: 包初始化文件，定义了预期的API结构
- **tests/**: 测试目录（目前为空）
- **配置文件**: `pyproject.toml`, `setup.py`, `requirements.txt`

### Core Architecture Components

#### 用户接口层 (JQ兼容API)
- `get_jq_account()`: JoinQuant兼容账户创建接口
- `AccountFactory`: 账户工厂模式实现

#### 处理器层 (业务逻辑)
- `StockHandler`: 股票账户处理器
- `FutureHandler`: 期货账户处理器  
- `CreditHandler`: 融资融券账户处理器

#### 适配器层 (平台集成)
- `JQAdapter`: JoinQuant平台适配器
- `QMTAdapter`: 迅投QMT平台适配器
- `MockAdapter`: 模拟交易适配器

#### 存储&缓存层 (数据持久化)
- `CacheManager`: 智能缓存管理器
- `SQLiteStorage`: SQLite数据库存储
- `MemoryStorage`: 内存存储实现

#### Core Modules (Based on __init__.py)
- `core/trader.py`: EmuTrader主类 - 模拟交易环境
- `core/strategy.py`: Strategy基类 - 交易策略接口
- `core/account.py`: Account类 - 虚拟账户管理
- `core/order.py`: Order相关类 - 订单管理系统

#### Utility Modules  
- `utils/data.py`: DataProvider - 数据获取和处理
- `utils/indicators.py`: TechnicalIndicators - 技术指标计算
- `utils/performance.py`: PerformanceAnalyzer - 性能分析工具

### Key Dependencies
- **数据分析**: numpy, pandas, scipy, scikit-learn
- **可视化**: matplotlib, seaborn  
- **金融数据**: yfinance, tushare
- **技术指标**: talib
- **工具**: loguru (日志), pyyaml (配置)

## Development Notes

### Current State
项目正在积极开发中，README.md已完成详细的架构设计和API规范。需要基于README中定义的架构实现各个组件。

### Development Priorities
1. 实现JoinQuant兼容的API接口层 (`get_jq_account()`)
2. 建立账户处理器体系 (Stock/Future/Credit Handlers)
3. 开发平台适配器 (JQ/QMT/Mock Adapters)
4. 实现缓存和存储系统 (CacheManager, SQLiteStorage)
5. 建立完整的测试套件
6. 性能优化和监控系统

### Key Features to Implement
- **JoinQuant API兼容性**: 100%兼容现有JQ策略
- **多账户类型支持**: STOCK/FUTURE/CREDIT/OPTION
- **高性能缓存**: LRU + TTL策略，目标 < 10ms响应
- **线程安全**: 支持多策略并发运行
- **数据持久化**: SQLite + 智能缓存优化

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

根据README.md中定义的性能指标：

| 指标 | 目标 | 实现方式 |
|------|------|----------|
| 查询响应时间 | < 10ms | 智能缓存优化 |
| 下单执行时间 | < 100ms | 异步处理 + 批量操作 |
| 缓存命中率 | > 90% | LRU + TTL 双重策略 |
| 并发支持 | 10+ 策略 | 线程安全设计 |
| 内存占用 | < 50MB | 轻量级设计 |

## API Compatibility

### JoinQuant API兼容性
- 完全兼容现有JQ策略代码
- 支持标准的 `order_shares()`, `get_portfolio()` 等接口
- 零修改迁移现有策略

### 使用示例
```python
# 标准JQ兼容接口
account = get_jq_account("strategy", 100000, "STOCK")
order_id = account.order_shares("000001.SZ", 1000)

# 工厂模式高级用法
handler = AccountHandlerFactory.create_handler("STOCK", "strategy", 0)
```