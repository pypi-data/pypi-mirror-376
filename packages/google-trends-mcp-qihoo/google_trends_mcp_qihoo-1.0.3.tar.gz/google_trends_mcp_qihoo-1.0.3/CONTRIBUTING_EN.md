# Contributing Guide

[English](#english) | [中文](CONTRIBUTING.md)

## English

Thank you for your interest in contributing to Google Trends MCP Server! We welcome all forms of contributions.

## 🤝 How to Contribute

### Reporting Issues
- Use [GitHub Issues](https://github.com/qihoo/google-trends-mcp-server/issues) to report bugs
- Provide clear problem descriptions and reproduction steps
- Include relevant error messages and environment details

### Feature Requests
- Propose new features in Issues
- Describe the purpose and expected behavior in detail
- Consider backward compatibility

### Code Contributions

#### Development Environment Setup
```bash
# 1. Fork and clone the repository
git clone https://github.com/yourusername/google-trends-mcp-server.git
cd google-trends-mcp-server

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install development dependencies
pip install -e .
pip install pytest black isort mypy

# 4. Run tests
python -m pytest tests/

# 5. Check code formatting
black google_trends_mcp/
isort google_trends_mcp/
mypy google_trends_mcp/
```

#### Pull Request Process
1. Create feature branch: `git checkout -b feature/your-feature-name`
2. Make changes and add tests
3. Ensure all tests pass
4. Commit changes: `git commit -m "Add: your feature description"`
5. Push branch: `git push origin feature/your-feature-name`
6. Create Pull Request

## 📝 Code Standards

### Python Code Style
- Use [Black](https://black.readthedocs.io/) for code formatting
- Use [isort](https://pycqa.github.io/isort/) to organize imports
- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) guidelines
- Add type annotations (use [mypy](http://mypy-lang.org/))

### Commit Message Format
```
Type: Brief description

Detailed description (optional)

- Related issue: #123
- Breaking changes: description (if any)
```

Type examples:
- `Add`: New feature
- `Fix`: Bug fix
- `Update`: Update existing feature
- `Remove`: Remove feature
- `Docs`: Documentation update

### Testing Requirements
- Add tests for new features
- Ensure test coverage doesn't decrease
- Tests should be fast and reliable
- Use descriptive test names

## 🏗️ Project Structure

```
google-trends-mcp-server/
├── google_trends_mcp/          # Main code
│   ├── __init__.py
│   └── server.py              # MCP server implementation
├── tests/                     # Test files
│   ├── __init__.py
│   ├── test_server.py
│   └── test_integration.py
├── examples/                  # Usage examples
│   ├── basic_usage.py
│   └── claude_config.json
├── docs/                      # Documentation
├── .github/                   # GitHub workflows
│   └── workflows/
│       └── ci.yml
├── pyproject.toml            # Project configuration
├── README.md                 # Project description
├── CONTRIBUTING.md           # Contribution guide
├── LICENSE                   # License
└── CHANGELOG.md              # Change log
```

## 🔄 Release Process

1. Update version number (`pyproject.toml`)
2. Update `CHANGELOG.md`
3. Create git tag: `git tag v1.x.x`
4. Push tag: `git push origin v1.x.x`
5. GitHub Actions automatically builds and publishes to PyPI

## 📋 Development Checklist

Before submitting PR, ensure:

- [ ] Code passes all tests
- [ ] Code formatting complies with standards (black, isort)
- [ ] Type checking passes (mypy)
- [ ] Added necessary tests
- [ ] Updated relevant documentation
- [ ] Commit messages are clear and descriptive

## ❓ Need Help?

- Check [Issues](https://github.com/qihoo/google-trends-mcp-server/issues) for beginner-friendly tasks
- Ask questions in Issues
- Review existing Pull Requests to understand contribution patterns

Thank you for your contribution! 🎉
