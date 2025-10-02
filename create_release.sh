#!/bin/bash
set -e

# KubeAgentic Release Script
# Usage: ./create_release.sh <version> [release_notes]

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║        KubeAgentic Release Creation Script                    ║"
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

# Check arguments
if [ -z "$1" ]; then
    error "Usage: ./create_release.sh <version> [release_notes]"
fi

VERSION=$1
RELEASE_NOTES=${2:-"Release v$VERSION"}

# Remove 'v' prefix if present
VERSION_NUM=${VERSION#v}
VERSION_TAG="v$VERSION_NUM"

info "Creating release for version: $VERSION_TAG"

# Step 1: Check for uncommitted changes
if ! git diff-index --quiet HEAD --; then
    warning "You have uncommitted changes!"
    read -p "Continue anyway? (yes/no): " CONTINUE
    if [ "$CONTINUE" != "yes" ]; then
        error "Aborted by user"
    fi
fi

# Step 2: Update version in files
info "Updating version numbers..."

# Update pyproject.toml
sed -i.bak "s/^version = .*/version = \"$VERSION_NUM\"/" pyproject.toml
rm -f pyproject.toml.bak

# Update __init__.py
sed -i.bak "s/^__version__ = .*/__version__ = \"$VERSION_NUM\"/" kubeagentic/__init__.py
rm -f kubeagentic/__init__.py.bak

# Update publish_to_pypi.sh
sed -i.bak "s/^VERSION=.*/VERSION=\"$VERSION_NUM\"/" publish_to_pypi.sh
rm -f publish_to_pypi.sh.bak

success "Version numbers updated to $VERSION_NUM"

# Step 3: Build and test
info "Building and testing package..."
./build_and_test.sh
if [ $? -ne 0 ]; then
    error "Build and test failed!"
fi
success "Build and test passed"

# Step 4: Commit changes
info "Committing version changes..."
git add pyproject.toml kubeagentic/__init__.py publish_to_pypi.sh
git commit -m "chore: Bump version to $VERSION_NUM"
success "Changes committed"

# Step 5: Create and push tag
info "Creating git tag: $VERSION_TAG"
git tag -a "$VERSION_TAG" -m "Release $VERSION_TAG"
success "Tag created"

# Step 6: Push everything
info "Pushing to GitHub..."
git push origin main
git push origin "$VERSION_TAG"
success "Pushed to GitHub"

# Step 7: Publish to PyPI
info "Publishing to PyPI..."
./publish_to_pypi.sh
success "Published to PyPI"

# Step 8: Create GitHub Release
info "Creating GitHub Release..."
gh release create "$VERSION_TAG" \
    --title "$VERSION_TAG" \
    --notes "$RELEASE_NOTES" \
    --latest \
    dist/kubeagentic-${VERSION_NUM}-py3-none-any.whl \
    dist/kubeagentic-${VERSION_NUM}.tar.gz

success "GitHub Release created"

echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║              ✅ RELEASE COMPLETE! ✅                          ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""
success "Release $VERSION_TAG completed successfully!"
echo ""
echo "🔗 Quick Links:"
echo "   • Release: https://github.com/KubeAgentic-Community/kubeagenticpkg/releases/tag/$VERSION_TAG"
echo "   • PyPI: https://pypi.org/project/kubeagentic/$VERSION_NUM/"
echo ""
echo "📦 Users can install with:"
echo "   pip install kubeagentic==$VERSION_NUM"
echo "" 