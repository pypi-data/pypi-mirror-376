"""
Cross-platform compatibility utilities for UnrealOn Driver.

Handles platform-specific configurations and fixes for Windows, macOS, and Linux.
"""

import asyncio
import sys
import platform
import warnings
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class PlatformCompatibility:
    """
    Handles cross-platform compatibility for UnrealOn Driver.
    
    Automatically applies platform-specific fixes and configurations
    to ensure consistent behavior across Windows, macOS, and Linux.
    """
    
    def __init__(self):
        """Initialize platform compatibility."""
        self.platform = platform.system()
        self.python_version = sys.version_info
        self._applied_fixes = []
    
    def apply_all_fixes(self) -> None:
        """
        Apply all platform-specific fixes automatically.
        
        This method should be called once at the start of the application
        to ensure optimal cross-platform compatibility.
        """
        logger.info(f"🔧 Applying platform fixes for {self.platform}")
        
        if self.platform == "Windows":
            self._apply_windows_fixes()
        elif self.platform == "Darwin":  # macOS
            self._apply_macos_fixes()
        elif self.platform == "Linux":
            self._apply_linux_fixes()
        
        logger.info(f"✅ Applied {len(self._applied_fixes)} platform fixes: {', '.join(self._applied_fixes)}")
    
    def _apply_windows_fixes(self) -> None:
        """Apply Windows-specific fixes."""
        
        # Fix 1: Set ProactorEventLoopPolicy for better asyncio performance
        if self.python_version >= (3, 8):
            try:
                asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
                self._applied_fixes.append("WindowsProactorEventLoopPolicy")
                logger.debug("✅ Set WindowsProactorEventLoopPolicy for better asyncio performance")
            except Exception as e:
                logger.warning(f"⚠️ Failed to set WindowsProactorEventLoopPolicy: {e}")
        
        # Fix 2: Suppress ResourceWarning on Windows
        try:
            warnings.filterwarnings("ignore", category=ResourceWarning)
            self._applied_fixes.append("ResourceWarning suppression")
            logger.debug("✅ Suppressed ResourceWarning for cleaner output")
        except Exception as e:
            logger.warning(f"⚠️ Failed to suppress ResourceWarning: {e}")
        
        # Fix 3: Set console encoding to UTF-8 if possible
        try:
            if hasattr(sys.stdout, 'reconfigure'):
                sys.stdout.reconfigure(encoding='utf-8')
                sys.stderr.reconfigure(encoding='utf-8')
                self._applied_fixes.append("UTF-8 console encoding")
                logger.debug("✅ Set console encoding to UTF-8")
        except Exception as e:
            logger.debug(f"Console encoding fix not needed or failed: {e}")
        
        # Fix 4: Increase default socket timeout for Windows
        try:
            import socket
            socket.setdefaulttimeout(30.0)
            self._applied_fixes.append("Socket timeout increase")
            logger.debug("✅ Increased default socket timeout to 30s")
        except Exception as e:
            logger.warning(f"⚠️ Failed to set socket timeout: {e}")
    
    def _apply_macos_fixes(self) -> None:
        """Apply macOS-specific fixes."""
        
        # Fix 1: Handle macOS SSL context issues
        try:
            import ssl
            # Create unverified SSL context for development
            ssl._create_default_https_context = ssl._create_unverified_context
            self._applied_fixes.append("SSL context fix")
            logger.debug("✅ Applied macOS SSL context fix")
        except Exception as e:
            logger.debug(f"SSL context fix not needed: {e}")
        
        # Fix 2: Set optimal file descriptor limits
        try:
            import resource
            soft, hard = resource.getrlimit(resource.RLIMIT_NOFILE)
            if soft < 1024:
                resource.setrlimit(resource.RLIMIT_NOFILE, (min(1024, hard), hard))
                self._applied_fixes.append("File descriptor limit increase")
                logger.debug("✅ Increased file descriptor limit")
        except Exception as e:
            logger.debug(f"File descriptor limit fix not needed: {e}")
    
    def _apply_linux_fixes(self) -> None:
        """Apply Linux-specific fixes."""
        
        # Fix 1: Set optimal file descriptor limits
        try:
            import resource
            soft, hard = resource.getrlimit(resource.RLIMIT_NOFILE)
            if soft < 2048:
                resource.setrlimit(resource.RLIMIT_NOFILE, (min(2048, hard), hard))
                self._applied_fixes.append("File descriptor limit increase")
                logger.debug("✅ Increased file descriptor limit")
        except Exception as e:
            logger.debug(f"File descriptor limit fix not needed: {e}")
        
        # Fix 2: Handle display issues for headless environments
        try:
            import os
            if not os.environ.get('DISPLAY'):
                os.environ['DISPLAY'] = ':99'
                self._applied_fixes.append("Headless display fix")
                logger.debug("✅ Set display for headless environment")
        except Exception as e:
            logger.debug(f"Display fix not needed: {e}")
    
    def get_platform_info(self) -> dict:
        """
        Get detailed platform information.
        
        Returns:
            Dictionary with platform details
        """
        return {
            'platform': self.platform,
            'platform_release': platform.release(),
            'platform_version': platform.version(),
            'architecture': platform.architecture(),
            'machine': platform.machine(),
            'processor': platform.processor(),
            'python_version': f"{self.python_version.major}.{self.python_version.minor}.{self.python_version.micro}",
            'python_implementation': platform.python_implementation(),
            'applied_fixes': self._applied_fixes
        }
    
    @classmethod
    def auto_configure(cls) -> 'PlatformCompatibility':
        """
        Automatically configure platform compatibility.
        
        This is the recommended way to use this class - it will
        automatically detect the platform and apply all necessary fixes.
        
        Returns:
            Configured PlatformCompatibility instance
        """
        compatibility = cls()
        compatibility.apply_all_fixes()
        return compatibility


# Global instance for easy access
_platform_compatibility: Optional[PlatformCompatibility] = None


def ensure_platform_compatibility() -> PlatformCompatibility:
    """
    Ensure platform compatibility is configured.
    
    This function can be called multiple times safely - it will only
    configure compatibility once per application run.
    
    Returns:
        PlatformCompatibility instance
    """
    global _platform_compatibility
    
    if _platform_compatibility is None:
        _platform_compatibility = PlatformCompatibility.auto_configure()
    
    return _platform_compatibility


def get_platform_info() -> dict:
    """
    Get platform information.
    
    Returns:
        Dictionary with platform details
    """
    compatibility = ensure_platform_compatibility()
    return compatibility.get_platform_info()


# Auto-configure on import for convenience
ensure_platform_compatibility()
