"""
Logging configuration for MoneyMate data layer.

This file sets up structured logging for all manager modules.
The logger is configured to output timestamp, log level, module name, and message.

Note:
- To reduce invasiveness in host applications, the root logger configuration
  can be disabled by setting environment variable MONEYMATE_CONFIGURE_LOGGING=false.
"""

import logging
import os

# Basic configuration for the root logger is opt-in via env var (defaults to True for tests/CLI).
_configure_root = os.environ.get("MONEYMATE_CONFIGURE_LOGGING", "true").lower() not in ("false", "0", "no")
_log_level = os.environ.get("MONEYMATE_LOG_LEVEL", "INFO").upper()
level = getattr(logging, _log_level, logging.INFO)

if _configure_root:
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s [%(name)s]: %(message)s",
    )