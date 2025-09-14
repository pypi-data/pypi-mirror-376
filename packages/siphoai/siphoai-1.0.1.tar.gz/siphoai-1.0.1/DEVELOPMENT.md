# Sipho AI - Development Guide

## Package Development and Deployment

This document explains how to build and deploy the Sipho AI package to PyPI.

## Prerequisites

1. **Python 3.7+** installed
2. **pip** package manager
3. **PyPI account** (create at https://pypi.org/account/register/)
4. **Test PyPI account** (create at https://test.pypi.org/account/register/)

## Building the Package

### Method 1: Using Build Script (Recommended)

```bash
# On Windows
build.bat

# On Linux/Mac
python build.py
```

### Method 2: Manual Build

```bash
# Install build dependencies
pip install --upgrade pip setuptools wheel build twine

# Clean previous builds
rm -rf build dist *.egg-info

# Build the package
python -m build
```

## Testing the Package Locally

```bash
# Install the built package
pip install dist/siphoai-1.0.0-py3-none-any.whl

# Test the CLI
siphoai --version
siphoai help-commands
siphoai test "open calculator"

# Start the server
siphoai
```

## Uploading to PyPI

### Step 1: Upload to Test PyPI (Recommended First)

```bash
python upload.py
# Select option 1: Upload to Test PyPI
```

### Step 2: Test Installation from Test PyPI

```bash
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ siphoai
```

### Step 3: Upload to Production PyPI

```bash
python upload.py  
# Select option 2: Upload to PyPI
```

## Package Structure

```
siphoai/
├── __init__.py              # Package initialization
├── app.py                   # Main Flask application  
├── cli.py                   # Command-line interface
├── data/
│   └── commands.json        # Default commands
└── utils/
    ├── __init__.py
    ├── command_manager.py   # Command management
    └── system_checker.py    # System scanning
```

## Configuration Files

- **setup.py**: Legacy setup configuration
- **pyproject.toml**: Modern Python packaging configuration
- **MANIFEST.in**: Specifies additional files to include
- **requirements.txt**: Runtime dependencies
- **LICENSE**: MIT license file

## Release Checklist

- [ ] Update version in `siphoai/__init__.py`
- [ ] Update version in `setup.py` and `pyproject.toml`
- [ ] Update CHANGELOG.md with new features
- [ ] Test all commands work correctly
- [ ] Build and test package locally
- [ ] Upload to Test PyPI and verify
- [ ] Upload to production PyPI
- [ ] Create GitHub release tag
- [ ] Update documentation

## Environment Variables

The package supports these environment variables:

```bash
# Required for AI features
OPENROUTER_API_KEY=your_key_here

# Optional Flask configuration
FLASK_HOST=0.0.0.0
FLASK_PORT=5000
FLASK_DEBUG=false

# Optional site information
SITE_URL=http://localhost:5000
SITE_NAME=Sipho AI Voice Assistant
```

## Troubleshooting

### Build Issues

1. **Missing dependencies**: Run `pip install build wheel setuptools twine`
2. **Permission errors**: Use `pip install --user` or virtual environment
3. **Path issues**: Ensure Python and pip are in your PATH

### Upload Issues

1. **Authentication**: Use API tokens instead of passwords
2. **Duplicate version**: Increment version number in config files
3. **File not found**: Run build script first

### Runtime Issues

1. **Module not found**: Ensure package is installed correctly
2. **API errors**: Check OPENROUTER_API_KEY in .env file
3. **Port conflicts**: Change FLASK_PORT in configuration

## Support

For issues and questions:
- Create an issue on GitHub
- Check the documentation
- Review the example configurations