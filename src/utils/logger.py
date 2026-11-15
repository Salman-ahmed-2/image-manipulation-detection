"""Logging utility for the Image Manipulation Detection System.

Provides standardized logging formats and handlers across all application modules.
"""

from __future__ import annotations

import logging
import sys
from typing import Optional

from config import Config


def get_logger(name: str) -> logging.Logger:
    """Get or configure a standardized logger instance.

    Args:
        name: Name of the logger, typically __name__ of the calling module.

    Returns:
        logging.Logger: Configured logger instance.
    """
    logger = logging.getLogger(name)

    if not logger.handlers:
        log_level = getattr(logging, Config.LOG_LEVEL.upper(), logging.INFO)
        logger.setLevel(log_level)

        formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setLevel(log_level)
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)

        if getattr(Config, "ENABLE_FILE_LOGGING", False) and getattr(Config, "LOG_FILE", None):
            try:
                log_file_path = Config.LOG_FILE
                log_file_path.parent.mkdir(parents=True, exist_ok=True)
                file_handler = logging.FileHandler(str(log_file_path), encoding="utf-8")
                file_handler.setLevel(log_level)
                file_handler.setFormatter(formatter)
                logger.addHandler(file_handler)
            except Exception:
                pass

    return logger
