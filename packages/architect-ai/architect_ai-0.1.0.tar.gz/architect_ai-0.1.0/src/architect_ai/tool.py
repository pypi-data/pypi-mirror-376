from abc import ABC, abstractmethod
from typing import Dict, Tuple, Any, Optional, List

from .precallable_tool import (
    ExecutionMode,
    PrecallableResultsProxy,
)


class Tool(ABC):
    """Base interface for normal tools that run during build plan execution."""

    @abstractmethod
    def use(
        self,
        parameters: Dict[str, Any],
        precallables: Optional[PrecallableResultsProxy] = None,
    ):
        """
        Execute the tool's primary behaviour with the provided parameters and optional precallables.

        Args:
            parameters: A dictionary of parameters to pass to the tool that maps the parameter name to the value.
            precallables: Lazy access to precallable tool results. Access methods:
                - For ASYNC tools: await precallables.get('tool_name') 
                - For THREAD/PROCESS tools: precallables.get_sync('tool_name')
        
        Note:
            - For ASYNC tools: This method can be async and can await precallables.get()
            - For THREAD/PROCESS tools: This method should be sync (non-async), use precallables.get_sync()
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def execution_mode(self) -> ExecutionMode:
        """
        Defines how this tool should be executed for optimal performance.
        
        Returns:
            ExecutionMode.ASYNC: For I/O-bound operations (network, file I/O, database)
            ExecutionMode.THREAD: For CPU-bound operations that can benefit from thread parallelism  
            ExecutionMode.PROCESS: For heavy CPU-bound operations that need true parallelism
        """
        raise NotImplementedError

    @property
    def required_precallables(self) -> List[str]:
        """
        For PROCESS tools only: List of specific precallable tool names this tool requires.
        
        This optimization prevents process tools from waiting for ALL precallables to complete.
        Only the specified precallables will be awaited and included in the PicklablePrecallableResults.
        
        Can be overridden by LLM via "_required_precallables" parameter in build plan.
        
        Default: [] (empty list means ALL precallables - backwards compatible)
        
        Example:
            return ["precallable_async_tool", "precallable_thread_tool"]
        
        Note: Async and Thread tools ignore this property as they can access
        PrecallableResultsProxy directly without serialization constraints.
        """
        return []  # Default: require all precallables (backwards compatible)


    @property
    @abstractmethod
    def tool_name(self) -> str:
        """Unique identifier for this tool."""
        raise NotImplementedError

    @property
    @abstractmethod
    def usage_context(self) -> str:
        """Description of when this tool should be used."""
        raise NotImplementedError

    @property
    @abstractmethod
    def purpose(self) -> str:
        """Description of what this tool accomplishes."""
        raise NotImplementedError

    @property
    @abstractmethod
    def parameter_instructions(self) -> Dict[str, Tuple[str, str]]:
        """Map of parameter names to (DataType, description) tuples."""
        raise NotImplementedError

    @property
    @abstractmethod
    def output_descriptions(self) -> Dict[str, Tuple[str, str]]:
        """Map of output names to (DataType, description) tuples."""
        raise NotImplementedError
