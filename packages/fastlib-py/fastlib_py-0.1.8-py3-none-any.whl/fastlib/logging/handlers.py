"""
Logger - A comprehensive logging utility for the application.
"""

import sys
from contextvars import ContextVar
from pathlib import Path
from typing import Any, Optional, Union

from asgi_correlation_id import correlation_id
from loguru import logger

from fastlib.config.manager import ConfigManager
from fastlib.logging.config import LogConfig

# Context variable for additional logging context
logging_context: ContextVar[dict[str, Any]] = ContextVar(
    "logging_context", default=None
)


class Logger:
    """
    Enhanced logging utility with correlation ID support and structured logging.
    """

    _instances: dict[str, "Logger"] = {}
    _config: Optional[LogConfig] = None
    _is_configured: bool = False

    @classmethod
    def _get_config(cls) -> LogConfig:
        """Lazy load configuration."""
        if cls._config is None:
            cls._config = ConfigManager.get_config_instance("log")
        return cls._config

    @classmethod
    def get_instance(cls, name: str = "default", **kwargs) -> "Logger":
        """
        Get or create a named logger instance.

        Args:
            name: Logger instance name
            **kwargs: Configuration overrides

        Returns:
            Logger instance
        """
        if name not in cls._instances:
            cls._instances[name] = cls(**kwargs)
        return cls._instances[name]

    def __init__(
        self,
        log_dir: Optional[Union[str, Path]] = None,
        app_name: Optional[str] = None,
        enable_console: Optional[bool] = None,
        **kwargs,
    ):
        """Initialize the Logger with optional overrides."""
        config: LogConfig = self._get_config()

        # Use provided values or fall back to config
        self.log_dir = Path(log_dir) if log_dir else config.log_dir
        self.app_name = app_name or config.app_name
        self.enable_console = (
            enable_console if enable_console is not None else config.enable_console_log
        )

        # Merge additional configuration overrides
        self._config_overrides = kwargs

        # Only setup logging once globally
        if not self.__class__._is_configured:
            self._setup_logging()
            self.__class__._is_configured = True

    def _setup_logging(self) -> None:
        """Configure loguru logger with handlers based on configuration."""
        # Remove default handler
        logger.remove()

        # Create log directory
        self.log_dir.mkdir(parents=True, exist_ok=True)

        config = self._get_config()

        # Common handler configuration
        common_config = {
            "backtrace": True,
            "diagnose": True,
            "enqueue": config.enable_async,
        }

        # Console handler
        if self.enable_console:
            logger.add(
                sys.stderr,
                format=self._get_format_string(),
                level=config.log_level,
                colorize=True,
                **common_config,
            )

        # Main file handler
        rotation = config.max_file_size or config.log_rotation
        log_file_pattern = self.log_dir / config.log_file_pattern

        logger.add(
            str(log_file_pattern),
            format=self._get_format_string(),
            level=config.log_level,
            rotation=rotation,
            retention=config.log_retention,
            compression="zip",
            serialize=config.enable_json_logs,
            **common_config,
        )

        # Error log handler
        error_log_pattern = self.log_dir / config.error_log_file_pattern

        logger.add(
            str(error_log_pattern),
            format=self._get_format_string(),
            level="ERROR",
            rotation=config.error_log_rotation,
            retention=config.error_log_retention,
            compression="zip",
            serialize=config.enable_json_logs,
            **common_config,
        )

    def _get_format_string(self) -> str:
        """Get the log format string with correlation ID and context."""
        config = self._get_config()

        if config.enable_json_logs:
            # JSON logs don't need format string
            return "{message}"

        # Check if format already contains correlation_id
        if "correlation_id" in config.log_format:
            return config.log_format

        # Insert correlation ID into the format
        return (
            "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | "
            "[CID:{extra[correlation_id]}] | "
            "{name}:{function}:{line} | {message}"
        )

    @staticmethod
    def _get_correlation_id() -> str:
        """Get the current correlation ID or return SYSTEM."""
        try:
            return correlation_id.get() or "SYSTEM"
        except Exception:
            return "SYSTEM"

    def _get_context(self) -> dict[str, Any]:
        """Get combined logging context."""
        context = {
            "correlation_id": self._get_correlation_id(),
            "app_name": self.app_name,
        }

        # Add any additional context from context variable
        context.update(logging_context.get())

        return context

    def _bind_logger(self, **extra_context: Any) -> logger:
        """Bind logger with current context."""
        context = self._get_context()
        context.update(extra_context)
        return logger.bind(**context)

    def debug(self, message: str, **kwargs: Any) -> None:
        """Log a debug message."""
        self._bind_logger(**kwargs).debug(message)

    def info(self, message: str, **kwargs: Any) -> None:
        """Log an info message."""
        self._bind_logger(**kwargs).info(message)

    def warning(self, message: str, **kwargs: Any) -> None:
        """Log a warning message."""
        self._bind_logger(**kwargs).warning(message)

    def error(
        self, message: str, exc_info: Optional[Exception] = None, **kwargs: Any
    ) -> None:
        """Log an error message with optional exception information."""
        bound_logger = self._bind_logger(**kwargs)

        if exc_info is not None:
            bound_logger.opt(exception=exc_info).error(message)
        else:
            bound_logger.error(message)

    def critical(
        self, message: str, exc_info: Optional[Exception] = None, **kwargs: Any
    ) -> None:
        """Log a critical error message."""
        bound_logger = self._bind_logger(**kwargs)

        if exc_info is not None:
            bound_logger.opt(exception=exc_info).critical(message)
        else:
            bound_logger.critical(message)

    def exception(self, message: str, **kwargs: Any) -> None:
        """Log an exception with traceback."""
        self._bind_logger(**kwargs).exception(message)

    @staticmethod
    def add_context(**context: Any) -> None:
        """Add context that will be included in all subsequent logs."""
        current_context = logging_context.get()
        current_context.update(context)
        logging_context.set(current_context)

    @staticmethod
    def clear_context() -> None:
        """Clear the logging context."""
        logging_context.set({})


# Create default instance
log = Logger.get_instance()
