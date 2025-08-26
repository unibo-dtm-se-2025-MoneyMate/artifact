"""
Logging configuration for MoneyMate data layer.

This file sets up structured logging for all manager modules.
The logger is configured to output timestamp, log level, module name, and message.
"""

import logging

# Basic configuration for the root logger.
logging.basicConfig(
    level=logging.INFO,  # Set logging level to INFO. Change to DEBUG for verbose output.
    format="%(asctime)s %(levelname)s [%(name)s]: %(message)s",
)