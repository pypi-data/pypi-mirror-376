from __future__ import annotations

import importlib

import pytest


def test_exit_raises_systemexit() -> None:
    mod = importlib.import_module("coterie_agents.commands.exit")
    fn = getattr(mod, "run", None) or getattr(mod, "main", None)
    assert callable(fn)
    with pytest.raises(SystemExit):
        try:
            fn()
        except TypeError:
            fn([], {"env": {}})
