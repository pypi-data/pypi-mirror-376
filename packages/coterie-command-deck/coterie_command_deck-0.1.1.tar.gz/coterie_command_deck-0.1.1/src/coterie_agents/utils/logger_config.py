"""Logger configuration utilities."""

import logging
import sys


def get_logger(name: str | None = None) -> logging.Logger:
    """Get a configured logger instance."""
    logger = logging.getLogger(name or __name__)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

    return logger


def debug_log(message: str, logger: logging.Logger | None = None) -> None:
    """Simple debug logging with fallback."""
    if logger:
        logger.debug(message)
    else:
        print(f"[DEBUG] {message}")
