"""
Test suite for Sipho AI package
"""

import pytest
import sys
import os

# Add the parent directory to the Python path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from siphoai import __version__


def test_version():
    """Test that version is defined and follows semver format"""
    assert __version__ is not None
    assert isinstance(__version__, str)

    # Basic semver format check (X.Y.Z)
    parts = __version__.split(".")
    assert len(parts) == 3

    for part in parts:
        assert part.isdigit()


def test_imports():
    """Test that main modules can be imported"""
    try:
        import siphoai

        assert hasattr(siphoai, "__version__")
        assert hasattr(siphoai, "__author__")
        assert hasattr(siphoai, "__description__")
    except ImportError as e:
        pytest.fail(f"Failed to import siphoai: {e}")


def test_cli_module():
    """Test that CLI module exists and can be imported"""
    try:
        from siphoai.cli import main

        assert callable(main)
    except ImportError as e:
        pytest.fail(f"Failed to import CLI module: {e}")


def test_app_module():
    """Test that app module components exist"""
    try:
        from siphoai.app import create_flask_app

        assert callable(create_flask_app)
    except ImportError as e:
        # This might fail if dependencies aren't installed, so we'll make it optional
        pytest.skip(f"App module import failed (dependencies may be missing): {e}")


class TestBasicFunctionality:
    """Test basic functionality without external dependencies"""

    def test_package_structure(self):
        """Ensure package has expected structure"""
        import siphoai

        # Check package attributes
        assert hasattr(siphoai, "__version__")
        assert hasattr(siphoai, "__author__")
        assert hasattr(siphoai, "__email__")
        assert hasattr(siphoai, "__description__")

        # Check version format
        version_parts = siphoai.__version__.split(".")
        assert len(version_parts) >= 2  # At least major.minor

    def test_version_consistency(self):
        """Test that version is consistent across files"""
        import siphoai

        # Read version from setup.py
        setup_py_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "setup.py"
        )

        if os.path.exists(setup_py_path):
            with open(setup_py_path, "r", encoding="utf-8") as f:
                setup_content = f.read()

            # Extract version from setup.py
            for line in setup_content.split("\n"):
                if "version=" in line and '"' in line:
                    setup_version = line.split('"')[1]
                    assert (
                        setup_version == siphoai.__version__
                    ), f"Version mismatch: setup.py has {setup_version}, __init__.py has {siphoai.__version__}"
                    break


if __name__ == "__main__":
    pytest.main([__file__])
