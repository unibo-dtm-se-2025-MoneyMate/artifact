"""
Logging configuration for MoneyMate data layer.

This file sets up structured logging for all manager modules.
The logger is configured to output timestamp, log level, module name, and message.

Note:
- To reduce invasiveness in host applications, the root logger configuration
  can be disabled by setting environment variable MONEYMATE_CONFIGURE_LOGGING=false.
"""

# data_layer/logging_config.py
import logging

def get_logger(name: str) -> logging.Logger:
    """
    Return a logger with a simple console configuration.
    """
    logger = logging.getLogger(name)
    if not logger.hasHandlers():
        logger.setLevel(logging.INFO)
        ch = logging.StreamHandler()  # Log su console
        ch.setLevel(logging.INFO)
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        ch.setFormatter(formatter)
        logger.addHandler(ch)
    return logger


