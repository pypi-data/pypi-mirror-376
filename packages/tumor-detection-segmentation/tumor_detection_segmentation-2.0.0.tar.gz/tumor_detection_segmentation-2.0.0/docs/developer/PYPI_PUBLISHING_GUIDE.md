# Publishing to PyPI Guide

This guide walks you through publishing the `tumor-detection-segmentation` package to PyPI.

## Prerequisites

1. **PyPI Account**: Create accounts on both [PyPI](https://pypi.org/account/register/) and [Test PyPI](https://test.pypi.org/account/register/)
2. **API Tokens**: Generate API tokens for secure authentication
3. **Build Tools**: Install required packaging tools

```bash
# Install build tools
pip install build twine

# Verify tools are installed
python -m build --help
twine --help
```

## Step 1: Prepare the Package

Ensure all files are up to date:

```bash
# Update version in src/tumor_detection/__init__.py if needed
# Update CHANGELOG.md with new version details
# Commit all changes
git add .
git commit -m "Prepare v2.0.0 for PyPI release"
git tag v2.0.0
git push origin main --tags
```

## Step 2: Build the Package

Build both source distribution and wheel:

```bash
# Clean previous builds
rm -rf dist/ build/ *.egg-info/

# Build the package
python -m build

# Verify build outputs
ls -la dist/
# Should show:
# tumor_detection_segmentation-2.0.0.tar.gz
# tumor_detection_segmentation-2.0.0-py3-none-any.whl
```

## Step 3: Test Upload to Test PyPI

Always test on Test PyPI first:

```bash
# Upload to Test PyPI
twine upload --repository testpypi dist/*

# Test installation from Test PyPI
pip install --index-url https://test.pypi.org/simple/ \
  --extra-index-url https://pypi.org/simple/ \
  tumor-detection-segmentation

# Test basic functionality
python -c "import tumor_detection; print(tumor_detection.__version__)"
```

## Step 4: Upload to Production PyPI

If testing succeeds, upload to production PyPI:

```bash
# Upload to production PyPI
twine upload dist/*

# Verify upload
pip install tumor-detection-segmentation
python -c "import tumor_detection; print(tumor_detection.__version__)"
```

## Step 5: Update Documentation

Update README.md to include PyPI installation:

```bash
# Installation section should now show:
pip install tumor-detection-segmentation

# Instead of just:
git clone ... && pip install -e .
```

## Authentication Setup

### Option 1: API Tokens (Recommended)

1. Generate API tokens on PyPI and Test PyPI
2. Configure in `~/.pypirc`:

```ini
[distutils]
index-servers =
    pypi
    testpypi

[pypi]
repository = https://upload.pypi.org/legacy/
username = __token__
password = pypi-your-api-token-here

[testpypi]
repository = https://test.pypi.org/legacy/
username = __token__
password = pypi-your-test-api-token-here
```

### Option 2: Interactive Authentication

```bash
# Upload with interactive authentication
twine upload --repository testpypi dist/* --verbose

# You'll be prompted for username/password
```

## Automated Publishing with GitHub Actions

Create `.github/workflows/publish.yml`:

```yaml
name: Publish to PyPI

on:
  release:
    types: [published]

jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.10'

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install build twine

    - name: Build package
      run: python -m build

    - name: Publish to PyPI
      env:
        TWINE_USERNAME: __token__
        TWINE_PASSWORD: ${{ secrets.PYPI_API_TOKEN }}
      run: twine upload dist/*
```

## Package Verification Checklist

Before publishing, verify:

- [ ] Version number updated in `__init__.py`
- [ ] CHANGELOG.md updated with new version
- [ ] All tests pass: `pytest tests/`
- [ ] Package builds successfully: `python -m build`
- [ ] No sensitive files included: check `MANIFEST.in`
- [ ] License file included
- [ ] README.md up to date
- [ ] Dependencies correctly specified in `pyproject.toml`
- [ ] CLI entry points work: `tumor-detect-train --help`

## Post-Publication Tasks

1. **Update README**: Add PyPI badges and installation instructions
2. **Create Release**: Create GitHub release with changelog
3. **Documentation**: Update docs with PyPI installation
4. **Community**: Announce on relevant forums/communities
5. **Monitor**: Watch for issues and user feedback

## Version Management

Follow semantic versioning:

- **Major (2.0.0)**: Breaking changes
- **Minor (2.1.0)**: New features, backward compatible
- **Patch (2.0.1)**: Bug fixes, backward compatible

## Common Issues and Solutions

### Build Failures

```bash
# Missing files error
# Solution: Update MANIFEST.in to include necessary files

# Import errors during build
# Solution: Check src/tumor_detection/__init__.py imports
```

### Upload Failures

```bash
# Authentication error
# Solution: Check API token and ~/.pypirc configuration

# File already exists error
# Solution: Increment version number, can't overwrite existing versions
```

### Installation Issues

```bash
# Dependency conflicts
# Solution: Review and update dependency versions in pyproject.toml

# Missing optional dependencies
# Solution: Install with extras: pip install tumor-detection-segmentation[all]
```

## Support

For publishing issues:

- PyPI Help: https://pypi.org/help/
- Packaging Guide: https://packaging.python.org/
- Test PyPI: https://test.pypi.org/

For package issues:

- GitHub Issues: https://github.com/hkevin01/tumor-detection-segmentation/issues
- Documentation: https://github.com/hkevin01/tumor-detection-segmentation/docs
