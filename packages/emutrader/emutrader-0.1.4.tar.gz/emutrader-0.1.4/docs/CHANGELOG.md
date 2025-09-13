# 更新日志

所有重要的项目变更都会记录在此文件中。

本项目遵循 [语义化版本](https://semver.org/lang/zh-CN/) 规范。

## [1.0.0] - 2025-01-12

### 重大架构重构 🚀
- **核心重构**: 从策略框架重构为专业账户管理库
- **职责分离**: EmuTrader专注账户管理，QSM专注策略执行
- **新架构**: StrategyContext → AccountContext，移除策略相关属性
- **QSM集成**: 提供完整的策略系统集成接口

### 新增
- **QSM集成接口**: update_market_price(), batch_update_prices()
- **交易执行接口**: execute_trade()方法处理账户状态更新
- **数据持久化接口**: load_from_db(), save_to_db()方法
- **行情订阅支持**: get_all_securities()获取持仓证券列表
- **EmuTrader主类**: 为QSM提供完整的账户管理接口
- **性能优化**: 内存实时计算 + 定期批量保存

### 变更
- **StrategyContext重命名**: 改为AccountContext，专注账户数据管理
- **EmuTrader重构**: 成为Portfolio和SubPortfolio的提供者
- **API适配**: get_jq_account()返回EmuTrader实例，保持JQ兼容性
- **数据流优化**: DB加载 → 内存实时更新 → 定期保存

### 移除
- **策略相关属性**: 从AccountContext中移除current_dt, run_params
- **陈旧文档**: 清理过时的API_REFERENCE.md, EXAMPLES.md等文档

### 兼容性
- ✅ **100% JQ API兼容**: 现有策略代码无需修改
- ✅ **向后兼容**: 保留所有JQ兼容函数和对象访问方式
- ✅ **扩展性**: 支持多种策略系统接入

## [0.9.0] - 2025-01-11

### 新增
- **JQ兼容API**: get_jq_account(), order_shares(), order_value()等
- **完整账户体系**: Portfolio, Position, SubPortfolio对象
- **子账户管理**: set_subportfolios(), transfer_cash()
- **数据模型**: Order工厂方法，AccountState快照

### 变更
- **项目重新定位**: 专为账户管理设计
- **架构优化**: 核心对象层完整实现

## [0.1.0] - 2024-12

### 新增
- 初始版本发布
- 基础项目结构
- 开发工具链配置

---

## 版本类型说明

- `新增` - 新功能
- `变更` - 对现有功能的变更
- `弃用` - 即将移除的功能
- `移除` - 已移除的功能
- `修复` - Bug 修复
- `安全` - 安全性相关修复