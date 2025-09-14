"""
PATH management utilities for siphoai package installation
Automatically adds/removes Python Scripts directory to/from PATH on Windows
"""

import os
import sys
import subprocess
import winreg
from pathlib import Path


def get_python_scripts_dir():
    """Get the Python Scripts directory where siphoai.exe is installed"""
    if hasattr(sys, "real_prefix") or (
        hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix
    ):
        # We're in a virtual environment
        scripts_dir = Path(sys.prefix) / "Scripts"
    else:
        # We're in the system Python - find the actual Scripts directory
        if sys.platform == "win32":
            # For Windows Store Python or regular Python
            python_exe = Path(sys.executable)

            # Check multiple possible locations
            possible_scripts = [
                python_exe.parent / "Scripts",  # Standard Python installation
                Path(os.environ.get("LOCALAPPDATA", ""))
                / "Packages"
                / "PythonSoftwareFoundation.Python.3.11_qbz5n2kfra8p0"
                / "LocalCache"
                / "local-packages"
                / "Python311"
                / "Scripts",
                Path(os.path.expanduser("~"))
                / "AppData"
                / "Roaming"
                / "Python"
                / f"Python{sys.version_info.major}{sys.version_info.minor}"
                / "Scripts",
            ]

            # Find the first existing directory
            for scripts_path in possible_scripts:
                if scripts_path.exists():
                    return str(scripts_path)

            # Default fallback
            return str(python_exe.parent / "Scripts")
        else:
            # Unix-like systems
            return str(Path(sys.executable).parent)

    return str(scripts_dir)


def add_to_path(directory):
    """Add directory to system PATH (Windows)"""
    if sys.platform != "win32":
        print("⚠️  PATH management is currently only supported on Windows")
        return True  # Don't fail on non-Windows systems

    if not os.path.exists(directory):
        print(f"⚠️  Directory {directory} does not exist, creating PATH entry anyway")

    try:
        # Get current PATH from registry
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, "Environment", 0, winreg.KEY_ALL_ACCESS
        ) as key:
            try:
                current_path, _ = winreg.QueryValueEx(key, "PATH")
            except FileNotFoundError:
                current_path = ""

            # Check if directory is already in PATH
            path_parts = [p.strip() for p in current_path.split(";") if p.strip()]
            if any(p.lower() == directory.lower() for p in path_parts):
                print(f"✅ {directory} is already in PATH")
                return True

            # Add directory to PATH
            new_path = f"{current_path};{directory}" if current_path else directory
            winreg.SetValueEx(key, "PATH", 0, winreg.REG_EXPAND_SZ, new_path)

        print(f"✅ Added {directory} to PATH")

        # Notify system of environment change
        try:
            import ctypes
            from ctypes import wintypes

            HWND_BROADCAST = 0xFFFF
            WM_SETTINGCHANGE = 0x001A
            SMTO_ABORTIFHUNG = 0x0002
            result = ctypes.windll.user32.SendMessageTimeoutW(
                HWND_BROADCAST,
                WM_SETTINGCHANGE,
                0,
                "Environment",
                SMTO_ABORTIFHUNG,
                5000,
                ctypes.byref(wintypes.DWORD()),
            )
            if result:
                print("📡 Successfully notified system of PATH changes")
        except Exception as e:
            print(f"⚠️  Could not broadcast PATH change: {e}")
            print("🔄 You may need to restart your terminal for changes to take effect")

        return True

    except Exception as e:
        print(f"❌ Failed to add {directory} to PATH: {e}")
        return False


def remove_from_path(directory):
    """Remove directory from system PATH (Windows)"""
    if sys.platform != "win32":
        print("⚠️  PATH management is currently only supported on Windows")
        return True

    try:
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, "Environment", 0, winreg.KEY_ALL_ACCESS
        ) as key:
            try:
                current_path, _ = winreg.QueryValueEx(key, "PATH")
            except FileNotFoundError:
                print("✅ PATH variable not found or already clean")
                return True

            # Remove directory from PATH
            path_parts = [p.strip() for p in current_path.split(";") if p.strip()]
            new_path_parts = [p for p in path_parts if p.lower() != directory.lower()]

            if len(new_path_parts) == len(path_parts):
                print(f"✅ {directory} was not in PATH")
                return True

            new_path = ";".join(new_path_parts)
            winreg.SetValueEx(key, "PATH", 0, winreg.REG_EXPAND_SZ, new_path)

        print(f"✅ Removed {directory} from PATH")

        # Notify system of environment change
        try:
            import ctypes
            from ctypes import wintypes

            HWND_BROADCAST = 0xFFFF
            WM_SETTINGCHANGE = 0x001A
            SMTO_ABORTIFHUNG = 0x0002
            ctypes.windll.user32.SendMessageTimeoutW(
                HWND_BROADCAST,
                WM_SETTINGCHANGE,
                0,
                "Environment",
                SMTO_ABORTIFHUNG,
                5000,
                ctypes.byref(wintypes.DWORD()),
            )
            print("📡 Successfully notified system of PATH changes")
        except Exception as e:
            print(f"⚠️  Could not broadcast PATH change: {e}")

        return True

    except Exception as e:
        print(f"❌ Failed to remove {directory} from PATH: {e}")
        return False


def install_path():
    """Add siphoai to PATH during installation"""
    print("🔧 Setting up siphoai PATH integration...")

    scripts_dir = get_python_scripts_dir()
    print(f"📁 Python Scripts directory: {scripts_dir}")

    if add_to_path(scripts_dir):
        print("✅ siphoai has been added to PATH!")
        print("📝 You can now use 'siphoai' command from anywhere in your terminal")
        print(
            "🔄 If the command doesn't work immediately, please restart your terminal"
        )
        return True
    else:
        print("❌ Failed to add siphoai to PATH")
        print("💡 You can still use: python -m siphoai")
        return False


def uninstall_path():
    """Remove siphoai from PATH during uninstallation"""
    print("🧹 Cleaning up siphoai PATH integration...")

    scripts_dir = get_python_scripts_dir()
    print(f"📁 Python Scripts directory: {scripts_dir}")

    if remove_from_path(scripts_dir):
        print("✅ siphoai has been removed from PATH")
        return True
    else:
        print("❌ Failed to remove siphoai from PATH")
        return False


if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "install":
            install_path()
        elif sys.argv[1] == "uninstall":
            uninstall_path()
        else:
            print("Usage: python installer.py [install|uninstall]")
    else:
        print("Sipho AI PATH Installer")
        print("Usage: python installer.py [install|uninstall]")
