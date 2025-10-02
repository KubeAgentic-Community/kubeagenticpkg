# Release Process Documentation

This document describes how to create new releases for the KubeAgentic package.

## 📦 Release Checklist

- [ ] All tests passing
- [ ] Documentation updated
- [ ] CHANGELOG.md updated (if exists)
- [ ] Version numbers ready to bump
- [ ] PyPI credentials configured

## 🚀 Method 1: Automated Release Script (Recommended)

The `create_release.sh` script automates the entire release process.

### Usage

```bash
./create_release.sh <version> ["Release notes"]
```

### Examples

```bash
# Simple release
./create_release.sh 0.2.3

# With custom release notes
./create_release.sh 0.2.3 "Bug fixes and performance improvements"

# Works with or without 'v' prefix
./create_release.sh v0.2.3
```

### What It Does

1. ✅ Updates version in:
   - `pyproject.toml`
   - `kubeagentic/__init__.py`
   - `publish_to_pypi.sh`

2. ✅ Builds and tests the package
3. ✅ Commits version changes
4. ✅ Creates and pushes git tag
5. ✅ Publishes to PyPI
6. ✅ Creates GitHub Release with assets

## 🔧 Method 2: Manual Release

If you prefer to do it step by step:

### Step 1: Update Version Numbers

Edit these files:

**`pyproject.toml`:**
```toml
[project]
version = "0.2.3"
```

**`kubeagentic/__init__.py`:**
```python
__version__ = "0.2.3"
```

**`publish_to_pypi.sh`:**
```bash
VERSION="0.2.3"
```

### Step 2: Test the Build

```bash
./build_and_test.sh
```

### Step 3: Commit Changes

```bash
git add pyproject.toml kubeagentic/__init__.py publish_to_pypi.sh
git commit -m "chore: Bump version to 0.2.3"
git push origin main
```

### Step 4: Create and Push Tag

```bash
git tag -a v0.2.3 -m "Release v0.2.3 - Description"
git push origin v0.2.3
```

### Step 5: Publish to PyPI

```bash
./publish_to_pypi.sh
```

### Step 6: Create GitHub Release

```bash
gh release create v0.2.3 \
  --title "v0.2.3 - Title" \
  --notes "Release notes here" \
  --latest \
  dist/kubeagentic-0.2.3-py3-none-any.whl \
  dist/kubeagentic-0.2.3.tar.gz
```

## 🤖 Method 3: GitHub Actions (Automated)

GitHub Actions workflow is configured to automatically:
- Create GitHub Release
- Publish to PyPI (if `PYPI_API_TOKEN` secret is set)

### Setup

1. Go to PyPI: https://pypi.org/manage/account/token/
2. Create API token for "kubeagentic" project
3. Go to GitHub: Settings → Secrets and variables → Actions
4. Add secret:
   - Name: `PYPI_API_TOKEN`
   - Value: Your PyPI token

### Trigger

Just push a tag:

```bash
git tag -a v0.2.3 -m "Release v0.2.3"
git push origin v0.2.3
```

The workflow will automatically:
1. Create GitHub Release
2. Build package
3. Publish to PyPI

## 📋 Version Numbering

We follow [Semantic Versioning](https://semver.org/):

- **MAJOR** version (X.0.0): Incompatible API changes
- **MINOR** version (0.X.0): New features, backward compatible
- **PATCH** version (0.0.X): Bug fixes, backward compatible

### Examples

- `0.2.0` → `0.2.1` - Bug fix
- `0.2.1` → `0.3.0` - New features
- `0.3.0` → `1.0.0` - Breaking changes

## 🏷️ Release Types

### Regular Release

```bash
./create_release.sh 0.2.3 "Bug fixes and improvements"
```

### Hotfix Release

For critical bugs:

```bash
./create_release.sh 0.2.3 "HOTFIX: Critical security update"
```

### Feature Release

For new features:

```bash
./create_release.sh 0.3.0 "New features: Streaming support, Session management"
```

## 📝 Release Notes Template

```markdown
## What's Changed

### Features
- Added X feature
- Improved Y functionality

### Bug Fixes
- Fixed issue with Z
- Resolved problem in W

### Breaking Changes
- Changed API for...

### Installation
\`\`\`bash
pip install kubeagentic==0.2.3
\`\`\`
```

## 🔍 Verification

After release, verify:

### 1. PyPI Package

```bash
pip install kubeagentic==0.2.3 --no-cache-dir
python -c "import kubeagentic; print(kubeagentic.__version__)"
```

### 2. GitHub Release

- Check: https://github.com/KubeAgentic-Community/kubeagenticpkg/releases
- Verify assets are attached
- Confirm "Latest" badge

### 3. Package Contents

```bash
pip download kubeagentic==0.2.3 --no-deps --dest /tmp
unzip -l /tmp/kubeagentic-0.2.3-py3-none-any.whl | grep "kubeagentic/"
# Should show all 8 submodules
```

## 🐛 Troubleshooting

### Issue: PyPI Upload Failed

**Solution:** Check credentials in `requirements/pypi.credential`

### Issue: Git Tag Already Exists

**Solution:** Delete and recreate tag:
```bash
git tag -d v0.2.3
git push origin :refs/tags/v0.2.3
git tag -a v0.2.3 -m "Release v0.2.3"
git push origin v0.2.3
```

### Issue: Package Missing Submodules

**Solution:** Run build test first:
```bash
./build_and_test.sh
```

### Issue: GitHub Release Creation Failed

**Solution:** Check GitHub CLI authentication:
```bash
gh auth status
gh auth login
```

## 📚 Additional Resources

- **PyPI Project:** https://pypi.org/project/kubeagentic/
- **GitHub Releases:** https://github.com/KubeAgentic-Community/kubeagenticpkg/releases
- **Semantic Versioning:** https://semver.org/
- **GitHub CLI:** https://cli.github.com/

## 🤝 Contributing

Before creating a release:
1. Ensure all PRs are merged
2. Update documentation
3. Run full test suite
4. Update CHANGELOG (if exists)

## ⚠️ Important Notes

1. **Always test locally first:** Run `./build_and_test.sh`
2. **Check package contents:** Verify all submodules are included
3. **Version consistency:** Ensure all three files have the same version
4. **PyPI is permanent:** You cannot delete or modify a release on PyPI
5. **Tag format:** Always use `vX.Y.Z` format for tags

## 🎯 Quick Reference

| Task | Command |
|------|---------|
| Automated release | `./create_release.sh 0.2.3` |
| Build & test | `./build_and_test.sh` |
| Publish to PyPI | `./publish_to_pypi.sh` |
| Create GitHub release | `gh release create v0.2.3` |
| List tags | `git tag -l` |
| Delete remote tag | `git push origin :refs/tags/v0.2.3` |

---

**Last Updated:** October 2, 2025  
**Current Version:** 0.2.2 