"""Centralized application logging configuration."""

from __future__ import annotations

import logging
import sys

from config import Config


_LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(message)s"


def get_logger(name: str) -> logging.Logger:
    """Return a configured application logger.

    Args:
        name: Logger name, typically the calling module's ``__name__``.

    Returns:
        A logger that writes to standard output and, when configured, a log file.
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, Config.LOG_LEVEL, logging.INFO))
    logger.propagate = False

    formatter = logging.Formatter(_LOG_FORMAT)
    has_stdout_handler = any(
        getattr(handler, "_imd_handler_kind", None) == "stdout" for handler in logger.handlers
    )
    if not has_stdout_handler:
        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setFormatter(formatter)
        stream_handler._imd_handler_kind = "stdout"  # type: ignore[attr-defined]
        logger.addHandler(stream_handler)

    log_file = Config.LOG_FILE
    if Config.ENABLE_FILE_LOGGING and log_file is not None and not any(
        getattr(handler, "_imd_handler_kind", None) == "file" for handler in logger.handlers
    ):
        try:
            log_file.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(log_file, encoding="utf-8")
            file_handler.setFormatter(formatter)
            file_handler._imd_handler_kind = "file"  # type: ignore[attr-defined]
            logger.addHandler(file_handler)
        except OSError as error:
            logger.warning("File logging is unavailable: %s", error)

    return logger
