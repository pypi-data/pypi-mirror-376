"""
Clean browser manager using unrealon_browser.
"""

from typing import Optional
from pydantic import Field

from unrealon_browser import BrowserManager as CoreBrowserManager, BrowserConfig
from unrealon_browser.dto.models.enums import BrowserMode

from .base import BaseManager, ManagerConfig


class BrowserManagerConfig(ManagerConfig):
    """Browser manager configuration."""

    headless: bool = Field(default=True, description="Run headless")
    parser_name: str = Field(..., description="Parser name for browser")
    stealth_warmup_enabled: bool = Field(default=False, description="Enable stealth warmup")
    
    # Proxy settings
    proxy_enabled: bool = Field(default=False, description="Enable proxy usage")
    proxy_url: Optional[str] = Field(default=None, description="Proxy URL (http://user:pass@host:port)")
    proxy_timeout: int = Field(default=30, description="Proxy timeout in seconds")


class BrowserManager(BaseManager):
    """Clean browser manager wrapper."""

    def __init__(self, config: BrowserManagerConfig):
        super().__init__(config, "browser")
        self.config: BrowserManagerConfig = config
        self.browser: Optional[CoreBrowserManager] = None

    async def _initialize(self) -> bool:
        """Initialize browser manager (but not the actual browser yet)."""
        try:
            # Don't initialize the actual browser here - do it lazily on first use
            # This prevents browser from starting in daemon mode until needed
            self.logger.info("Browser manager ready (browser will start on first use)")
            return True

        except Exception as e:
            self.logger.error(f"Browser manager initialization failed: {e}")
            return False

    async def _shutdown(self):
        """Shutdown browser."""
        if self.browser:
            await self.browser.close_async()
            self.browser = None

    async def _ensure_browser_initialized(self) -> bool:
        """Ensure browser is initialized (lazy initialization)."""
        if self.browser is not None:
            return True
            
        try:
            self.logger.info("🚀 Starting browser (lazy initialization)...")
            
            # Log proxy status
            if self.config.proxy_enabled and self.config.proxy_url:
                self.logger.info(f"🔒 Proxy enabled: {self.config.proxy_url}")
            else:
                self.logger.info("🌐 No proxy configured")
            
            # Create browser config with proper headless mode
            browser_mode = BrowserMode.HEADLESS if self.config.headless else BrowserMode.HEADED
            
            browser_config = BrowserConfig(
                parser_name=self.config.parser_name,
                mode=browser_mode,
                stealth_warmup_enabled=self.config.stealth_warmup_enabled
            )

            # Create browser manager with proxy support
            self.browser = CoreBrowserManager(browser_config)
            
            # Set proxy if enabled (we'll need to modify CoreBrowserManager to support this)
            if self.config.proxy_enabled and self.config.proxy_url:
                self.browser._proxy_url = self.config.proxy_url

            # Initialize browser
            await self.browser.initialize_async()
            
            self.logger.info("✅ Browser started successfully")
            return True

        except Exception as e:
            self.logger.error(f"❌ Browser initialization failed: {e}")
            self.browser = None
            return False

    async def navigate(self, url: str) -> bool:
        """Navigate to URL (with lazy browser initialization)."""
        # Ensure browser is initialized
        if not await self._ensure_browser_initialized():
            raise RuntimeError("Failed to initialize browser")

        try:
            await self.browser.navigate_async(url)
            self.stats.record_operation(True, 0.0)
            return True
        except Exception as e:
            self.logger.error(f"Navigation failed: {e}")
            self.stats.record_operation(False, 0.0)
            return False

    async def get_html(self) -> Optional[str]:
        """Get page HTML (with lazy browser initialization)."""
        # Ensure browser is initialized
        if not await self._ensure_browser_initialized():
            raise RuntimeError("Failed to initialize browser")

        try:
            html = await self.browser.get_page_content_async()
            self.stats.record_operation(True, 0.0)
            return html
        except Exception as e:
            self.logger.error(f"Get HTML failed: {e}")
            self.stats.record_operation(False, 0.0)
            return None
    
    async def execute_script_async(self, script: str) -> any:
        """Execute JavaScript on current page via ScriptManager."""
        # Ensure browser is initialized
        if not await self._ensure_browser_initialized():
            raise RuntimeError("Failed to initialize browser")
        
        try:
            # Use ScriptManager from CoreBrowserManager
            result = await self.browser.script_manager.execute_script(script)
            self.stats.record_operation(True, 0.0)
            return result
        except Exception as e:
            self.logger.error(f"Script execution failed: {e}")
            self.stats.record_operation(False, 0.0)
            raise
