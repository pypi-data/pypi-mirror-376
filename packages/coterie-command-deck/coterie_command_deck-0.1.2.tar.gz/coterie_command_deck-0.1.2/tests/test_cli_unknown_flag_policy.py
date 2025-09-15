import importlib
import pkgutil
from types import SimpleNamespace

import pytest

import coterie_agents.commands as commands_pkg


def _iter_command_modules():
    for m in pkgutil.iter_modules(commands_pkg.__path__, commands_pkg.__name__ + "."):
        if m.name.endswith(".test_error"):
            continue
        yield m.name


@pytest.mark.parametrize("modname", list(_iter_command_modules()))
def test_unknown_flag_prints_not_found_and_usage(modname, capsys):
    mod = importlib.import_module(modname)
    run = getattr(mod, "run", None)
    if not callable(run):
        pytest.skip(f"{modname} has no run()")
    run(["--definitely-unknown-flag"], SimpleNamespace(store={}))
    out = capsys.readouterr().out.lower()
    assert "not found" in out
    assert "usage" in out or "help" in out
