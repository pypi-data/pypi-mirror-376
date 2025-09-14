"""
Sipho AI - Voice Command Assistant
A scalable Python application that uses AI to execute voice commands on your PC.
"""

__version__ = "1.0.2"
__author__ = "Your Name"
__email__ = "your.email@example.com"
__description__ = "AI-powered voice command assistant for desktop automation"

try:
    from .app import CommandProcessor, create_flask_app, run_server
    from .cli import main
    __all__ = ['CommandProcessor', 'create_flask_app', 'run_server', 'main']
except ImportError:
    # Allow partial imports for development
    __all__ = []