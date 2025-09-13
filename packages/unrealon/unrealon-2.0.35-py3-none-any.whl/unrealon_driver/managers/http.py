"""
Clean HTTP managers for requests - both aiohttp and httpx with HTTP/2 support.
"""

import asyncio
import aiohttp
import httpx
from typing import Dict, Any, Optional
from pydantic import Field

from .base import BaseManager, ManagerConfig


class HttpManagerConfig(ManagerConfig):
    """HTTP manager configuration."""
    user_agent: str = Field(default="UnrealOn-Driver/1.0", description="User agent string")
    max_connections: int = Field(default=100, description="Max concurrent connections")
    connector_limit: int = Field(default=30, description="Connector limit per host")


class HttpxManagerConfig(ManagerConfig):
    """HTTPx manager configuration with HTTP/2 support."""
    user_agent: str = Field(default="UnrealOn-Driver/1.0", description="User agent string")
    max_connections: int = Field(default=100, description="Max concurrent connections")
    connector_limit: int = Field(default=30, description="Connector limit per host")
    http2: bool = Field(default=True, description="Enable HTTP/2 support")


class HttpManager(BaseManager):
    """Clean HTTP manager with aiohttp (original)."""
    
    def __init__(self, config: HttpManagerConfig):
        super().__init__(config, "http")
        self.config: HttpManagerConfig = config
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def _initialize(self) -> bool:
        """Initialize HTTP session."""
        try:
            # Create connector
            connector = aiohttp.TCPConnector(
                limit=self.config.max_connections,
                limit_per_host=self.config.connector_limit,
                ttl_dns_cache=300,
                use_dns_cache=True
            )
            
            # Create session
            timeout = aiohttp.ClientTimeout(total=self.config.timeout)
            headers = {"User-Agent": self.config.user_agent}
            
            self.session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                headers=headers
            )
            
            return True
            
        except Exception as e:
            self.logger.error(f"HTTP manager initialization failed: {e}")
            return False
    
    async def _shutdown(self):
        """Shutdown HTTP session."""
        if self.session:
            await self.session.close()
            self.session = None
    
    async def get(self, url: str, **kwargs) -> aiohttp.ClientResponse:
        """Make GET request."""
        if not self.session:
            raise RuntimeError("HTTP manager not initialized")
        
        start_time = asyncio.get_event_loop().time()
        success = False
        
        try:
            response = await self.session.get(url, **kwargs)
            success = True
            return response
        finally:
            duration = asyncio.get_event_loop().time() - start_time
            self.stats.record_operation(success, duration)
    
    async def post(self, url: str, **kwargs) -> aiohttp.ClientResponse:
        """Make POST request."""
        if not self.session:
            raise RuntimeError("HTTP manager not initialized")
        
        start_time = asyncio.get_event_loop().time()
        success = False
        
        try:
            response = await self.session.post(url, **kwargs)
            success = True
            return response
        finally:
            duration = asyncio.get_event_loop().time() - start_time
            self.stats.record_operation(success, duration)
    
    async def request(self, method: str, url: str, **kwargs) -> aiohttp.ClientResponse:
        """Make generic request."""
        if not self.session:
            raise RuntimeError("HTTP manager not initialized")
        
        start_time = asyncio.get_event_loop().time()
        success = False
        
        try:
            response = await self.session.request(method, url, **kwargs)
            success = True
            return response
        finally:
            duration = asyncio.get_event_loop().time() - start_time
            self.stats.record_operation(success, duration)


class HttpxManager(BaseManager):
    """Modern HTTP manager with httpx and HTTP/2 support."""
    
    def __init__(self, config: HttpxManagerConfig):
        super().__init__(config, "httpx")
        self.config: HttpxManagerConfig = config
        self.client: Optional[httpx.AsyncClient] = None
    
    async def _initialize(self) -> bool:
        """Initialize HTTP client with HTTP/2 support."""
        try:
            # Create limits
            limits = httpx.Limits(
                max_keepalive_connections=self.config.max_connections,
                max_connections=self.config.max_connections,
                keepalive_expiry=300
            )
            
            # Create timeout
            timeout = httpx.Timeout(self.config.timeout)
            
            # Default headers
            headers = {"User-Agent": self.config.user_agent}
            
            # Create client with HTTP/2 support
            self.client = httpx.AsyncClient(
                limits=limits,
                timeout=timeout,
                headers=headers,
                http2=self.config.http2,
                verify=True,
                follow_redirects=True
            )
            
            return True
            
        except Exception as e:
            self.logger.error(f"HTTPx manager initialization failed: {e}")
            return False
    
    async def _shutdown(self):
        """Shutdown HTTP client."""
        if self.client:
            await self.client.aclose()
            self.client = None
    
    async def get(self, url: str, **kwargs) -> httpx.Response:
        """Make GET request."""
        if not self.client:
            raise RuntimeError("HTTPx manager not initialized")
        
        start_time = asyncio.get_event_loop().time()
        success = False
        
        try:
            response = await self.client.get(url, **kwargs)
            success = True
            return response
        finally:
            duration = asyncio.get_event_loop().time() - start_time
            self.stats.record_operation(success, duration)
    
    async def post(self, url: str, **kwargs) -> httpx.Response:
        """Make POST request."""
        if not self.client:
            raise RuntimeError("HTTPx manager not initialized")
        
        start_time = asyncio.get_event_loop().time()
        success = False
        
        try:
            response = await self.client.post(url, **kwargs)
            success = True
            return response
        finally:
            duration = asyncio.get_event_loop().time() - start_time
            self.stats.record_operation(success, duration)
    
    async def request(self, method: str, url: str, **kwargs) -> httpx.Response:
        """Make generic request."""
        if not self.client:
            raise RuntimeError("HTTPx manager not initialized")
        
        start_time = asyncio.get_event_loop().time()
        success = False
        
        try:
            response = await self.client.request(method, url, **kwargs)
            success = True
            return response
        finally:
            duration = asyncio.get_event_loop().time() - start_time
            self.stats.record_operation(success, duration)
