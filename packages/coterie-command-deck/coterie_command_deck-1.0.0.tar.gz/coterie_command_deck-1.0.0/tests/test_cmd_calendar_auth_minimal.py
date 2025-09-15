import importlib
import tempfile
from types import SimpleNamespace


def test_calendar_auth_help_and_noop(capsys, monkeypatch):
    mod = importlib.import_module("coterie_agents.commands.calendar_auth")
    ctx = SimpleNamespace(store={})

    mod.run(["--help"], ctx)
    help_out = capsys.readouterr().out.lower()
    assert "usage" in help_out or "help" in help_out

    # override token path to something that won't exist (secure)
    with tempfile.NamedTemporaryFile() as tmp:
        monkeypatch.setenv("COTERIE_TOKEN_FILE", tmp.name)
        mod.run([], ctx)
        out = capsys.readouterr().out.lower()
        assert "dry-run" in out and "path" in out and ("missing" in out or "present" in out)
