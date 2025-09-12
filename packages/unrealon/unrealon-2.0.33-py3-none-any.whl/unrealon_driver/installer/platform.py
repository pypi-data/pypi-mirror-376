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
    
    # AGGRESSIVE Windows asyncio fixes
    if sys.version_info >= (3, 8):
        try:
            # Close any existing event loop first
            try:
                current_loop = asyncio.get_event_loop()
                if current_loop and not current_loop.is_closed():
                    current_loop.close()
            except Exception:
                pass
            
            # Force ProactorEventLoopPolicy to avoid pipe issues
            policy = asyncio.WindowsProactorEventLoopPolicy()
            asyncio.set_event_loop_policy(policy)
            
            # Create and set a completely new event loop
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            fixes.append("ProactorEventLoop + clean loop")
        except Exception as e:
            logger.warning(f"Failed to set Windows event loop policy: {e}")
            # Fallback: try to at least set the policy
            try:
                asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
                fixes.append("ProactorEventLoop (fallback)")
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
    
    # AGGRESSIVE warning suppression for Windows
    warnings.filterwarnings("ignore", category=ResourceWarning)
    warnings.filterwarnings("ignore", category=DeprecationWarning, module="asyncio")
    warnings.filterwarnings("ignore", message=".*unclosed transport.*")
    warnings.filterwarnings("ignore", message=".*I/O operation on closed pipe.*")
    warnings.filterwarnings("ignore", message=".*unclosed.*")
    warnings.filterwarnings("ignore", message=".*BaseSubprocessTransport.*")
    warnings.filterwarnings("ignore", message=".*ProactorBasePipeTransport.*")
    
    # Set asyncio debug mode to False to reduce noise
    try:
        asyncio.get_event_loop().set_debug(False)
    except Exception:
        pass
    
    fixes.append("Aggressive Windows warnings suppression")
    
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


def cleanup_asyncio_resources():
    """Force cleanup of all asyncio resources. Call this at program exit on Windows."""
    if platform.system() != "Windows":
        return
    
    try:
        # Get current loop and close all pending tasks
        loop = asyncio.get_event_loop()
        if loop and not loop.is_closed():
            # Cancel all pending tasks
            pending = asyncio.all_tasks(loop)
            for task in pending:
                task.cancel()
            
            # Wait for tasks to finish cancellation
            if pending:
                loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
            
            # Close the loop
            loop.close()
            
    except Exception:
        # Ignore all cleanup errors
        pass
    
    # Force garbage collection to clean up any remaining references
    import gc
    gc.collect()
