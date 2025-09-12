# EmuTrader 测试套件使用指南

## 📋 测试文件结构

```
tests/
├── README.md                     # 本文件 - 测试使用指南
├── __init__.py                   # 测试包初始化
├── conftest.py                   # pytest配置和共享fixtures
├── 
├── # === 新架构JQ兼容测试 ===
├── test_jq_compatibility.py      # JQ API 100%兼容性测试
├── test_strategy_context.py      # StrategyContext核心功能测试
├── test_portfolio.py             # Portfolio投资组合测试  
├── test_trading_api.py           # 全局交易API测试
├── test_subportfolio.py          # 子账户系统测试
├── test_basic.py                 # 基础导入和API可用性测试
├── test_integration_new.py       # 新架构完整集成测试
├──
├── # === 旧架构测试（向后兼容） ===
├── test_integration.py           # 旧架构集成测试
├── core/
│   └── test_models.py            # 旧数据模型测试
├── handlers/  
│   └── test_stock.py             # 旧StockHandler测试
├── adapters/
│   └── test_mock_adapter.py      # Mock适配器测试
└── storage/
    ├── test_cache.py             # 缓存系统测试
    └── test_sqlite.py            # SQLite存储测试
```

## 🚀 快速开始

### 安装测试依赖
```bash
pip install pytest pytest-cov
```

### 运行所有测试
```bash
# 基本运行
pytest

# 详细输出
pytest -v

# 显示测试进度
pytest -v --tb=short
```

## 🎯 按类别运行测试

### 1. JQ兼容性测试
```bash
# 运行所有JQ兼容性测试
pytest -m jq_compatibility -v

# 快速验证JQ API可用性
pytest tests/test_jq_compatibility.py::TestJQCompatibility::test_get_jq_account_basic -v
```

### 2. 核心组件测试
```bash
# Context测试
pytest tests/test_strategy_context.py -v

# Portfolio测试  
pytest tests/test_portfolio.py -v

# 交易API测试
pytest tests/test_trading_api.py -v

# 子账户测试
pytest tests/test_subportfolio.py -v
```

### 3. 集成测试
```bash
# 新架构完整集成测试
pytest tests/test_integration_new.py -v

# 基础功能集成
pytest tests/test_basic.py -v
```

## 📊 测试标记 (Markers)

### 使用pytest标记运行特定测试

```bash
# JQ兼容性测试
pytest -m jq_compatibility

# 核心Context测试
pytest -m context

# Portfolio相关测试
pytest -m portfolio

# 交易API测试
pytest -m trading_api

# 子账户测试
pytest -m subportfolio

# 集成测试
pytest -m integration

# 性能测试
pytest -m performance
```

### 排除特定测试
```bash
# 排除性能测试
pytest -m "not performance"

# 只运行快速测试（排除集成和性能）
pytest -m "not integration and not performance"
```

## 🔍 详细测试场景

### 1. 开发阶段测试
```bash
# 快速验证基本功能
pytest tests/test_basic.py -v

# 验证JQ兼容性
pytest tests/test_jq_compatibility.py::TestJQCompatibility -v

# 验证核心功能
pytest tests/test_strategy_context.py tests/test_portfolio.py -v
```

### 2. 功能验证测试
```bash
# 验证交易功能
pytest tests/test_trading_api.py -v

# 验证子账户功能
pytest tests/test_subportfolio.py -v

# 端到端工作流程
pytest tests/test_integration_new.py::TestCompleteWorkflow -v
```

### 3. 性能和压力测试
```bash
# 性能测试
pytest -m performance -v

# 压力测试
pytest tests/test_integration_new.py::TestStressTest -v

# 并发测试
pytest tests/test_trading_api.py::TestTradingAPIPerformance -v
```

## 📈 测试覆盖率

### 生成覆盖率报告
```bash
# 生成HTML覆盖率报告
pytest --cov=emutrader --cov-report=html

# 生成终端覆盖率报告
pytest --cov=emutrader --cov-report=term-missing

# 只针对核心模块
pytest --cov=emutrader.core --cov=emutrader.api --cov-report=html
```

### 查看覆盖率报告
```bash
# 在浏览器中打开HTML报告
start htmlcov/index.html  # Windows
open htmlcov/index.html   # macOS
```

## 🐛 调试测试

### 详细错误信息
```bash
# 显示完整错误堆栈
pytest tests/test_jq_compatibility.py -v --tb=long

# 在第一个失败时停止
pytest tests/test_portfolio.py -x -v

# 显示本地变量
pytest tests/test_trading_api.py -v -l
```

### 调试特定测试
```bash
# 运行单个测试方法
pytest tests/test_strategy_context.py::TestStrategyContextCreation::test_context_creation_via_get_jq_account -v -s

# 带输出的运行（不捕获print）
pytest tests/test_integration_new.py -v -s
```

## ⚡ 并行测试

### 安装并行运行插件
```bash
pip install pytest-xdist
```

### 并行运行测试
```bash
# 使用4个进程并行运行
pytest -n 4

# 自动检测CPU数量
pytest -n auto

# 只对某些测试并行运行
pytest tests/test_jq_compatibility.py tests/test_portfolio.py -n 2
```

## 📋 测试配置

### pytest.ini 配置示例
```ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*

markers =
    jq_compatibility: JoinQuant API compatibility tests
    context: StrategyContext related tests
    portfolio: Portfolio related tests
    trading_api: Trading API tests
    subportfolio: SubPortfolio system tests
    integration: Integration tests
    performance: Performance tests
    slow: Slow running tests

addopts = 
    --strict-markers
    --disable-warnings
    -ra
```

## 🎯 测试最佳实践

### 1. 测试命名规范
- 测试文件: `test_*.py`
- 测试类: `Test*`
- 测试方法: `test_*`

### 2. 运行测试前检查
```bash
# 确保所有导入正常
python -c "import emutrader; print('Import OK')"

# 验证基础API
python -c "from emutrader import get_jq_account; print('JQ API OK')"
```

### 3. 常见测试命令
```bash
# 日常开发
pytest tests/test_basic.py -v                    # 快速验证
pytest tests/test_jq_compatibility.py -v        # JQ兼容性
pytest -m "not performance" -v                  # 非性能测试

# 功能验证
pytest tests/test_integration_new.py -v         # 完整工作流程
pytest -m integration -v                        # 所有集成测试

# 发布前验证
pytest --cov=emutrader --cov-report=term       # 完整覆盖率测试
pytest -m performance                           # 性能基准测试
```

## 🚨 故障排除

### 常见问题

1. **导入错误**
   ```bash
   # 检查PYTHONPATH
   export PYTHONPATH=$PWD:$PYTHONPATH
   
   # 或安装开发模式
   pip install -e .
   ```

2. **测试发现问题**
   ```bash
   # 显示测试发现过程
   pytest --collect-only
   ```

3. **依赖问题**
   ```bash
   # 检查测试依赖
   pip install -r requirements.txt
   pip install pytest pytest-cov
   ```

### 获取帮助
```bash
# 查看所有pytest选项
pytest --help

# 查看可用的markers
pytest --markers

# 查看fixtures
pytest --fixtures
```

## 📞 支持

如果遇到测试相关问题：

1. **查看测试输出**: 使用 `-v` 参数获取详细信息
2. **检查依赖**: 确保所有必要包已安装
3. **查看日志**: 使用 `-s` 参数查看print输出
4. **单独运行**: 先运行单个测试文件定位问题

---

**快速验证EmuTrader功能是否正常:**
```bash
pytest tests/test_basic.py::test_jq_compatibility_quick_test -v
```

这个命令会快速验证JQ API的基本功能是否可用。✅