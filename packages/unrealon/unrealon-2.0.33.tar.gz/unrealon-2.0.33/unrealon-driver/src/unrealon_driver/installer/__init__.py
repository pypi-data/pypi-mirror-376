"""
Simple installer utilities for UnrealOn parsers.
No bullshit, just platform fixes.
"""

from .platform import apply_platform_fixes, cleanup_asyncio_resources

__all__ = ["apply_platform_fixes", "cleanup_asyncio_resources"]
