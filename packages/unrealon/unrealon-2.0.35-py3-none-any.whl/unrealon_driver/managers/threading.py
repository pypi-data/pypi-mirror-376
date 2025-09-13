"""
Clean threading manager.
"""

import asyncio
import inspect
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Callable, Optional, Dict, Coroutine, Union
from pydantic import Field

from .base import BaseManager, ManagerConfig


class ThreadManagerConfig(ManagerConfig):
    """Thread manager configuration."""
    max_workers: int = Field(default=4, description="Max thread workers")


class ThreadManager(BaseManager):
    """Simple thread pool manager."""
    
    def __init__(self, config: ThreadManagerConfig):
        super().__init__(config, "threading")
        self.config: ThreadManagerConfig = config
        self.executor: Optional[ThreadPoolExecutor] = None
    
    async def _initialize(self) -> bool:
        """Initialize thread pool."""
        self.executor = ThreadPoolExecutor(
            max_workers=self.config.max_workers,
            thread_name_prefix="unrealon-driver"
        )
        return True
    
    async def _shutdown(self):
        """Shutdown thread pool."""
        if self.executor:
            self.executor.shutdown(wait=True)
            self.executor = None
    
    async def run_in_thread(self, func: Callable, *args, **kwargs) -> Any:
        """Run function in thread pool (supports both sync and async functions)."""
        if not self.executor:
            raise RuntimeError("Thread manager not initialized")
        
        # Check if function is async
        if inspect.iscoroutinefunction(func):
            # For async functions, we need to run them in a new event loop in the thread
            def run_async_in_thread():
                # Create new event loop for this thread
                new_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(new_loop)
                try:
                    return new_loop.run_until_complete(func(*args, **kwargs))
                finally:
                    new_loop.close()
            
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(self.executor, run_async_in_thread)
        else:
            # For sync functions, use normal executor
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(self.executor, func, *args, **kwargs)
    
    async def run_concurrent_async(self, async_funcs: list[Callable], max_concurrent: int = None) -> list[Any]:
        """
        Run multiple async functions concurrently using semaphore for control.
        
        This is more efficient than ThreadManager for pure async operations,
        but provides controlled concurrency.
        """
        if not async_funcs:
            return []
        
        # Use max_workers as default concurrency limit
        max_concurrent = max_concurrent or self.config.max_workers
        
        # Create semaphore to limit concurrency
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def run_with_semaphore(func):
            async with semaphore:
                return await func()
        
        # Execute all functions concurrently with semaphore control
        tasks = [run_with_semaphore(func) for func in async_funcs]
        return await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _health_check(self) -> Dict[str, Any]:
        """Thread manager health check."""
        return {
            "status": "ok",
            "max_workers": self.config.max_workers,
            "active": self.executor is not None
        }
