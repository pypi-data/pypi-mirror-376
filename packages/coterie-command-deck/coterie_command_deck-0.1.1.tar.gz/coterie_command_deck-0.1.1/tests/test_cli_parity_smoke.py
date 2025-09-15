import importlib
import pkgutil
from types import SimpleNamespace

import pytest

import coterie_agents.commands as commands_pkg


def _iter_command_modules():
    for m in pkgutil.iter_modules(commands_pkg.__path__, commands_pkg.__name__ + "."):
        name = m.name
        # Skip any intentional test stubs or internal fixtures if you have them
        if name.endswith(".test_error"):
            continue
        yield name


@pytest.mark.parametrize("modname", list(_iter_command_modules()))
def test_command_help_and_default_do_not_raise(modname, capsys):
    mod = importlib.import_module(modname)
    run = getattr(mod, "run", None)
    if not callable(run):
        pytest.skip(f"{modname} has no run()")
    ctx = SimpleNamespace(store={})
    # --help path must not raise
    run(["--help"], ctx)
    _ = capsys.readouterr().out  # drain output
    # default [] path must not raise
    run([], ctx)
    _ = capsys.readouterr().out
