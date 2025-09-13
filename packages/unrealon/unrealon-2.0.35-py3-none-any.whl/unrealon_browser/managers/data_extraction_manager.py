"""
Data Extraction Manager - Extract different types of data from pages
"""
import json
from typing import Optional, Dict, Any, Union
from playwright.async_api import Page

from .logger_bridge import BrowserLoggerBridge as LoggingBridge


class DataExtractionManager:
    """Manager for extracting different types of data from web pages"""
    
    def __init__(self, page: Optional[Page], logger_bridge: LoggingBridge):
        self._page = page
        self.logger_bridge = logger_bridge
    
    def update_page(self, page: Optional[Page]):
        """Update the page reference"""
        self._page = page
    
    async def get_json_content(self) -> Optional[Dict[str, Any]]:
        """Extract JSON content from current page (for API endpoints)."""
        if not self._page:
            self.logger_bridge.log_error("No page available for JSON extraction")
            return None
        
        try:
            self.logger_bridge.log_info("🔍 Extracting JSON content from page...")
            
            # JavaScript to extract JSON from different page formats
            script = """
            (() => {
                try {
                    // Method 1: Try to get from document.body.textContent (for API responses)
                    const bodyText = document.body.textContent || document.body.innerText || '';
                    const cleanBodyText = bodyText.trim();
                    
                    if (cleanBodyText && (cleanBodyText.startsWith('{') || cleanBodyText.startsWith('['))) {
                        return {
                            success: true,
                            data: JSON.parse(cleanBodyText),
                            method: 'body_text'
                        };
                    }
                    
                    // Method 2: Try to get from <pre> tag (common for JSON APIs)
                    const preElement = document.querySelector('pre');
                    if (preElement) {
                        const preText = (preElement.textContent || preElement.innerText || '').trim();
                        if (preText && (preText.startsWith('{') || preText.startsWith('['))) {
                            return {
                                success: true,
                                data: JSON.parse(preText),
                                method: 'pre_element'
                            };
                        }
                    }
                    
                    // Method 3: Check if entire document is JSON
                    const docText = (document.documentElement.textContent || document.documentElement.innerText || '').trim();
                    if (docText && (docText.startsWith('{') || docText.startsWith('['))) {
                        return {
                            success: true,
                            data: JSON.parse(docText),
                            method: 'document_text'
                        };
                    }
                    
                    // Method 4: Look for JSON in script tags
                    const scriptTags = document.querySelectorAll('script[type="application/json"]');
                    for (const script of scriptTags) {
                        const scriptText = (script.textContent || script.innerText || '').trim();
                        if (scriptText && (scriptText.startsWith('{') || scriptText.startsWith('['))) {
                            return {
                                success: true,
                                data: JSON.parse(scriptText),
                                method: 'script_tag'
                            };
                        }
                    }
                    
                    return {
                        success: false,
                        error: 'No JSON content found',
                        page_text_preview: cleanBodyText.substring(0, 200)
                    };
                    
                } catch (e) {
                    return {
                        success: false,
                        error: 'JSON parse failed: ' + e.message,
                        page_text_preview: (document.body.textContent || '').substring(0, 200)
                    };
                }
            })();
            """
            
            result = await self._page.evaluate(script)
            
            if result.get('success'):
                method = result.get('method', 'unknown')
                self.logger_bridge.log_info(f"✅ JSON extracted successfully using method: {method}")
                return result.get('data')
            else:
                error = result.get('error', 'Unknown error')
                preview = result.get('page_text_preview', '')
                self.logger_bridge.log_warning(f"❌ JSON extraction failed: {error}")
                if preview:
                    self.logger_bridge.log_info(f"📄 Page preview: {preview}...")
                return None
                
        except Exception as e:
            self.logger_bridge.log_error(f"JSON extraction error: {e}")
            return None
    
    async def get_page_text(self) -> Optional[str]:
        """Get plain text content from current page."""
        if not self._page:
            return None
        
        try:
            self.logger_bridge.log_info("📄 Extracting plain text content...")
            
            script = """
            (() => {
                return {
                    body_text: document.body.textContent || document.body.innerText || '',
                    title: document.title || '',
                    url: window.location.href
                };
            })();
            """
            
            result = await self._page.evaluate(script)
            text = result.get('body_text', '').strip()
            
            if text:
                self.logger_bridge.log_info(f"✅ Text extracted: {len(text)} characters")
                return text
            else:
                self.logger_bridge.log_warning("❌ No text content found")
                return None
                
        except Exception as e:
            self.logger_bridge.log_error(f"Text extraction error: {e}")
            return None
    
    async def get_structured_data(self) -> Optional[Dict[str, Any]]:
        """Get structured data including JSON, text, and metadata."""
        if not self._page:
            return None
        
        try:
            self.logger_bridge.log_info("🔍 Extracting structured data...")
            
            # Try JSON first
            json_data = await self.get_json_content()
            
            # Get page metadata
            script = """
            (() => {
                return {
                    url: window.location.href,
                    title: document.title || '',
                    content_type: document.contentType || '',
                    charset: document.characterSet || '',
                    ready_state: document.readyState,
                    has_pre_element: !!document.querySelector('pre'),
                    body_text_length: (document.body.textContent || '').length
                };
            })();
            """
            
            metadata = await self._page.evaluate(script)
            
            result = {
                "extraction_success": json_data is not None,
                "json_data": json_data,
                "metadata": metadata,
                "extracted_at": self._get_timestamp()
            }
            
            if json_data:
                self.logger_bridge.log_info("✅ Structured data extraction successful")
            else:
                self.logger_bridge.log_warning("⚠️ No JSON data found, but metadata extracted")
            
            return result
            
        except Exception as e:
            self.logger_bridge.log_error(f"Structured data extraction error: {e}")
            return None
    
    async def detect_content_type(self) -> str:
        """Detect the type of content on the current page."""
        if not self._page:
            return "unknown"
        
        try:
            script = """
            (() => {
                const bodyText = (document.body.textContent || '').trim();
                const contentType = document.contentType || '';
                const hasPreElement = !!document.querySelector('pre');
                
                // Check for JSON
                if (bodyText.startsWith('{') || bodyText.startsWith('[')) {
                    return 'json';
                }
                
                // Check for XML
                if (bodyText.startsWith('<') && contentType.includes('xml')) {
                    return 'xml';
                }
                
                // Check for HTML
                if (document.querySelector('html') && document.querySelector('body') && !hasPreElement) {
                    return 'html';
                }
                
                // Check for plain text
                if (hasPreElement || contentType.includes('text/plain')) {
                    return 'text';
                }
                
                return 'unknown';
            })();
            """
            
            content_type = await self._page.evaluate(script)
            self.logger_bridge.log_info(f"🔍 Detected content type: {content_type}")
            return content_type
            
        except Exception as e:
            self.logger_bridge.log_error(f"Content type detection error: {e}")
            return "unknown"
    
    async def get_page_html(self) -> Optional[str]:
        """Get full HTML content from current page."""
        if not self._page:
            return None
        
        try:
            self.logger_bridge.log_info("📄 Extracting HTML content...")
            html = await self._page.content()
            
            if html:
                self.logger_bridge.log_info(f"✅ HTML extracted: {len(html)} characters")
                return html
            else:
                self.logger_bridge.log_warning("❌ No HTML content found")
                return None
                
        except Exception as e:
            self.logger_bridge.log_error(f"HTML extraction error: {e}")
            return None
    
    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format."""
        from datetime import datetime
        return datetime.now().isoformat()


# Export
__all__ = ["DataExtractionManager"]
