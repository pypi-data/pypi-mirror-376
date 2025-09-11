# 贡献指南

[English](CONTRIBUTING_EN.md) | [中文](#中文)

## 中文

感谢您对 Google Trends MCP Server 的关注！我们欢迎各种形式的贡献。

## 🤝 如何贡献

### 报告问题
- 使用 [GitHub Issues](https://github.com/qihoo/google-trends-mcp-server/issues) 报告 bug
- 提供清晰的问题描述和复现步骤
- 包含相关的错误信息和环境详情

### 功能建议
- 在 Issues 中提出新功能建议
- 详细描述功能的用途和预期行为
- 考虑向后兼容性

### 代码贡献

#### 开发环境设置
```bash
# 1. Fork 并克隆仓库
git clone https://github.com/yourusername/google-trends-mcp-server.git
cd google-trends-mcp-server

# 2. 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. 安装开发依赖
pip install -e .
pip install pytest black isort mypy

# 4. 运行测试
python -m pytest tests/

# 5. 检查代码格式
black google_trends_mcp/
isort google_trends_mcp/
mypy google_trends_mcp/
```

#### Pull Request 流程
1. 创建功能分支：`git checkout -b feature/your-feature-name`
2. 进行更改并添加测试
3. 确保所有测试通过
4. 提交更改：`git commit -m "Add: your feature description"`
5. 推送分支：`git push origin feature/your-feature-name`
6. 创建 Pull Request

## 📝 代码规范

### Python 代码风格
- 使用 [Black](https://black.readthedocs.io/) 进行代码格式化
- 使用 [isort](https://pycqa.github.io/isort/) 整理导入
- 遵循 [PEP 8](https://www.python.org/dev/peps/pep-0008/) 规范
- 添加类型注解（使用 [mypy](http://mypy-lang.org/)）

### 提交信息格式
```
类型: 简短描述

详细描述（可选）

- 相关 issue: #123
- 破坏性变更: 描述（如有）
```

类型示例：
- `Add`: 新功能
- `Fix`: 修复 bug
- `Update`: 更新现有功能
- `Remove`: 删除功能
- `Docs`: 文档更新

### 测试要求
- 为新功能添加测试
- 确保测试覆盖率不低于现有水平
- 测试应该快速且可靠
- 使用描述性的测试名称

## 🏗️ 项目结构

```
google-trends-mcp-server/
├── google_trends_mcp/          # 主要代码
│   ├── __init__.py
│   └── server.py              # MCP 服务器实现
├── tests/                     # 测试文件
│   ├── __init__.py
│   ├── test_server.py
│   └── test_integration.py
├── examples/                  # 使用示例
│   ├── basic_usage.py
│   └── claude_config.json
├── docs/                      # 文档
├── .github/                   # GitHub 工作流
│   └── workflows/
│       └── ci.yml
├── pyproject.toml            # 项目配置
├── README.md                 # 项目说明
├── CONTRIBUTING.md           # 贡献指南
├── LICENSE                   # 许可证
└── CHANGELOG.md              # 变更日志
```

## 🔄 发布流程

1. 更新版本号（`pyproject.toml`）
2. 更新 `CHANGELOG.md`
3. 创建 git tag：`git tag v1.x.x`
4. 推送 tag：`git push origin v1.x.x`
5. GitHub Actions 自动构建并发布到 PyPI

## 📋 开发检查清单

在提交 PR 之前，请确保：

- [ ] 代码通过所有测试
- [ ] 代码格式符合规范（black, isort）
- [ ] 类型检查通过（mypy）
- [ ] 添加了必要的测试
- [ ] 更新了相关文档
- [ ] 提交信息清晰明确

## ❓ 需要帮助？

- 查看 [Issues](https://github.com/qihoo/google-trends-mcp-server/issues) 寻找适合新手的任务
- 在 Issues 中提问
- 查看现有的 Pull Requests 了解贡献模式

感谢您的贡献！🎉
