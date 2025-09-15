from __future__ import annotations

import logging

import pytest

from coterie_agents.logging_config import configure


def test_configure_debug_level() -> None:
    logger = configure("DEBUG")
    assert isinstance(logger, logging.Logger)
    logger.debug("ping")


def test_configure_bad_level_raises() -> None:
    with pytest.raises(ValueError):
        configure("NOT_A_LEVEL")
