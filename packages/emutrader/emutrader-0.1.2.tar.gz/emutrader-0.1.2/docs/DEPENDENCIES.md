# EmuTrader 依赖说明

## 🎯 项目定位（2025年重构更新）

EmuTrader 是一个**专业的量化交易账户管理库**，专注于：
- ✅ 100% JoinQuant API 兼容
- ✅ 为QSM等策略系统提供账户管理服务
- ✅ 多账户类型支持 (stock 股票账户、futures 期货账户)  
- ✅ 实时盈亏计算和账户状态管理
- ✅ 高性能内存计算 + 数据持久化
- ✅ 轻量级设计，无复杂外部依赖

## 📦 核心依赖（必需）

```
numpy>=1.21.0         # 基础数值计算
pandas>=1.3.0         # 数据结构和处理
pyyaml>=6.0           # 配置文件管理
loguru>=0.6.0         # 日志记录
typing-extensions>=4.0.0  # 类型检查支持
```

**特点**：
- 🚀 快速安装，无编译问题
- 📦 轻量级，总大小 < 20MB
- 🔧 兼容 Python 3.8-3.12
- ⚡ 启动速度快

## 🔧 开发依赖（可选）

```bash
pip install emutrader[dev]
```

包含：
- pytest>=6.0 (测试框架)
- pytest-cov (覆盖率)
- black (代码格式化)
- flake8 (代码检查)
- mypy (类型检查)

## 📊 分析依赖（可选）

```bash
pip install emutrader[analysis]
```

包含：
- matplotlib>=3.5.0 (图表绘制)
- scipy>=1.7.0 (科学计算)

## 💾 数据获取（用户自选）

EmuTrader **不绑定特定数据源**，用户可根据需要单独安装：

### 中国市场数据
```bash
pip install akshare     # A股、期货、基金等
pip install tushare     # 专业金融数据
pip install efinance    # 东方财富数据
```

### 国际市场数据
```bash
pip install yfinance    # Yahoo Finance
pip install alpha_vantage  # Alpha Vantage
pip install quandl     # Quandl数据
```

### 技术指标（可选）
```bash
pip install pandas-ta   # 技术分析指标
pip install talib       # 传统技术分析（需要编译）
```

## 🏗️ 安装示例

### 基础安装（推荐）
```bash
pip install emutrader
```

### 完整开发环境
```bash
pip install emutrader[dev,analysis]
pip install akshare  # 如果需要中国市场数据
```

### 验证安装
```python
from emutrader import get_jq_account

# 创建模拟账户 (账户ID只能使用英文+数字)
context = get_jq_account("test_strategy_001", 100000, "stock")
print(f"账户创建成功: {context.portfolio.total_value}")
```

## ❓ 常见问题

### Q: 为什么不内置数据获取功能？
A: 为了保持轻量级和避免依赖冲突。用户可根据需要选择最适合的数据源。

### Q: 支持哪些Python版本？ 
A: 支持 Python 3.8-3.12，核心依赖都有良好的兼容性。

### Q: 如何获取实时数据？
A: 建议使用 akshare 或 yfinance，然后通过 EmuTrader 的 API 更新价格。

### Q: 是否支持实盘交易？
A: EmuTrader 只提供模拟交易功能，不支持实盘交易。

## 🔄 版本兼容性

| EmuTrader版本 | Python版本 | 核心功能 | 主要特性 |
|-------------|-----------|---------|---------|
| 0.1.2+ | 3.8-3.12 | ✅ | JQ兼容、多账户、轻量级 |
| 0.1.1 | 3.8-3.11 | ✅ | 早期版本 |
| 0.1.0 | 3.8+ | ✅ | 初始版本 |

---

**设计理念**: 专注核心功能，保持简单高效，让用户自由选择扩展组件。