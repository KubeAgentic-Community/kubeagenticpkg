# Contributing to KubeAgentic

Thank you for your interest in contributing to KubeAgentic! This document provides guidelines and instructions for contributing.

## Code of Conduct

By participating in this project, you agree to maintain a respectful and inclusive environment for all contributors.

## Getting Started

### 1. Fork and Clone

```bash
# Fork the repository on GitHub, then clone your fork
git clone https://github.com/YOUR_USERNAME/kubeagentic.git
cd kubeagentic
```

### 2. Set Up Development Environment

```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install development dependencies
pip install -e ".[dev]"
# Or use requirements-dev.txt
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install
```

### 3. Create a Branch

```bash
git checkout -b feature/your-feature-name
# Or for bug fixes:
git checkout -b fix/bug-description
```

## Development Workflow

### Code Style

We use:
- **Black** for code formatting (line length: 100)
- **Ruff** for linting
- **MyPy** for type checking

Run formatters and linters:

```bash
# Format code
black kubeagentic tests

# Lint code
ruff check kubeagentic tests

# Type check
mypy kubeagentic
```

### Testing

Write tests for all new features and bug fixes.

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=kubeagentic --cov-report=html

# Run specific test file
pytest tests/test_agent.py -v

# Run tests with logging output
pytest -v -s
```

### Writing Tests

- Place tests in the `tests/` directory
- Mirror the structure of `kubeagentic/`
- Use descriptive test names: `test_should_do_something_when_condition()`
- Mock external dependencies (LLMs, databases, etc.)
- Aim for >80% code coverage

Example test structure:

```python
import pytest
from kubeagentic import Agent

def test_agent_creation_from_config():
    """Test that agent can be created from configuration."""
    config = {...}
    agent = Agent.from_dict(config)
    assert agent.name == "test_agent"

@pytest.mark.asyncio
async def test_agent_async_invoke():
    """Test async agent invocation."""
    agent = Agent.from_dict(config)
    response = await agent.ainvoke("Hello")
    assert "content" in response
```

### Documentation

- Add docstrings to all public functions and classes
- Use Google-style docstrings
- Update README.md if adding new features
- Add examples for new functionality

Example docstring:

```python
def parse_config(file_path: str) -> AgentConfig:
    """
    Parse configuration from YAML file.
    
    Args:
        file_path: Path to the YAML configuration file
        
    Returns:
        Parsed and validated agent configuration
        
    Raises:
        ConfigurationError: If file is invalid or cannot be parsed
        
    Example:
        >>> config = parse_config("agent.yaml")
        >>> print(config.agent.name)
        'my_agent'
    """
```

## Pull Request Process

### 1. Before Submitting

- [ ] Code follows style guidelines (Black, Ruff, MyPy pass)
- [ ] Tests are added and passing
- [ ] Documentation is updated
- [ ] Commits are clean and well-described
- [ ] Branch is up to date with main

```bash
# Update your branch
git fetch upstream
git rebase upstream/main
```

### 2. Commit Messages

Follow conventional commits format:

```
feat: add support for Cohere LLM provider
fix: resolve session management bug
docs: update API documentation
test: add tests for config parser
refactor: simplify agent initialization
```

### 3. Submit Pull Request

- Fill out the pull request template
- Link related issues
- Add clear description of changes
- Request review from maintainers

### 4. Code Review

- Address review comments
- Keep discussion respectful and constructive
- Update code as needed
- Once approved, a maintainer will merge

## Project Structure

```
kubeagentic/
├── kubeagentic/          # Main package
│   ├── config/           # Configuration parsing
│   ├── core/             # Core agent implementation
│   ├── llm/              # LLM provider integrations
│   ├── api/              # REST API endpoints
│   ├── utils/            # Utilities
│   └── cli.py            # CLI interface
├── tests/                # Test suite
├── examples/             # Example configurations
├── docs/                 # Documentation
└── scripts/              # Development scripts
```

## Adding New Features

### Adding a New LLM Provider

1. Add provider enum to `kubeagentic/config/schema.py`
2. Implement factory method in `kubeagentic/llm/factory.py`
3. Add tests in `tests/test_llm_factory.py`
4. Update documentation

### Adding a New Tool

1. Create tool class in `kubeagentic/tools/`
2. Register in tool loader
3. Add example configuration
4. Write tests
5. Update documentation

## Release Process

(For maintainers)

1. Update version in `pyproject.toml`
2. Update CHANGELOG.md
3. Create release tag
4. Build and publish to PyPI
5. Create GitHub release

## Getting Help

- 🌐 Website: [https://kubeagentic.com](https://kubeagentic.com)
- 📧 Email: contact@kubeagentic.com
- 🐛 [GitHub Issues](https://github.com/KubeAgentic-Community/kubeagenticpkg/issues)
- 💬 [GitHub Discussions](https://github.com/KubeAgentic-Community/kubeagenticpkg/discussions)

## Recognition

Contributors will be:
- Listed in CONTRIBUTORS.md
- Mentioned in release notes
- Credited in the documentation

Thank you for contributing to KubeAgentic! 🎉 