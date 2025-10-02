#!/bin/bash
set -e

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║     KubeAgentic Package Build & Test Script (v0.2.2)         ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

info() { echo -e "${BLUE}[INFO]${NC} $1"; }
success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }

# Step 1: Verify package structure
info "Verifying package structure..."
REQUIRED_MODULES=(
    "api"
    "config"
    "core"
    "llm"
    "middleware"
    "session"
    "tools"
    "utils"
)

for module in "${REQUIRED_MODULES[@]}"; do
    if [ ! -f "kubeagentic/$module/__init__.py" ]; then
        error "Missing: kubeagentic/$module/__init__.py"
    fi
done
success "All required modules have __init__.py files"

# Step 2: Clean previous builds
info "Cleaning previous builds..."
rm -rf dist/ build/ *.egg-info kubeagentic.egg-info
success "Clean complete"

# Step 3: Build package
info "Building package..."
python3 -m build
if [ $? -ne 0 ]; then
    error "Build failed!"
fi
success "Package built successfully"

# Step 4: Check with twine
info "Checking package with twine..."
python3 -m twine check dist/*
if [ $? -ne 0 ]; then
    error "Package check failed!"
fi
success "Package integrity verified"

# Step 5: Inspect wheel contents
info "Inspecting wheel contents..."
echo ""
unzip -l dist/kubeagentic-0.2.2-py3-none-any.whl | grep "kubeagentic/" | head -30
echo ""

# Step 6: Count submodules
MODULE_COUNT=$(unzip -l dist/kubeagentic-0.2.2-py3-none-any.whl | grep -c "kubeagentic/.*/__init__.py" || true)
info "Found $MODULE_COUNT submodules in package"

if [ $MODULE_COUNT -lt 8 ]; then
    error "Expected at least 8 submodules, found $MODULE_COUNT"
fi
success "All submodules included (found $MODULE_COUNT)"

# Step 7: Test in clean environment
info "Testing in clean virtual environment..."
rm -rf test_venv
python3 -m venv test_venv
source test_venv/bin/activate

info "Installing package from wheel..."
pip install -q dist/kubeagentic-0.2.2-py3-none-any.whl

info "Testing imports..."
python3 << 'EOF'
import sys
try:
    import kubeagentic
    print(f"✓ kubeagentic version: {kubeagentic.__version__}")
    
    from kubeagentic.core import Agent, AgentConfig
    print("✓ kubeagentic.core imports successful")
    
    from kubeagentic.config import ConfigParser, ConfigValidator
    print("✓ kubeagentic.config imports successful")
    
    from kubeagentic.llm.factory import LLMFactory
    print("✓ kubeagentic.llm imports successful")
    
    from kubeagentic.api.app import create_app
    print("✓ kubeagentic.api imports successful")
    
    from kubeagentic.tools.executor import ToolExecutor
    print("✓ kubeagentic.tools imports successful")
    
    from kubeagentic.session.manager import SessionManager
    print("✓ kubeagentic.session imports successful")
    
    from kubeagentic.middleware.rate_limit import RateLimiter
    print("✓ kubeagentic.middleware imports successful")
    
    from kubeagentic.utils.logging import setup_logging
    print("✓ kubeagentic.utils imports successful")
    
    print("\n✅ All imports successful!")
    
except ImportError as e:
    print(f"\n❌ Import failed: {e}")
    sys.exit(1)
EOF

if [ $? -ne 0 ]; then
    deactivate
    error "Import tests failed!"
fi

success "All import tests passed!"

# Step 8: Test CLI
info "Testing CLI..."
kubeagentic --version
if [ $? -ne 0 ]; then
    deactivate
    error "CLI test failed!"
fi
success "CLI test passed!"

# Cleanup
deactivate
rm -rf test_venv

echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║              ✅ ALL TESTS PASSED! ✅                          ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""
success "Package v0.2.2 is ready for PyPI upload!"
echo ""
echo "📦 Package Details:"
echo "   • Version: 0.2.2"
echo "   • Wheel: $(ls -lh dist/*.whl | awk '{print $9, $5}')"
echo "   • Source: $(ls -lh dist/*.tar.gz | awk '{print $9, $5}')"
echo "   • Submodules: $MODULE_COUNT"
echo ""
echo "🚀 Next Steps:"
echo "   1. Review the package contents above"
echo "   2. (Optional) Upload to TestPyPI:"
echo "      twine upload --repository testpypi dist/*"
echo "   3. Upload to PyPI:"
echo "      ./publish_to_pypi.sh"
echo "" 