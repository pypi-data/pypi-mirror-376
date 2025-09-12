"""
Platform compatibility fixes. Clean and simple.
"""

import asyncio
import sys
import platform
import warnings
import logging

logger = logging.getLogger(__name__)


def apply_platform_fixes():
    """Apply all necessary platform fixes automatically."""
    system = platform.system()
    fixes = []
    
    if system == "Windows":
        fixes.extend(_apply_windows_fixes())
    elif system == "Darwin":  # macOS
        fixes.extend(_apply_macos_fixes())
    elif system == "Linux":
        fixes.extend(_apply_linux_fixes())
    
    if fixes:
        logger.info(f"✅ Applied platform fixes: {', '.join(fixes)}")
    
    return fixes


def _apply_windows_fixes():
    """Windows-specific fixes."""
    fixes = []
    
    # Asyncio event loop policy
    if sys.version_info >= (3, 8):
        try:
            asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
            fixes.append("ProactorEventLoop")
        except Exception:
            pass
    
    # Console encoding
    try:
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8')
            sys.stderr.reconfigure(encoding='utf-8')
            fixes.append("UTF-8 encoding")
    except Exception:
        pass
    
    # Suppress warnings
    warnings.filterwarnings("ignore", category=ResourceWarning)
    fixes.append("ResourceWarning suppression")
    
    return fixes


def _apply_macos_fixes():
    """macOS-specific fixes."""
    fixes = []
    
    # SSL context fix
    try:
        import ssl
        ssl._create_default_https_context = ssl._create_unverified_context
        fixes.append("SSL context")
    except Exception:
        pass
    
    # File descriptor limits
    try:
        import resource
        soft, hard = resource.getrlimit(resource.RLIMIT_NOFILE)
        if soft < 1024:
            resource.setrlimit(resource.RLIMIT_NOFILE, (min(1024, hard), hard))
            fixes.append("File descriptor limit")
    except Exception:
        pass
    
    return fixes


def _apply_linux_fixes():
    """Linux-specific fixes."""
    fixes = []
    
    # File descriptor limits
    try:
        import resource
        soft, hard = resource.getrlimit(resource.RLIMIT_NOFILE)
        if soft < 2048:
            resource.setrlimit(resource.RLIMIT_NOFILE, (min(2048, hard), hard))
            fixes.append("File descriptor limit")
    except Exception:
        pass
    
    # Headless display
    import os
    if not os.environ.get('DISPLAY'):
        os.environ['DISPLAY'] = ':99'
        fixes.append("Headless display")
    
    return fixes


def get_platform_info():
    """Get platform information."""
    return {
        'platform': platform.system(),
        'architecture': platform.architecture()[0],
        'python_version': f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
    }


def check_system_requirements():
    """Check if system meets requirements."""
    return {
        'python_version': sys.version_info >= (3, 9),
        'platform_supported': platform.system() in ['Windows', 'Darwin', 'Linux']
    }
