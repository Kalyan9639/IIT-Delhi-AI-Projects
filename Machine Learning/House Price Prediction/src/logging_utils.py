"""
Logging module for Bangalore Real Estate Intelligence System.
Provides comprehensive logging functionality.
"""

import logging

from .config import LOG_DIR, LOG_FILE

# Ensure log directory exists
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Create logger
logger = logging.getLogger('RealEstateAI')
logger.setLevel(logging.DEBUG)

# File handler
file_handler = logging.FileHandler(LOG_FILE)
file_handler.setLevel(logging.DEBUG)

# Console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

# Formatter
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(module)s - %(funcName)s - %(message)s'
)
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

# Add handlers
logger.addHandler(file_handler)
logger.addHandler(console_handler)


def log_function_call(func_name, message):
    """Log a function call with message."""
    logger.info(f"Function '{func_name}': {message}")


def log_error(func_name, error_message):
    """Log an error."""
    logger.error(f"Function '{func_name}': {error_message}")


def log_warning(func_name, warning_message):
    """Log a warning."""
    logger.warning(f"Function '{func_name}': {warning_message}")


def log_debug(func_name, debug_message):
    """Log debug information."""
    logger.debug(f"Function '{func_name}': {debug_message}")


def log_info(func_name, info_message):
    """Log information."""
    logger.info(f"Function '{func_name}': {info_message}")


def get_logger():
    """Get the logger instance."""
    return logger
