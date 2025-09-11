# 贡献指南

欢迎为 EmuTrader 项目做出贡献！本文档提供了参与项目开发的指导。

## 开发环境设置

### 1. 克隆仓库
```bash
git clone https://github.com/yourusername/EmuTrader.git
cd EmuTrader
```

### 2. 创建虚拟环境
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows
```

### 3. 安装开发依赖
```bash
make install-dev
# 或
pip install -e ".[dev]"
pre-commit install
```

## 开发流程

### 代码规范
- 使用 Black 进行代码格式化
- 遵循 PEP 8 代码风格
- 启用类型注释（mypy）
- 编写详细的文档字符串

### 质量检查
```bash
make quality  # 运行所有质量检查
```

或单独运行：
```bash
make format     # 代码格式化
make lint       # 代码检查
make type-check # 类型检查
make test-cov   # 测试和覆盖率
```

### 测试要求
- 新功能必须包含测试
- 测试覆盖率应 > 80%
- 所有测试必须通过

### 提交流程
1. 创建功能分支：`git checkout -b feature/your-feature`
2. 进行开发和测试
3. 运行质量检查：`make quality`
4. 提交代码：`git commit -m "feat: add your feature"`
5. 推送分支：`git push origin feature/your-feature`
6. 创建 Pull Request

## 架构指导

### 模块设计原则
- **用户接口层**: JoinQuant API 兼容性
- **处理器层**: 业务逻辑封装
- **适配器层**: 平台集成抽象
- **存储层**: 数据持久化

### 性能目标
- 查询响应时间 < 10ms
- 缓存命中率 > 90%
- 支持 10+ 并发策略

## 问题报告

使用 GitHub Issues 报告 bug 或请求功能：
- 提供详细的复现步骤
- 包含环境信息
- 附上相关日志或错误信息

## 许可证

通过贡献代码，您同意您的贡献将在 MIT 许可证下发布。