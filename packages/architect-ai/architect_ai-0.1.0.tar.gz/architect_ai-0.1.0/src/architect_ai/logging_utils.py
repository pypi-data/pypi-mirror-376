"""
Shared logging utilities for the architect_ai package.
"""
import logging
from typing import Optional


def log_structured(
    logger: logging.Logger,
    level: str,
    message: str,
    correlation_id: Optional[str] = None,
    perf_time: Optional[float] = None,
    **kwargs,
) -> None:
    """
    Helper function for structured logging using extra parameters.
    
    Args:
        logger: The logger instance to use
        level: The log level ('debug', 'info', 'warning', 'error', 'critical')
        message: The log message
        correlation_id: Optional correlation ID for request tracing
        perf_time: Optional performance timing in seconds
        **kwargs: Additional structured data to include in the log
        
    Note: 
        Library defaults to 'warning' level and above for production usage.
        Callers should configure logging levels as needed.
    """
    extra_data = {**kwargs}
    
    if correlation_id:
        extra_data["correlation_id"] = correlation_id
    if perf_time is not None:
        extra_data["perf_time"] = round(perf_time, 3)
    
    getattr(logger, level)(message, extra=extra_data)
