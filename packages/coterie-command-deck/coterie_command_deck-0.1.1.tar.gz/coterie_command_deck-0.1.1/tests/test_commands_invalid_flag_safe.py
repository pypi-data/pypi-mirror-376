import importlib
import pkgutil
from types import SimpleNamespace

import coterie_agents.commands as commands_pkg


def iter_mods():
    for m in pkgutil.iter_modules(commands_pkg.__path__, commands_pkg.__name__ + "."):
        yield importlib.import_module(m.name)


def test_every_command_handles_unknown_flag():
    ctx = SimpleNamespace(store={}, router=SimpleNamespace(get_available_commands=lambda **_: []))
    for mod in iter_mods():
        if hasattr(mod, "run"):
            try:
                mod.run(["--definitely-not-a-real-flag"], ctx)
            except SystemExit as exc:
                raise AssertionError(f"{mod.__name__} raised SystemExit on unknown flag") from exc
