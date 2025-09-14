#!/usr/bin/env python3
"""
Allow siphoai to be executable as a module with `python -m siphoai`.
"""

from .cli import main

if __name__ == "__main__":
    main()