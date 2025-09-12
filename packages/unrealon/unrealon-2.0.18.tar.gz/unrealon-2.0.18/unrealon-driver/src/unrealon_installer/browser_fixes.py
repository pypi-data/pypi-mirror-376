"""
Browser troubleshooting and fixes for Windows.
"""

import os
import sys
import subprocess
import platform
from pathlib import Path
from typing import Dict, List, Optional
import shutil


class BrowserFixer:
    """Windows browser troubleshooting and fixes."""
    
    def __init__(self):
        self.is_windows = platform.system() == "Windows"
        self.playwright_cache = self._get_playwright_cache_path()
    
    def _get_playwright_cache_path(self) -> Optional[Path]:
        """Get Playwright cache directory path."""
        if self.is_windows:
            return Path(os.environ.get("USERPROFILE", "")) / "AppData" / "Local" / "ms-playwright"
        elif platform.system() == "Darwin":  # macOS
            return Path.home() / "Library" / "Caches" / "ms-playwright"
        else:  # Linux
            return Path.home() / ".cache" / "ms-playwright"
    
    def diagnose_browser_issues(self) -> Dict[str, bool]:
        """Diagnose common browser issues."""
        issues = {}
        
        # Check if Playwright is installed
        issues['playwright_installed'] = self._check_playwright_installed()
        
        # Check if browsers are installed
        issues['browsers_installed'] = self._check_browsers_installed()
        
        # Check cache directory
        issues['cache_exists'] = self._check_cache_directory()
        
        # Check if browsers can launch
        issues['browser_launch_test'] = self._test_browser_launch()
        
        return issues
    
    def _check_playwright_installed(self) -> bool:
        """Check if Playwright is installed."""
        try:
            subprocess.run([sys.executable, "-c", "import playwright"], 
                         check=True, capture_output=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
    
    def _check_browsers_installed(self) -> bool:
        """Check if Playwright browsers are installed."""
        try:
            result = subprocess.run([sys.executable, "-m", "playwright", "--version"], 
                                  check=True, capture_output=True, text=True)
            return "version" in result.stdout.lower()
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
    
    def _check_cache_directory(self) -> bool:
        """Check if Playwright cache directory exists."""
        if not self.playwright_cache:
            return False
        return self.playwright_cache.exists()
    
    def _test_browser_launch(self) -> bool:
        """Test if browser can launch (quick test)."""
        try:
            test_code = """
from playwright.sync_api import sync_playwright
try:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        browser.close()
    print("OK")
except Exception as e:
    print(f"ERROR: {e}")
"""
            result = subprocess.run([sys.executable, "-c", test_code], 
                                  capture_output=True, text=True, timeout=30)
            return "OK" in result.stdout
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            return False
    
    def fix_browser_issues(self, force_reinstall: bool = False) -> bool:
        """Fix common browser issues."""
        print("🔧 Fixing browser issues...")
        
        success = True
        
        # Step 1: Clear cache if it exists
        if self._clear_browser_cache():
            print("✅ Browser cache cleared")
        else:
            print("⚠️  Could not clear browser cache")
        
        # Step 2: Reinstall Playwright if needed or forced
        if force_reinstall or not self._check_playwright_installed():
            if self._reinstall_playwright():
                print("✅ Playwright reinstalled")
            else:
                print("❌ Failed to reinstall Playwright")
                success = False
        
        # Step 3: Install browsers
        if self._install_browsers():
            print("✅ Browsers installed")
        else:
            print("❌ Failed to install browsers")
            success = False
        
        # Step 4: Test installation
        if self._test_browser_launch():
            print("✅ Browser test passed")
        else:
            print("❌ Browser test failed")
            success = False
        
        return success
    
    def _clear_browser_cache(self) -> bool:
        """Clear Playwright browser cache."""
        try:
            if self.playwright_cache and self.playwright_cache.exists():
                shutil.rmtree(self.playwright_cache, ignore_errors=True)
                print(f"Cleared cache: {self.playwright_cache}")
            return True
        except Exception as e:
            print(f"Cache clear error: {e}")
            return False
    
    def _reinstall_playwright(self) -> bool:
        """Reinstall Playwright completely."""
        try:
            # Uninstall
            subprocess.run([sys.executable, "-m", "pip", "uninstall", "-y", "playwright"], 
                         check=False, capture_output=True)
            
            # Clear pip cache
            subprocess.run([sys.executable, "-m", "pip", "cache", "purge"], 
                         check=False, capture_output=True)
            
            # Reinstall
            subprocess.run([sys.executable, "-m", "pip", "install", "playwright"], 
                         check=True, capture_output=True)
            
            return True
        except subprocess.CalledProcessError:
            return False
    
    def _install_browsers(self) -> bool:
        """Install Playwright browsers."""
        try:
            # Install chromium (most stable)
            subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], 
                         check=True, capture_output=True)
            
            # Try to install firefox too (optional)
            subprocess.run([sys.executable, "-m", "playwright", "install", "firefox"], 
                         check=False, capture_output=True)
            
            return True
        except subprocess.CalledProcessError:
            return False
    
    def get_browser_info(self) -> Dict[str, str]:
        """Get browser installation information."""
        info = {}
        
        # Playwright version
        try:
            # Try new way first
            result = subprocess.run([sys.executable, "-c", "import playwright; print(getattr(playwright, '__version__', 'Unknown'))"], 
                                  capture_output=True, text=True)
            if "Unknown" in result.stdout:
                # Fallback to CLI version
                result = subprocess.run([sys.executable, "-m", "playwright", "--version"], 
                                      capture_output=True, text=True)
            info['playwright_version'] = result.stdout.strip()
        except:
            info['playwright_version'] = "Not installed"
        
        # Cache directory
        info['cache_path'] = str(self.playwright_cache) if self.playwright_cache else "Unknown"
        info['cache_exists'] = str(self._check_cache_directory())
        
        # Browser test
        info['browser_test'] = "PASS" if self._test_browser_launch() else "FAIL"
        
        return info


def fix_browsers(force_reinstall: bool = False) -> bool:
    """
    Quick browser fix function.
    
    Args:
        force_reinstall: Force complete reinstall
    
    Returns:
        True if successful
    """
    fixer = BrowserFixer()
    return fixer.fix_browser_issues(force_reinstall)


def diagnose_browsers() -> Dict[str, bool]:
    """
    Quick browser diagnosis.
    
    Returns:
        Dictionary with diagnosis results
    """
    fixer = BrowserFixer()
    return fixer.diagnose_browser_issues()


def get_browser_status() -> Dict[str, str]:
    """
    Get browser status information.
    
    Returns:
        Dictionary with browser info
    """
    fixer = BrowserFixer()
    return fixer.get_browser_info()
