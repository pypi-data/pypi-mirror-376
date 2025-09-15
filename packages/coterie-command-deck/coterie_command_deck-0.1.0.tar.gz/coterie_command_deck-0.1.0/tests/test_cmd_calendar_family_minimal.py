import importlib
import pkgutil
from types import SimpleNamespace


def _calendar_modules():
    pkg = importlib.import_module("coterie_agents.commands")
    for m in pkgutil.iter_modules(pkg.__path__, pkg.__name__ + "."):
        name = m.name.rsplit(".", 1)[-1]
        if name.startswith("calendar_"):
            yield importlib.import_module(m.name)


def test_calendar_modules_help_and_noop_soft(capsys):
    ctx = SimpleNamespace(store={})
    for mod in _calendar_modules():
        # help path
        mod.run(["--help"], ctx)
        help_out = capsys.readouterr().out.lower()
        assert "help" in help_out or "usage" in help_out or "calendar" in help_out

        # noop/default path
        mod.run([], ctx)
        out = capsys.readouterr().out.lower()
        # don't assert too strictly; just ensure something was printed
        assert out.strip() != ""
