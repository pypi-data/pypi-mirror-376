from __future__ import annotations

import pytest

from coterie_agents.logging_config import configure as configure_logging
from coterie_agents.runtime_guard import configure_deprecation_handling


def test_logging_config_runs():
    configure_logging("DEBUG")  # should not raise


def test_runtime_guard_default_env_ok(monkeypatch):
    monkeypatch.delenv("AGENTS_DEBUG", raising=False)
    monkeypatch.delenv("USE_OLD_TASK_KEY", raising=False)
    configure_deprecation_handling()  # should not raise


def test_runtime_guard_deprecated_env_raises(monkeypatch):
    monkeypatch.setenv("USE_OLD_TASK_KEY", "1")
    with pytest.raises(RuntimeError):
        configure_deprecation_handling()
