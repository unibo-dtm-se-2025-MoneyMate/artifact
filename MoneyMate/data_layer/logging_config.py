"""
Shared logging configuration for the MoneyMate data layer.

This module exposes get_logger(name), which returns a logger preconfigured
with a simple console handler and a standard format:

    timestamp - logger_name - level - message

The intent is to have a non-invasive, centralized way to obtain loggers for
all data-layer modules without forcing a specific global logging setup on
embedding applications.
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


