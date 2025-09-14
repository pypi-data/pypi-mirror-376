# PyPI Upload Guide

This guide explains how to upload the youtube-mcp-server package to PyPI.

## Prerequisites

1. Install twine:
```bash
pip install twine
```

2. Create accounts on:
   - [PyPI](https://pypi.org/account/register/) (production)
   - [Test PyPI](https://test.pypi.org/account/register/) (testing)

## Upload Process

### 1. Test Upload (Recommended First)

Upload to Test PyPI first to verify everything works:

```bash
python -m twine upload --repository testpypi dist/*
```

You'll be prompted for:
- Username: `__token__`
- Password: Your Test PyPI API token (get from https://test.pypi.org/manage/account/#api-tokens)

### 2. Production Upload

After testing, upload to the real PyPI:

```bash
python -m twine upload dist/*
```

You'll be prompted for:
- Username: `__token__`
- Password: Your PyPI API token (get from https://pypi.org/manage/account/#api-tokens)

## API Token Setup

### For Test PyPI:
1. Go to https://test.pypi.org/manage/account/#api-tokens
2. Click "Add API token"
3. Set the token name (e.g., "youtube-mcp-server")
4. Set the scope to "Entire account" (or specific project after first upload)
5. Copy the generated token

### For PyPI:
1. Go to https://pypi.org/manage/account/#api-tokens
2. Follow the same steps as Test PyPI

## Configuration File (Optional)

Create `~/.pypirc` to store credentials:

```ini
[distutils]
index-servers =
    pypi
    testpypi

[pypi]
username = __token__
password = pypi-your-api-token-here

[testpypi]
repository = https://test.pypi.org/legacy/
username = __token__
password = pypi-your-test-api-token-here
```

## Verify Upload

After uploading, verify the package:

### Test PyPI:
```bash
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ youtube-mcp-server
```

### PyPI:
```bash
pip install youtube-mcp-server
```

## Update Version

For future updates:
1. Update version in `pyproject.toml`
2. Rebuild: `python -m build`
3. Upload new version: `python -m twine upload dist/*`

## Package Information

- Package name: `youtube-mcp-server`
- Author: yzfly
- License: MIT
- Repository: https://github.com/yzfly/youtube-mcp-server (update this URL)