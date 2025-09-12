"""
Browser Manager - Core orchestrator for browser automation
Layer 0: Foundation - Basic browser lifecycle management
"""

import asyncio
import signal
import sys
import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any, Union
from pathlib import Path
import subprocess
import platform
from playwright.async_api import async_playwright
from unrealon_browser.dto import (
    BrowserConfig,
    BrowserSession,
    BrowserSessionStatus,
    BrowserStatistics,
    BrowserManagerStatistics,
    BrowserType,
    PageResult,
    ProxyInfo,
)
from unrealon_browser.managers import (
    StealthManager,
    ProfileManager,
    CookieManager,
    CaptchaDetector,
    create_browser_logger_bridge,
    PageWaitManager,
    ScriptManager,
)


class BrowserManager:
    """
    Core browser automation orchestrator

    Layer 0: Foundation - Basic browser lifecycle management
    - Browser initialization and cleanup
    - Session metadata tracking
    - Signal handling for graceful shutdown
    - Basic statistics
    """

    def __init__(self, config: BrowserConfig, parser_id: Optional[str] = None):
        """Initialize browser manager with configuration"""
        self.config = config
        self.parser_id = parser_id or config.parser_id or config.parser_name
        self.session_metadata: Optional[BrowserSession] = None
        self._browser = None
        self._context = None
        self._page = None
        self._initialized = False
        self._statistics = BrowserManagerStatistics()
        
        # Proxy settings (can be set externally)
        self._proxy_url: Optional[str] = None

        # Initialize logger bridge first
        self.logger_bridge = create_browser_logger_bridge(session_id=self._generate_session_id(), parser_id=self.parser_id, enable_console=True)  # Use resolved parser_id
        
        # Initialize managers
        self.stealth_manager = StealthManager(logger_bridge=self.logger_bridge)
        # ✅ FIX: Don't create default managers here - they will be set by Browser service
        # This prevents duplicate directory creation with wrong paths
        self.profile_manager = None
        self.cookie_manager = None
        self.captcha_manager = CaptchaDetector()
        self.page_wait = PageWaitManager(None, self.logger_bridge)
        self.script_manager = ScriptManager(None, self.logger_bridge)

        # Signal handlers for graceful shutdown
        self._setup_signal_handlers()

    def _setup_signal_handlers(self) -> None:
        """Setup signal handlers for graceful shutdown"""

        def signal_handler(signum, frame):
            self.logger_bridge.log_info(f"\n🔄 Received signal {signum}, shutting down gracefully...")
            if self._initialized:
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        # Schedule cleanup and set a timer to force exit if it takes too long
                        task = loop.create_task(self._force_cleanup_with_timeout())
                        return
                    else:
                        # If no event loop running, use asyncio.run
                        asyncio.run(self.close_async())
                except Exception as e:
                    self.logger_bridge.log_warning(f"⚠️ Error during shutdown: {e}")
            self.logger_bridge.log_info("🔄 Browser cleanup completed")
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

    async def _force_cleanup_with_timeout(self):
        """Cleanup with timeout to prevent hanging."""
        try:
            # Try graceful cleanup with timeout
            await asyncio.wait_for(self.close_async(), timeout=3.0)
        except asyncio.TimeoutError:
            self.logger_bridge.log_warning("⚠️ Cleanup timeout - forcing exit")
        except Exception as e:
            self.logger_bridge.log_warning(f"⚠️ Cleanup error: {e}")
        finally:
            self.logger_bridge.log_info("🔄 Browser cleanup completed")
            # Force exit from the event loop
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    loop.stop()
            except Exception:
                pass
            import os

            os._exit(0)

    def _generate_session_id(self) -> str:
        """Generate unique session ID"""
        return f"browser_session_{uuid.uuid4().hex[:8]}"

    async def _force_cleanup_chromium_processes(self) -> None:
        """Force cleanup of any remaining Chromium processes."""
        try:

            if platform.system() == "Darwin":  # macOS
                # Kill playwright chromium processes
                subprocess.run(["pkill", "-f", "playwright.*chromium"], capture_output=True, check=False)

            elif platform.system() == "Linux":
                # Kill playwright chromium processes on Linux
                subprocess.run(["pkill", "-f", "playwright.*chromium"], capture_output=True, check=False)

            elif platform.system() == "Windows":
                # Kill chromium processes on Windows
                subprocess.run(["taskkill", "/F", "/IM", "chrome.exe"], capture_output=True, check=False)
                subprocess.run(["taskkill", "/F", "/IM", "chromium.exe"], capture_output=True, check=False)

        except Exception as e:
            self.logger_bridge.log_warning(f"⚠️ Could not force cleanup Chromium processes: {e}")
            # Don't raise - this is a best-effort cleanup

    async def initialize_async(self) -> None:
        """Initialize browser with Playwright"""
        if self._initialized:
            return

        try:

            # Create session metadata
            self.session_metadata = BrowserSession(
                session_id=self._generate_session_id(),
                parser_name=self.config.parser_name,
                proxy=None,
                profile_path="",
                created_at=datetime.now(timezone.utc),
                is_active=True,
                page_count=0,
                browser_type=self.config.browser_type.value,
            )

            self.logger_bridge.log_info(f"🚀 Initializing browser session: {self.session_metadata.session_id}")
            self.logger_bridge.log_info(f"   Parser: {self.config.parser_name}")
            self.logger_bridge.log_info(f"   Browser: {self.config.browser_type.value}")
            self.logger_bridge.log_info(f"   Stealth: ALWAYS ON")

            # Log initialization through bridge
            self.logger_bridge.log_browser_initialized(self.session_metadata)

            # Start Playwright
            self._playwright = await async_playwright().start()

            # Create or get profile BEFORE launching browser (needed for user_data_dir)
            profile_path = None
            if self.profile_manager:
                profile_path = self.profile_manager.create_profile(
                    parser_name=self.config.parser_name,
                    proxy_info=None,  # TODO: Add proxy integration
                )

            # Launch browser based on type with profile
            browser_args = self._get_browser_args()
            context_options = self._get_context_options()

            # ✅ FIX: Use launch_persistent_context for profiles, regular launch otherwise
            if profile_path:
                self.logger_bridge.log_info(f"   📂 Using profile: {profile_path}")

                # Combine args for persistent context (different structure than regular launch)
                persistent_args = {
                    "user_data_dir": str(profile_path),
                    "headless": browser_args.get("headless", True),
                    "args": browser_args.get("args", []),
                    # 🔥 CRITICAL: Remove automation flag like old unrealparser!
                    "ignore_default_args": ["--enable-automation"],
                    **context_options,  # viewport, user_agent, etc.
                }
                
                # Add proxy configuration for persistent context
                if self._proxy_url:
                    proxy_config = self._get_playwright_proxy_config()
                    if proxy_config:
                        persistent_args["proxy"] = proxy_config

                # Use persistent context with user_data_dir for profiles
                if self.config.browser_type == BrowserType.CHROMIUM:
                    self._context = await self._playwright.chromium.launch_persistent_context(**persistent_args)
                elif self.config.browser_type == BrowserType.FIREFOX:
                    self._context = await self._playwright.firefox.launch_persistent_context(**persistent_args)
                elif self.config.browser_type == BrowserType.WEBKIT:
                    self._context = await self._playwright.webkit.launch_persistent_context(**persistent_args)
                else:
                    raise ValueError(f"Unsupported browser type: {self.config.browser_type}")

                # For persistent context, browser is accessed via context.browser
                self._browser = self._context.browser
                self.logger_bridge.log_info(f"✅ Persistent context created with profile: {profile_path}")
            else:
                # Regular browser launch without profile
                if self.config.browser_type == BrowserType.CHROMIUM:
                    self._browser = await self._playwright.chromium.launch(**browser_args)
                elif self.config.browser_type == BrowserType.FIREFOX:
                    self._browser = await self._playwright.firefox.launch(**browser_args)
                elif self.config.browser_type == BrowserType.WEBKIT:
                    self._browser = await self._playwright.webkit.launch(**browser_args)
                else:
                    raise ValueError(f"Unsupported browser type: {self.config.browser_type}")

                # Create context without profile
                # Add proxy configuration for context
                if self._proxy_url:
                    proxy_config = self._get_playwright_proxy_config()
                    if proxy_config:
                        context_options["proxy"] = proxy_config
                
                self._context = await self._browser.new_context(**context_options)

            # 🔥 STEALTH ALWAYS ON - NO CONFIG NEEDED!
            await self.stealth_manager.apply_webdriver_removal(self._context)

            # Create page
            self._page = await self._context.new_page()

            # Update page wait manager with new page
            self.page_wait.update_page(self._page)
            
            # Update script manager with new page
            self.script_manager.update_page(self._page)

            # 🔥 STEALTH ALWAYS APPLIED TO EVERY PAGE!
            stealth_success = await self.stealth_manager.apply_stealth(self._page)
            self.logger_bridge.log_stealth_applied(stealth_success)

            # 🔥 CRITICAL: If stealth fails, CLOSE BROWSER WITH ERROR!
            if not stealth_success:
                self.logger_bridge.log_error("❌ STEALTH FAILED - CLOSING BROWSER!")
                await self.close_async()
                raise RuntimeError("🔥 STEALTH MANDATORY: Browser closed due to stealth application failure")

            # Update session status
            self.session_metadata.current_status = BrowserSessionStatus.ACTIVE
            self._statistics.set_session_start()
            self._initialized = True

            self.logger_bridge.log_info(f"✅ Browser initialized successfully")
            self.logger_bridge.log_info(f"   Session ID: {self.session_metadata.session_id}")

        except Exception as e:
            if self.session_metadata:
                self.session_metadata.current_status = BrowserSessionStatus.ERROR
            self.logger_bridge.log_error(f"❌ Failed to initialize browser: {e}")
            raise

    def _get_browser_args(self) -> Dict[str, Any]:
        """Get browser launch arguments"""
        args = {
            "headless": self.config.mode.value == "headless",
        }

        # Add basic browser arguments
        browser_args = [
            "--no-first-run",
            "--no-default-browser-check",
        ]

        # 🔥 STEALTH ALWAYS ON - ALWAYS ADD STEALTH ARGS!
        browser_args.extend(self.stealth_manager.get_stealth_args())

        # Note: Proxy configuration is now handled via Playwright API in context options
        # instead of command line arguments for better compatibility

        if self.config.disable_images:
            browser_args.extend(
                [
                    "--blink-settings=imagesEnabled=false",
                    "--disable-images",
                ]
            )

        args["args"] = browser_args
        return args
    
    def _get_playwright_proxy_config(self) -> Optional[Dict[str, Any]]:
        """
        Get Playwright-compatible proxy configuration.
        
        Returns:
            Proxy configuration dict for Playwright or None if not supported
        """
        if not self._proxy_url:
            return None
            
        try:
            from urllib.parse import urlparse
            
            parsed = urlparse(self._proxy_url)
            
            # Playwright proxy configuration
            proxy_config = {
                "server": f"{parsed.scheme}://{parsed.hostname}:{parsed.port}"
            }
            
            # Add authentication if present
            if parsed.username and parsed.password:
                # WARNING: Playwright does NOT support SOCKS5 authentication!
                if parsed.scheme == 'socks5':
                    self.logger_bridge.log_warning("⚠️ Playwright does not support SOCKS5 authentication!")
                    self.logger_bridge.log_warning("⚠️ Falling back to SOCKS5 without auth - may fail!")
                    # Return configuration without authentication for SOCKS5
                    return proxy_config
                else:
                    # HTTP/HTTPS proxies support authentication
                    proxy_config["username"] = parsed.username
                    proxy_config["password"] = parsed.password
            
            self.logger_bridge.log_info(f"🔒 Playwright proxy config: {proxy_config['server']}")
            return proxy_config
            
        except Exception as e:
            self.logger_bridge.log_error(f"❌ Failed to parse proxy URL: {e}")
            return None

    def _get_context_options(self) -> Dict[str, Any]:
        """Get browser context options"""
        options = {
            "viewport": {
                "width": 1920,  # Default viewport
                "height": 1080,
            },
        }

        # Note: user_agent can be set later if needed
        # options["user_agent"] = "custom_user_agent"

        return options

    async def navigate_async(self, url: str, wait_for: Optional[str] = None) -> Dict[str, Any]:
        """Navigate to URL with stealth retry logic"""
        # Always use stealth retry logic
        return await self._navigate_with_stealth_retry(url, wait_for)

    async def _navigate_with_stealth_retry(self, url: str, wait_for: Optional[str] = None) -> Dict[str, Any]:
        """Navigate with stealth retry logic - universal for all sites"""
        self.logger_bridge.log_info(f"🥷 Stealth navigation to: {url}")

        # Stealth warmup if enabled
        if self.config.stealth_warmup_enabled:
            self.logger_bridge.log_info(f"🧪 First visiting stealth test page: {self.config.stealth_test_url}")
            await self._navigate_basic(self.config.stealth_test_url, None)
            self.logger_bridge.log_info(f"⏳ Waiting {self.config.stealth_warmup_delay} seconds for stealth establishment...")
            await asyncio.sleep(self.config.stealth_warmup_delay)

        # Now navigate to the actual target URL with retry logic
        max_retries = self.config.stealth_retry_attempts
        for attempt in range(max_retries + 1):
            if attempt > 0:
                self.logger_bridge.log_info(f"🔄 Stealth retry attempt {attempt}/{max_retries}")
                await asyncio.sleep(self.config.stealth_retry_delay)

            result = await self._navigate_basic(url, wait_for)

            # If successful, return result
            if result["success"]:
                if attempt > 0:
                    self.logger_bridge.log_info(f"✅ Stealth retry successful on attempt {attempt + 1}")
                return result

            # If failed and we have retries left, continue
            if attempt < max_retries:
                self.logger_bridge.log_info(f"⚠️ Navigation failed, will retry in {self.config.stealth_retry_delay} seconds...")
                continue

        # All retries failed
        self.logger_bridge.log_warning(f"❌ Stealth navigation failed after {max_retries + 1} attempts")
        return result

    async def _navigate_basic(self, url: str, wait_for: Optional[str] = None) -> Dict[str, Any]:
        """Basic navigation without retry logic"""
        if not self._initialized or not self._page:
            raise RuntimeError("Browser not initialized. Call initialize_async() first.")

        self._statistics.increment_total()

        try:
            self.logger_bridge.log_info(f"🌐 Navigating to: {url}")

            # Navigate with timeout
            response = await self._page.goto(
                url,
                timeout=self.config.page_load_timeout_seconds * 1000,
                wait_until="domcontentloaded",
            )

            # Wait for additional selector if specified
            if wait_for:
                self.logger_bridge.log_info(f"⏳ Waiting for: {wait_for}")
                await self._page.wait_for_selector(wait_for, timeout=self.config.page_load_timeout_seconds * 1000)

            # Check response status
            if response and response.status >= 400:
                raise Exception(f"HTTP {response.status}: {response.status_text}")

            self._statistics.increment_successful()

            # Mark profile session as success
            if self.profile_manager:
                self.profile_manager.mark_session_success(True)

            # Calculate duration
            duration_ms = (datetime.now(timezone.utc) - datetime.now(timezone.utc).replace(microsecond=0)).total_seconds() * 1000

            # Log successful navigation
            title = await self._page.title()
            self.logger_bridge.log_navigation_success(self._page.url, title, duration_ms)

            # Check for captcha after navigation (TEMPORARILY DISABLED FOR DEBUGGING)
            # captcha_result = await self.captcha_manager.detect_captcha(self._page)
            # if captcha_result.detected:
            #     self.logger_bridge.log_captcha_detected(captcha_result)
            #     self.logger_bridge.log_warning(f"⚠️ Captcha detected: {captcha_result.captcha_type.value}")
            #     # Update session status to indicate captcha is required
            #     self.session_metadata.current_status = BrowserSessionStatus.CAPTCHA_REQUIRED

            return {
                "success": True,
                "url": self._page.url,
                "title": title,
                "status": response.status if response else 200,
                "error": None,
            }

        except Exception as e:
            self._statistics.increment_failed()
            self.logger_bridge.log_error(f"❌ Navigation failed: {e}")

            # Mark profile session as failure
            if self.profile_manager:
                self.profile_manager.mark_session_success(False)

            # Calculate duration
            duration_ms = (datetime.now(timezone.utc) - datetime.now(timezone.utc).replace(microsecond=0)).total_seconds() * 1000

            # Log failed navigation
            self.logger_bridge.log_navigation_failed(url, str(e), duration_ms)

            return {
                "success": False,
                "url": url,
                "title": None,
                "status": 0,
                "error": str(e),
            }

    async def get_page_content_async(self) -> Optional[str]:
        """Get current page content"""
        if not self._page:
            return None

        try:
            return await self._page.content()
        except Exception as e:
            self.logger_bridge.log_error(f"❌ Failed to get page content: {e}")
            return None

    async def execute_script_async(self, script: str) -> Any:
        """Execute JavaScript on current page"""
        if not self._page:
            raise RuntimeError("No page available")

        try:
            return await self._page.evaluate(script)
        except Exception as e:
            self.logger_bridge.log_error(f"❌ Script execution failed: {e}")
            raise

    def get_statistics(self) -> Dict[str, Any]:
        """Get browser session statistics"""
        # Convert Pydantic model to dict with computed values
        stats_dict = self._statistics.model_dump()

        if self._statistics.session_start_time:
            current_time = datetime.now(timezone.utc)
            stats_dict["session_duration_seconds"] = (current_time - self._statistics.session_start_time).total_seconds()

        if self._statistics.total_navigations > 0:
            stats_dict["success_rate"] = self._statistics.successful_navigations / self._statistics.total_navigations
        else:
            stats_dict["success_rate"] = 0.0

        return stats_dict

    def print_statistics(self) -> None:
        """Print session statistics"""
        stats = self.get_statistics()

        self.logger_bridge.log_info("\n📊 Browser Session Statistics:")
        self.logger_bridge.log_info(f"   Session ID: {self.session_metadata.session_id if self.session_metadata else 'N/A'}")
        self.logger_bridge.log_info(f"   Total navigations: {stats['total_navigations']}")
        self.logger_bridge.log_info(f"   Successful: {stats['successful_navigations']}")
        self.logger_bridge.log_info(f"   Failed: {stats['failed_navigations']}")
        self.logger_bridge.log_info(f"   Success rate: {stats['success_rate']:.1%}")
        self.logger_bridge.log_info(f"   Duration: {stats['session_duration_seconds']:.1f}s")

        # Print stealth status
        self.stealth_manager.print_stealth_status()

        # Print profile status
        if self.profile_manager:
            self.profile_manager.print_profile_statistics()

        # Print cookie manager statistics
        if self.cookie_manager:
            self.cookie_manager.print_statistics()

        # Print captcha manager statistics
        self.captcha_manager.print_statistics()

        # Print logger bridge statistics
        self.logger_bridge.print_statistics()

    async def test_stealth_async(self) -> Dict[str, Any]:
        """Test stealth effectiveness on detection service"""
        self.logger_bridge.log_info("🔍 DEBUG: test_stealth_async called")
        self.logger_bridge.log_info(f"🔍 DEBUG: stealth_manager={self.stealth_manager}")
        try:
            self.logger_bridge.log_info("🔍 DEBUG: About to call stealth_manager.test_stealth_effectiveness")
            result = await self.stealth_manager.test_stealth_effectiveness(self)
            self.logger_bridge.log_info(f"🔍 DEBUG: stealth_manager.test_stealth_effectiveness returned: {result}")
            return result
        except Exception as e:
            self.logger_bridge.log_error(f"❌ DEBUG: Exception in test_stealth_async: {e}")
            import traceback
            self.logger_bridge.log_error(f"❌ DEBUG: Traceback: {traceback.format_exc()}")
            return {
                "success": False,
                "error": str(e),
                "skipped": False,
            }

    async def detect_captcha_async(self) -> Dict[str, Any]:
        """Detect captcha on current page"""
        if not self._page:
            return {"captcha_detected": False, "error": "No page available"}

        try:
            detection_result = await self.captcha_manager.detect_captcha(self._page)

            if detection_result.detected:
                self.logger_bridge.log_captcha_detected(detection_result)
                # Update session status
                self.session_metadata.current_status = BrowserSessionStatus.CAPTCHA_REQUIRED

            return {
                "captcha_detected": detection_result.detected,
                "captcha_type": detection_result.captcha_type.value,
                "page_url": detection_result.page_url,
                "detected_at": detection_result.detected_at.isoformat(),
            }

        except Exception as e:
            return {"captcha_detected": False, "error": str(e)}

    async def handle_captcha_interactive_async(self, timeout_seconds: int = 300) -> Dict[str, Any]:
        """Handle captcha through interactive manual resolution"""
        if not self._page:
            return {"success": False, "error": "No page available"}

        try:
            # First detect captcha
            detection_result = await self.captcha_manager.detect_captcha(self._page)

            if not detection_result.detected:
                return {"success": False, "error": "No captcha detected", "should_continue": True}

            self.logger_bridge.log_info(f"\n🤖 Starting interactive captcha resolution...")

            # Handle captcha interactively
            resolution_result = await self.captcha_manager.handle_captcha_interactive(self, detection_result, timeout_seconds)

            if resolution_result["success"]:
                # Log successful captcha resolution
                if hasattr(self, "_current_proxy") and self._current_proxy:
                    proxy_host = self._current_proxy.get("host", "unknown")
                    proxy_port = self._current_proxy.get("port", 0)
                    self.logger_bridge.log_captcha_solved(proxy_host, proxy_port, manual=True)

                # Update session status back to active
                self.session_metadata.current_status = BrowserSessionStatus.ACTIVE

            return resolution_result

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def full_automation_workflow_async(self, url: str) -> Dict[str, Any]:
        """
        Complete automation workflow with captcha handling

        Args:
            url: URL to navigate to

        Returns:
            Workflow result with status and details
        """
        workflow_result = {
            "success": False,
            "url": url,
            "steps_completed": [],
            "captcha_encountered": False,
            "captcha_resolved": False,
            "cookies_saved": False,
            "error": None,
        }

        try:
            # Step 1: Navigate to URL
            self.logger_bridge.log_info(f"🚀 Starting automation workflow for: {url}")
            navigation_result = await self.navigate_async(url)
            workflow_result["steps_completed"].append("navigation")

            if not navigation_result["success"]:
                workflow_result["error"] = f"Navigation failed: {navigation_result.get('error')}"
                return workflow_result

            # Step 2: Check for captcha
            captcha_result = await self.detect_captcha_async()
            if captcha_result["captcha_detected"]:
                workflow_result["captcha_encountered"] = True
                workflow_result["steps_completed"].append("captcha_detection")

                self.logger_bridge.log_info(f"🤖 Captcha detected: {captcha_result['captcha_type']}")

                # Step 3: Handle captcha interactively
                resolution_result = await self.handle_captcha_interactive_async(timeout_seconds=300)
                workflow_result["steps_completed"].append("captcha_handling")

                if resolution_result["success"]:
                    workflow_result["captcha_resolved"] = True
                    self.logger_bridge.log_info("✅ Captcha resolved successfully!")
                else:
                    workflow_result["error"] = f"Captcha resolution failed: {resolution_result.get('error')}"
                    return workflow_result

            # Step 4: Save cookies if we have a proxy
            if hasattr(self, "_current_proxy") and self._current_proxy:
                cookies_saved = await self.save_cookies_for_current_proxy_async()
                workflow_result["cookies_saved"] = cookies_saved
                workflow_result["steps_completed"].append("cookie_saving")

                if cookies_saved:
                    self.logger_bridge.log_info("💾 Cookies saved successfully!")

            workflow_result["success"] = True
            self.logger_bridge.log_info("🎉 Automation workflow completed successfully!")

            return workflow_result

        except Exception as e:
            workflow_result["error"] = str(e)
            self.logger_bridge.log_error(f"❌ Automation workflow failed: {e}")
            return workflow_result

    async def close_async(self) -> None:
        """Close browser and cleanup resources"""

        if not self._initialized:
            return

        try:
            self.logger_bridge.log_info("🔄 Closing browser session...")

            if self.session_metadata:
                self.session_metadata.current_status = BrowserSessionStatus.CLOSED

            # Close page with safety checks
            if self._page:
                try:
                    if not self._page.is_closed():
                        await self._page.close()
                except Exception as e:
                    self.logger_bridge.log_warning(f"⚠️ Page already closed: {e}")
                finally:
                    self._page = None
                    self.page_wait.update_page(None)
                    self.script_manager.update_page(None)

            # Close context with safety checks
            if self._context:
                try:
                    # Check if context is still valid before closing
                    await self._context.close()
                except Exception as e:
                    self.logger_bridge.log_warning(f"⚠️ Context already closed: {e}")
                finally:
                    self._context = None

            # Close browser with safety checks
            if self._browser:
                try:
                    if self._browser.is_connected():
                        await self._browser.close()
                except Exception as e:
                    self.logger_bridge.log_warning(f"⚠️ Browser already closed: {e}")
                finally:
                    self._browser = None

            # Stop playwright
            if hasattr(self, "_playwright") and self._playwright:
                try:
                    await self._playwright.stop()
                except Exception as e:
                    self.logger_bridge.log_warning(f"⚠️ Playwright already stopped: {e}")
                finally:
                    self._playwright = None

            # Force cleanup of any remaining Chromium processes
            await self._force_cleanup_chromium_processes()

            self._initialized = False

            # Log final statistics
            self.print_statistics()
            self.logger_bridge.log_info("✅ Browser closed successfully")

        except Exception as e:
            self.logger_bridge.log_error(f"❌ Error closing browser: {e}")
            # Don't re-raise - we want graceful shutdown even with errors

    @property
    def page(self):
        """Get current page (for advanced usage)"""
        return self._page

    @property
    def context(self):
        """Get current context (for advanced usage)"""
        return self._context

    @property
    def browser(self):
        """Get current browser (for advanced usage)"""
        return self._browser

    @property
    def is_initialized(self) -> bool:
        """Check if browser is initialized"""
        return self._initialized
