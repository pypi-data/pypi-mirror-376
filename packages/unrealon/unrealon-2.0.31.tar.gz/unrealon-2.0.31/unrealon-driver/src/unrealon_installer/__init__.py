"""
UnrealOn Universal Installer - Clean Edition

One function installs everything. Simple and reliable.
"""

from .core import install_parser
from .browser_fixes import fix_browsers, diagnose_browsers, get_browser_status
from .platform import apply_platform_fixes, cleanup_asyncio_resources

__version__ = "2.0.0"
__all__ = ["install_parser", "fix_browsers", "diagnose_browsers", "get_browser_status", "apply_platform_fixes", "cleanup_asyncio_resources"]
