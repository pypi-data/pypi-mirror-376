"""
UnrealOn Universal Installer - Clean Edition

One function installs everything. Simple and reliable.
"""

from .core import install_parser
from .browser_fixes import fix_browsers, diagnose_browsers, get_browser_status

__version__ = "2.0.0"
__all__ = ["install_parser", "fix_browsers", "diagnose_browsers", "get_browser_status"]
