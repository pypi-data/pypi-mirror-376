from __future__ import annotations

import importlib

import pytest


def test_configure_debug_level() -> None:
    mod = importlib.import_module("coterie_agents.commands.logger_config")
    assert callable(getattr(mod, "configure", None))
    mod.configure("DEBUG")


def test_configure_invalid_level() -> None:
    mod = importlib.import_module("coterie_agents.commands.logger_config")
    with pytest.raises(ValueError):
        mod.configure("NOTALEVEL")


def test_configure_context_override() -> None:
    mod = importlib.import_module("coterie_agents.commands.logger_config")
    ctx = {"log_level": "INFO"}
    mod.configure("DEBUG", ctx)
    assert ctx["log_level"] == "DEBUG"
