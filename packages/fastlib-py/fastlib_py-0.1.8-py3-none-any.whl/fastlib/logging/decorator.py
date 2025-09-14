from contextlib import contextmanager
from .handlers import log, logging_context
from typing import Any, Optional
import time
from functools import wraps

from fastlib.logging.handlers import Logger


@contextmanager
def log_context(**context: Any):
    """
    Context manager for temporarily adding logging context.

    Example:
        with log_context(user_id=123, request_id="abc"):
            log.info("Processing request")  # Will include user_id and request_id
    """
    current_context = logging_context.get().copy()
    try:
        Logger.add_context(**context)
        yield
    finally:
        logging_context.set(current_context)


def log_performance(operation_name: Optional[str] = None):
    """
    Decorator to log function performance.

    Args:
        operation_name: Custom operation name (defaults to function name)
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            name = operation_name or func.__name__
            start_time = time.time()

            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                log.info(
                    f"Operation completed: {name}",
                    operation=name,
                    duration_ms=round(duration * 1000, 2),
                    status="success",
                )
                return result
            except Exception as e:
                duration = time.time() - start_time
                log.error(
                    f"Operation failed: {name}",
                    operation=name,
                    duration_ms=round(duration * 1000, 2),
                    status="error",
                    exc_info=e,
                )
                raise

        return wrapper

    return decorator
