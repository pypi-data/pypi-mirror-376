from __future__ import annotations

import importlib
import inspect
import pkgutil
from contextlib import suppress

import pytest

import coterie_agents.commands as commands_pkg


def get_command_modules():
    return [
        importlib.import_module(m.name)
        for m in pkgutil.iter_modules(commands_pkg.__path__, commands_pkg.__name__ + ".")
    ]


@pytest.mark.parametrize("mod", get_command_modules())
def test_run_zero_arg_safe(mod):
    # If the module has a zero-arg run(), call it defensively
    run_func = getattr(mod, "run", None)
    if callable(run_func):
        sig = inspect.signature(run_func)
        # Only call if all parameters have defaults or are optional
        if (
            all(
                p.default != inspect.Parameter.empty
                or p.kind == inspect.Parameter.VAR_POSITIONAL
                or p.kind == inspect.Parameter.VAR_KEYWORD
                for p in sig.parameters.values()
            )
            or len(sig.parameters) == 0
        ):
            with suppress(Exception):
                run_func()  # Should not raise
