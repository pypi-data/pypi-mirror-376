"""PreCallable tool related classes and utilities for architect_ai package."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Union, List
from enum import Enum
import asyncio
import concurrent.futures
import threading

from .exceptions.tool_exceptions import (
    PrecallableToolNotFoundError,
    PrecallableToolExecutionError,
    PrecallableToolRuntimeError,
)


class ExecutionMode(Enum):
    """Defines how a tool should be executed for optimal performance."""
    ASYNC = "async"     
    THREAD = "thread"    
    PROCESS = "process"  


class PicklablePrecallableResults:
    """Simple, picklable container for resolved precallable results."""
    
    def __init__(self, resolved_results: Dict[str, Any]):
        self._results = resolved_results
    
    def get_sync(self, tool_name: str) -> Any:
        """Get resolved result synchronously."""
        if tool_name not in self._results:
            raise PrecallableToolNotFoundError(tool_name)
        return self._results[tool_name]
    
    async def get(self, tool_name: str) -> Any:
        """Get resolved result (async version for compatibility)."""
        return self.get_sync(tool_name)
    
    def __contains__(self, tool_name: str) -> bool:
        return tool_name in self._results
    
    def available_tools(self) -> list[str]:
        """Return list of available precallable tool names."""
        return list(self._results.keys())


class PrecallableResultsProxy:
    """Lazy access to precallable results - only waits when actually needed."""
    
    def __init__(self, precall_awaitables: Dict[str, Union['asyncio.Task[Any]', 'asyncio.Future[Any]']], main_loop: Optional['asyncio.AbstractEventLoop'] = None):
        self._awaitables = precall_awaitables
        self._cached_results: Dict[str, Any] = {}
        self._main_loop = main_loop
        self._cache_lock = threading.RLock()  # Reentrant lock to prevent race conditions
    
    async def get(self, tool_name: str) -> Any:
        """Get result from precallable tool, waiting if necessary (async version)."""
        
        # Already cached? (thread-safe check)
        with self._cache_lock:
            if tool_name in self._cached_results:
                return self._cached_results[tool_name]
        
        # Get the awaitable
        if tool_name not in self._awaitables:
            raise PrecallableToolNotFoundError(tool_name)
        
        awaitable = self._awaitables[tool_name]
        
        # All awaitables from run_in_executor are awaitable
        result = await awaitable
        
        # Cache and return (thread-safe)
        with self._cache_lock:
            self._cached_results[tool_name] = result
        return result
    
    def get_sync(self, tool_name: str) -> Any:
        """
        Get result from precallable tool synchronously.
        WARNING: This will block! Only use from THREAD/PROCESS tools.
        """
        # Already cached? (thread-safe check)
        with self._cache_lock:
            if tool_name in self._cached_results:
                return self._cached_results[tool_name]
        
        # For sync tools, we need to block and wait
        if tool_name not in self._awaitables:
            raise PrecallableToolNotFoundError(tool_name)
        
        awaitable = self._awaitables[tool_name]
        
        # The awaitable is already a running Task or Future, we just need to wait for it
        
        try:
            # Simple type-based approach
            if isinstance(awaitable, concurrent.futures.Future):
                # It's a concurrent.futures.Future from thread executor
                result = awaitable.result(timeout=60)  # Generous default for sync access
            else:
                # It's an asyncio Task - wait for it using the main loop
                if self._main_loop is not None and not self._main_loop.is_closed():
                    # Create a simple coroutine to await the task
                    async def await_task():
                        return await awaitable
                    
                    # Run it on the main loop thread-safely
                    future = asyncio.run_coroutine_threadsafe(await_task(), self._main_loop)
                    result = future.result(timeout=60)  # Generous default for sync access
                else:
                    # No main loop available - this shouldn't happen in normal operation
                    raise PrecallableToolRuntimeError(
                        "No main loop available to wait for async task",
                        tool_name=tool_name
                    )
        except Exception as e:
            raise PrecallableToolExecutionError(tool_name, e) from e
        
        # Cache and return (thread-safe)
        with self._cache_lock:
            self._cached_results[tool_name] = result
        return result
    
    def __contains__(self, tool_name: str) -> bool:
        return tool_name in self._awaitables
    
    def available_tools(self) -> list[str]:
        """Return list of available precallable tool names."""
        return list(self._awaitables.keys())


class PrecallTool(ABC):
    """Base interface for precallable tools that run before build plan generation."""

    @abstractmethod
    def use(
        self,
        parameters: Dict[str, Any],
        precallables: Optional[PrecallableResultsProxy] = None,
    ):
        """
        Execute the precall tool's primary behaviour with the provided parameters.

        Args:
            parameters: A dictionary of parameters to pass to the tool (usually empty for precall tools).
            precallables: Not used for precall tools (they don't depend on other precallables).
        
        Note:
            - For ASYNC precall tools: This method can be async
            - For THREAD/PROCESS precall tools: This method should be sync (non-async)
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def execution_mode(self) -> ExecutionMode:
        """
        Defines how this precall tool should be executed for optimal performance.
        
        Returns:
            ExecutionMode.ASYNC: For I/O-bound operations (network, file I/O, database)
            ExecutionMode.THREAD: For CPU-bound operations that can benefit from thread parallelism  
            ExecutionMode.PROCESS: For heavy CPU-bound operations that need true parallelism
        """
        raise NotImplementedError

    @property
    def kill_after_response(self) -> bool:
        """
        Whether this precallable tool should be killed after the response is complete.
        If False, the tool remains alive and can be reused in subsequent calls.
        Default: True (kill after response for safety and resource cleanup).
        """
        return True


    @property
    @abstractmethod
    def tool_name(self) -> str:
        """Unique identifier for this precall tool."""
        raise NotImplementedError
