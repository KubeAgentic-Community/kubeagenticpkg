"""Logging configuration and utilities."""

import logging
import logging.config
import sys
from pathlib import Path
from typing import Optional

from pythonjsonlogger import jsonlogger

from kubeagentic.config.schema import LogFormat, LogLevel, LogOutput


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """Custom JSON formatter with additional fields."""

    def add_fields(self, log_record: dict, record: logging.LogRecord, message_dict: dict) -> None:
        """Add custom fields to log record."""
        super().add_fields(log_record, record, message_dict)
        log_record["level"] = record.levelname
        log_record["logger"] = record.name
        log_record["timestamp"] = self.formatTime(record, self.datefmt)


def setup_logging(
    level: LogLevel = LogLevel.INFO,
    log_format: LogFormat = LogFormat.JSON,
    output: LogOutput = LogOutput.CONSOLE,
    file_path: Optional[Path] = None,
) -> None:
    """
    Setup logging configuration.

    Args:
        level: Logging level (debug, info, warning, error)
        log_format: Log format (json or text)
        output: Log output destination (console or file)
        file_path: Path to log file (required if output is file)
    """
    # Map log level string to logging constant
    level_map = {
        LogLevel.DEBUG: logging.DEBUG,
        LogLevel.INFO: logging.INFO,
        LogLevel.WARNING: logging.WARNING,
        LogLevel.ERROR: logging.ERROR,
    }
    log_level = level_map.get(level, logging.INFO)

    # Create formatter
    if log_format == LogFormat.JSON:
        formatter = CustomJsonFormatter(
            "%(timestamp)s %(level)s %(name)s %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    else:
        formatter = logging.Formatter(
            fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    # Create handler
    if output == LogOutput.FILE:
        if file_path is None:
            raise ValueError("file_path must be provided when output is 'file'")

        # Create parent directories if they don't exist
        file_path.parent.mkdir(parents=True, exist_ok=True)

        handler = logging.FileHandler(file_path, encoding="utf-8")
    else:
        handler = logging.StreamHandler(sys.stdout)

    handler.setFormatter(formatter)
    handler.setLevel(log_level)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Remove existing handlers
    for h in root_logger.handlers[:]:
        root_logger.removeHandler(h)

    root_logger.addHandler(handler)

    # Set level for specific loggers
    logging.getLogger("kubeagentic").setLevel(log_level)

    # Reduce noise from third-party libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Logger instance
    """
    return logging.getLogger(name) 