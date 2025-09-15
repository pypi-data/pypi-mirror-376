"""
Logging configuration for the agents package.

Use `configure(level: str | None)` once on startup. Override with
`AGENTS_LOG_LEVEL` environment variable (DEBUG|INFO|WARNING|ERROR|CRITICAL).
"""

from __future__ import annotations

import logging
import os
from typing import Final

_LEVELS: Final[dict[str, int]] = {
    "CRITICAL": logging.CRITICAL,
    "ERROR": logging.ERROR,
    "WARNING": logging.WARNING,
    "INFO": logging.INFO,
    "DEBUG": logging.DEBUG,
    "NOTSET": logging.NOTSET,
}


def _normalize_level(level: str | int | None) -> int:
    if level is None:
        return logging.INFO
    if isinstance(level, int):
        return level
    lvl = _LEVELS.get(level.upper())
    if lvl is None:
        raise ValueError(f"Invalid log level: {level!r}")
    return lvl


def configure(
    level: str | int | None = None,
    *,
    name: str | None = None,
    propagate: bool = False,
    fmt: str | None = None,
) -> logging.Logger:
    """
    Configure and return a logger for the project.

    - Respects explicit `level` first; falls back to $COTERIE_LOG_LEVEL, then INFO.
    - Avoids duplicate handlers on repeated calls.
    - Returns the configured logger (so tests can assert on it).

    Args:
        level: str/int log level (e.g., "DEBUG"), overrides env.
        name: logger name; defaults to "coterie_agents".
        propagate: set logger.propagate.
        fmt: optional format string for StreamHandler.

    Raises:
        ValueError: if `level` is an unknown level string.
    """
    env_level = os.getenv("COTERIE_LOG_LEVEL")
    eff_level = _normalize_level(level if level is not None else env_level)

    logger_name = name or "coterie_agents"
    logger = logging.getLogger(logger_name)
    logger.setLevel(eff_level)
    logger.propagate = propagate

    # Add exactly one StreamHandler with a reasonable format
    if not any(isinstance(h, logging.StreamHandler) for h in logger.handlers):
        handler = logging.StreamHandler()
        handler.setLevel(eff_level)
        handler.setFormatter(
            logging.Formatter(fmt or "%(asctime)s %(levelname)s [%(name)s] %(message)s")
        )
        logger.addHandler(handler)

    return logger
