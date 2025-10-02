#!/bin/bash
set -e  # Exit on error

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║     KubeAgentic PyPI Package Builder & Publisher              ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Project details
PROJECT_NAME="kubeagentic"
VERSION="0.2.1"
CREDENTIAL_FILE="requirements/pypi.credential"

# Function to print colored messages
info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
    exit 1
}

# Step 1: Check if credential file exists
info "Checking for PyPI credentials..."
if [ ! -f "$CREDENTIAL_FILE" ]; then
    error "Credential file not found: $CREDENTIAL_FILE"
fi
success "Credential file found"

# Step 2: Read credentials
info "Reading PyPI credentials..."
PYPI_TOKEN=$(grep "password" "$CREDENTIAL_FILE" | awk '{print $3}')

if [ -z "$PYPI_TOKEN" ]; then
    error "Failed to read API token from $CREDENTIAL_FILE"
fi

# For PyPI API tokens, username must be "__token__"
PYPI_USERNAME="__token__"
PYPI_PASSWORD="$PYPI_TOKEN"

success "API token loaded successfully"

# Step 3: Check required tools
info "Checking required tools..."
if ! command -v python3 &> /dev/null; then
    error "python3 is not installed"
fi
success "python3 found: $(python3 --version)"

# Step 4: Install/upgrade build tools
info "Installing/upgrading build tools..."
python3 -m pip install --upgrade pip setuptools wheel twine build > /dev/null 2>&1
success "Build tools ready"

# Step 5: Clean previous builds
info "Cleaning previous builds..."
rm -rf dist/ build/ *.egg-info kubeagentic.egg-info
success "Clean complete"

# Step 6: Build the package
info "Building package: $PROJECT_NAME v$VERSION..."
python3 -m build
if [ $? -ne 0 ]; then
    error "Build failed!"
fi
success "Package built successfully"

# Step 7: List built packages
info "Built packages:"
ls -lh dist/
echo ""

# Step 8: Check package with twine
info "Checking package integrity..."
python3 -m twine check dist/*
if [ $? -ne 0 ]; then
    error "Package check failed!"
fi
success "Package integrity verified"

# Step 9: Ask for confirmation
echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                    READY TO PUBLISH                            ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""
echo "  Package: $PROJECT_NAME"
echo "  Version: $VERSION"
echo "  Target:  PyPI (pypi.org)"
echo "  Auth:    API Token"
echo ""
read -p "Do you want to publish to PyPI? (yes/no): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    warning "Publication cancelled by user"
    exit 0
fi

# Step 10: Publish to PyPI
info "Publishing to PyPI..."
python3 -m twine upload dist/* \
    --username "$PYPI_USERNAME" \
    --password "$PYPI_PASSWORD" \
    --verbose

if [ $? -ne 0 ]; then
    error "Publication failed!"
fi

echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║              🎉 PUBLISHED SUCCESSFULLY! 🎉                     ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""
success "Package $PROJECT_NAME v$VERSION published to PyPI!"
echo ""
echo "Install with:"
echo "  pip install $PROJECT_NAME"
echo ""
echo "Upgrade with:"
echo "  pip install --upgrade $PROJECT_NAME"
echo ""
echo "View on PyPI:"
echo "  https://pypi.org/project/$PROJECT_NAME/"
echo "" 