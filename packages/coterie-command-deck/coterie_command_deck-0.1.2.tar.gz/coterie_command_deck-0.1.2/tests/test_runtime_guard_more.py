from __future__ import annotations

import warnings

import pytest

from coterie_agents.runtime_guard import configure_deprecation_handling


def test_strict_deprecation_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AGENTS_DEPRECATION_STRICT", "1")
    configure_deprecation_handling()
    with pytest.raises(DeprecationWarning):
        warnings.warn("deprecated", DeprecationWarning, stacklevel=2)


def test_legacy_task_env_fence(monkeypatch: pytest.MonkeyPatch) -> None:
    # If your runtime_guard escalates legacy flags, this covers it.
    monkeypatch.setenv("USE_OLD_TASK_KEY", "1")
    with pytest.raises(RuntimeError):
        configure_deprecation_handling()
