"""
Structured Logging System for Aviator Bot
Replaces print() statements with proper logging
"""

import logging
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler
import sys


class BotLogger:
    """
    Centralized logging system with multiple handlers.
    - Console output (INFO and above)
    - File output (DEBUG and above, rotating)
    - Structured format for easy parsing
    """

    def __init__(self, name='AviatorBot', log_dir='logs'):
        """
        Initialize logger with file and console handlers.

        Args:
            name: Logger name
            log_dir: Directory for log files
        """
        self.name = name
        self.log_dir = log_dir
        os.makedirs(log_dir, exist_ok=True)

        # Create logger
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)

        # Prevent duplicate handlers
        if self.logger.handlers:
            return

        # Formatter for detailed logs
        detailed_formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        # Formatter for console (simpler)
        console_formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(message)s',
            datefmt='%H:%M:%S'
        )

        # File handler - Rotating (10MB per file, keep 5 files)
        log_file = os.path.join(log_dir, f'{name.lower()}.log')
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(detailed_formatter)

        # Console handler - Only INFO and above
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(console_formatter)

        # Add handlers
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

    def debug(self, msg, *args, **kwargs):
        """Log debug message (file only)."""
        self.logger.debug(msg, *args, **kwargs)

    def info(self, msg, *args, **kwargs):
        """Log info message (console + file)."""
        self.logger.info(msg, *args, **kwargs)

    def warning(self, msg, *args, **kwargs):
        """Log warning message (console + file)."""
        self.logger.warning(msg, *args, **kwargs)

    def error(self, msg, *args, **kwargs):
        """Log error message (console + file)."""
        self.logger.error(msg, *args, **kwargs)

    def critical(self, msg, *args, **kwargs):
        """Log critical message (console + file)."""
        self.logger.critical(msg, *args, **kwargs)

    def exception(self, msg, *args, **kwargs):
        """Log exception with traceback."""
        self.logger.exception(msg, *args, **kwargs)

    def section(self, title, width=85):
        """Log a section header."""
        self.logger.info("=" * width)
        self.logger.info(title)
        self.logger.info("=" * width)

    def subsection(self, title, width=85):
        """Log a subsection header."""
        self.logger.info("-" * width)
        self.logger.info(title)
        self.logger.info("-" * width)


# Global logger instance
_bot_logger = None


def get_logger(name='AviatorBot'):
    """
    Get or create global logger instance.

    Args:
        name: Logger name

    Returns:
        BotLogger instance
    """
    global _bot_logger
    if _bot_logger is None:
        _bot_logger = BotLogger(name=name)
    return _bot_logger


# Convenience functions for quick access
def debug(msg, *args, **kwargs):
    """Log debug message."""
    get_logger().debug(msg, *args, **kwargs)


def info(msg, *args, **kwargs):
    """Log info message."""
    get_logger().info(msg, *args, **kwargs)


def warning(msg, *args, **kwargs):
    """Log warning message."""
    get_logger().warning(msg, *args, **kwargs)


def error(msg, *args, **kwargs):
    """Log error message."""
    get_logger().error(msg, *args, **kwargs)


def critical(msg, *args, **kwargs):
    """Log critical message."""
    get_logger().critical(msg, *args, **kwargs)


def exception(msg, *args, **kwargs):
    """Log exception with traceback."""
    get_logger().exception(msg, *args, **kwargs)


def section(title, width=85):
    """Log a section header."""
    get_logger().section(title, width)


def subsection(title, width=85):
    """Log a subsection header."""
    get_logger().subsection(title, width)
