"""
Logging configuration for MoneyMate data layer.

This file sets up structured logging for all manager modules.
The logger is configured to output timestamp, log level, module name, and message.
"""

import logging
import os

# Basic configuration for the root logger.
# Level can be overridden via env var MONEYMATE_LOG_LEVEL (e.g., DEBUG, INFO, WARNING, ERROR).
_log_level = os.environ.get("MONEYMATE_LOG_LEVEL", "INFO").upper()
level = getattr(logging, _log_level, logging.INFO)

logging.basicConfig(
    level=level,  # Set logging level to INFO. Change to DEBUG for verbose output.
    format="%(asctime)s %(levelname)s [%(name)s]: %(message)s",
)