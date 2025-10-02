# Release v0.2.2 - Critical Package Fix 🚨

## ⚠️ CRITICAL FIX - v0.2.1 was Non-Functional

**If you installed v0.2.1, please upgrade immediately:**
```bash
pip install --upgrade kubeagentic
```

## 🐛 What Was Broken in v0.2.1

- ❌ **Only 3 files packaged** (out of 28 required files)
- ❌ **All submodules missing** (api, config, core, llm, middleware, session, tools, utils)
- ❌ **Package completely non-functional** - All imports failed with `ModuleNotFoundError`
- ❌ **Unable to create agents or use any features**

## ✅ What's Fixed in v0.2.2

- ✅ **All 28 files now included** in the package
- ✅ **All 8 submodules packaged correctly**
- ✅ **All imports working** as expected
- ✅ **Package fully functional** - Tested on PyPI
- ✅ **Added regression test script** (`build_and_test.sh`)

## 🔧 Technical Details

**Root Cause:** Incorrect setuptools configuration in `pyproject.toml`

**Before (Broken):**
```toml
[tool.setuptools]
packages = ["kubeagentic"]  # Only top-level package
```

**After (Fixed):**
```toml
[tool.setuptools.packages.find]
where = ["."]
include = ["kubeagentic*"]  # Auto-discovers all subpackages
exclude = ["tests*", "docs*", "*.egg-info"]
```

## 📦 Installation

### Fresh Install
```bash
pip install kubeagentic
```

### Upgrade from v0.2.1
```bash
pip install --upgrade kubeagentic
```

### Verify Installation
```python
import kubeagentic
print(kubeagentic.__version__)  # Should print: 0.2.2

# Test imports
from kubeagentic.core import Agent, AgentConfig
from kubeagentic.config import ConfigParser
from kubeagentic.llm.factory import LLMFactory
from kubeagentic.api.app import create_app
# All should work without errors!
```

## 📊 Package Comparison

| Metric | v0.2.1 (Broken) | v0.2.2 (Fixed) |
|--------|-----------------|----------------|
| Files Packaged | 3 | 28 |
| Submodules | 0 | 8 |
| Functional | ❌ | ✅ |
| All Imports Work | ❌ | ✅ |

## 🎯 What's Included

All submodules now available:
- ✅ `kubeagentic.api` - REST API server (5 files)
- ✅ `kubeagentic.config` - Configuration parsing (4 files)
- ✅ `kubeagentic.core` - Agent implementation (3 files)
- ✅ `kubeagentic.llm` - LLM providers (3 files)
- ✅ `kubeagentic.middleware` - API middleware (2 files)
- ✅ `kubeagentic.session` - Session management (3 files)
- ✅ `kubeagentic.tools` - Tool execution (3 files)
- ✅ `kubeagentic.utils` - Utilities (2 files)

## 🚀 Quick Start

```python
from kubeagentic.core import Agent
from kubeagentic.config import ConfigParser

# Parse YAML configuration
config = ConfigParser.parse_file("agent.yaml")

# Create and use agent
agent = Agent(config)
response = agent.invoke("Hello!")
print(response)
```

## 🔗 Links

- 📦 **PyPI Package:** https://pypi.org/project/kubeagentic/0.2.2/
- 📚 **Documentation:** https://kubeagentic.com/guides
- 🌐 **Website:** https://kubeagentic.com
- 🐛 **Issues:** https://github.com/KubeAgentic-Community/kubeagenticpkg/issues
- 💬 **Discussions:** https://github.com/KubeAgentic-Community/kubeagenticpkg/discussions

## 📝 Full Changelog

**Fixed:**
- 🐛 Package now includes all submodules (api, config, core, llm, middleware, session, tools, utils)
- 🐛 Fixed `pyproject.toml` to use `packages.find` for auto-discovery

**Added:**
- ✨ `build_and_test.sh` - Comprehensive test script to verify package integrity
- ✨ Test verification in clean virtual environment

**Changed:**
- 🔧 Updated `.gitignore` to exclude `test_venv/`
- 🔧 Version bumped from 0.2.1 to 0.2.2

## 👥 Contributors

- KubeAgentic Team

## 🙏 Thank You

Thank you for your patience during this critical fix. We've added comprehensive testing to prevent similar issues in the future.

---

**Full Commit:** https://github.com/KubeAgentic-Community/kubeagenticpkg/commit/afa0257 