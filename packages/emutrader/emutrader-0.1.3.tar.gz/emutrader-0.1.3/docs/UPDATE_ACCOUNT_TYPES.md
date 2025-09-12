# 账户类型更新说明

## 🔄 聚宽API兼容更新

为了100%兼容聚宽API，所有账户类型已更新为聚宽标准格式：

### ✅ 新的账户类型（小写格式）

| 类型 | 说明 | 支持状态 |
|------|------|----------|
| `stock` | 股票、场内基金、场内交易的货币基金 | ✅ 已实现 |
| `futures` | 期货 | ✅ 已实现 |

### 🔄 向后兼容

为保持向后兼容，系统仍然支持旧的大写格式：

```python
# 旧格式（仍然支持）
context = get_jq_account("策略", 100000, "STOCK")

# 新格式（推荐）  
context = get_jq_account("策略", 100000, "stock")

# 自动映射
"STOCK" -> "stock"
"FUTURE" -> "futures" 
"CREDIT" -> "stock"  # 融资融券归类为股票账户
"INDEX_FUTURE" -> "index_futures"
```

### 📝 使用示例

```python
from emutrader import get_jq_account, set_subportfolios, SubPortfolioConfig

# 创建不同类型的账户
stock_context = get_jq_account("股票策略", 100000, "stock")
futures_context = get_jq_account("期货策略", 100000, "futures")
index_futures_context = get_jq_account("金融期货", 100000, "index_futures")

# 设置多账户
configs = [
    SubPortfolioConfig(cash=300000, type='stock'),
    SubPortfolioConfig(cash=200000, type='futures'), 
    SubPortfolioConfig(cash=100000, type='index_futures')
]
set_subportfolios(configs)
```

### 🔍 验证账户类型

```python
from emutrader.constants import AccountTypes

# 检查所有支持的类型
print("支持的账户类型:", AccountTypes.ALL)
print("已实现的类型:", AccountTypes.IMPLEMENTED)
print("开发中的类型:", AccountTypes.IN_DEVELOPMENT)

# 兼容性映射
print("兼容映射:", AccountTypes.LEGACY_MAPPING)
```

### ⚠️ 重要变更

1. **默认类型变更**: 默认账户类型从 `"STOCK"` 变更为 `"stock"`
2. **函数参数**: 所有接受账户类型的函数现在优先使用小写格式
3. **配置文件**: 配置文件中的账户类型应更新为小写格式
4. **测试用例**: 测试用例已全部更新为新格式

### 📚 更新的文件

以下文件已更新到新的账户类型格式：
- `emutrader/constants.py` - 核心常量定义
- `README.md` - 主文档
- `CLAUDE.md` - 开发指南  
- `docs/API_REFERENCE.md` - API参考
- `docs/EXAMPLES.md` - 使用示例
- 所有测试文件 (`tests/*.py`)

### 🚀 升级指南

如果您正在使用 EmuTrader v0.1.1 或更早版本：

1. **推荐更新**: 将代码中的账户类型更新为小写格式
2. **无需立即更新**: 旧格式仍然支持，不会破坏现有代码
3. **渐进式升级**: 可以逐步将项目迁移到新格式

---

此更新确保了 EmuTrader 与聚宽API的100%兼容性！ 🎉