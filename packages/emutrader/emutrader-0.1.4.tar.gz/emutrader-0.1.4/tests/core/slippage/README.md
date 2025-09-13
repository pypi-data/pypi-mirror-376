# 滑点功能测试目录

本目录包含EmuTrader滑点功能的完整测试套件。

## 测试文件说明

### 核心测试文件

1. **test_slippage_core.py** - 核心滑点类测试
   - 测试三种滑点类型的基本功能
   - 测试SlippageManager的配置管理
   - 测试滑点计算逻辑和优先级
   - 测试错误处理和边界情况

2. **test_slippage_integration.py** - 集成测试
   - 测试滑点与EmuTrader主类的集成
   - 测试交易执行中的滑点应用
   - 测试多账户和多证券类型场景
   - 测试配置持久化和清除功能

3. **test_jq_compatibility.py** - JoinQuant兼容性测试
   - 验证100%兼容JoinQuant API规范
   - 测试JQ风格的错误处理
   - 测试向后兼容性
   - 测试JQ文档中的使用示例

4. **test_runner.py** - 测试运行器
   - 提供便捷的测试运行接口
   - 支持分类测试和快速验证

## 测试覆盖范围

### 功能测试
- ✅ FixedSlippage (固定值滑点)
- ✅ PriceRelatedSlippage (百分比滑点)  
- ✅ StepRelatedSlippage (跳数滑点)
- ✅ SlippageManager (滑点管理器)
- ✅ 优先级系统 (具体标的 > 类型 > 全局)
- ✅ 货币基金零滑点强制执行

### 集成测试
- ✅ EmuTrader主类集成
- ✅ 交易执行滑点应用
- ✅ 多子账户支持
- ✅ 配置持久化
- ✅ 清除和重置功能

### 兼容性测试
- ✅ JoinQuant API 100%兼容
- ✅ JQ错误处理风格
- ✅ 向后兼容性
- ✅ JQ文档示例验证

### 边界情况测试
- ✅ 极值处理 (极大/极小价格和数量)
- ✅ 零值和负值验证
- ✅ 无效参数处理
- ✅ 内存和性能边界

## 运行测试

### 运行所有测试
```bash
cd tests/core/slippage
python test_runner.py
```

### 运行特定类别测试
```bash
# 核心功能测试
python test_runner.py core

# 集成测试  
python test_runner.py integration

# 兼容性测试
python test_runner.py compatibility
```

### 快速验证
```bash
python test_runner.py quick
```

### 直接使用pytest
```bash
# 运行单个测试文件
pytest test_slippage_core.py -v

# 运行所有测试
pytest . -v

# 运行特定测试类
pytest test_slippage_core.py::TestFixedSlippage -v

# 运行特定测试方法
pytest test_slippage_core.py::TestFixedSlippage::test_creation_valid -v
```

## 测试环境要求

- Python 3.8+
- pytest
- emutrader包已安装

## 测试数据

测试使用模拟数据和场景，无需外部数据源。测试包括：
- 模拟股票交易 (000001.SZ, 000002.SZ)
- 模拟期货交易 (IF2312, CU)  
- 模拟货币基金 (511880.SH)
- 各种价格和数量组合

## 预期结果

所有测试应该通过 (exit code 0)。任何测试失败都表示：
1. 代码实现有问题
2. 测试环境配置问题
3. 依赖项问题

## 故障排除

如果测试失败：

1. **检查导入错误**: 确保emutrader包正确安装
2. **检查Python版本**: 需要Python 3.8+
3. **检查依赖**: 确保pytest已安装
4. **检查路径**: 确保在正确的目录中运行测试
5. **查看详细日志**: 使用`pytest -v --tb=long`获取更多信息

## 贡献指南

添加新测试时请遵循：
1. 每个测试函数应该测试一个具体功能
2. 使用清晰的测试函数和变量命名
3. 包含适当的断言和边界情况
4. 添加必要的文档字符串
5. 确保测试独立运行，不依赖执行顺序