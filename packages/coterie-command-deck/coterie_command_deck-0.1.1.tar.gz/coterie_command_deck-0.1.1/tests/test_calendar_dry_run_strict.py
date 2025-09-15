import importlib
import pkgutil
from types import SimpleNamespace

import pytest

import coterie_agents.commands as commands_pkg


def _calendar_modules():
    for m in pkgutil.iter_modules(commands_pkg.__path__, commands_pkg.__name__ + "."):
        name = m.name.rsplit(".", 1)[-1]
        if name.startswith("calendar_"):
            yield m.name


@pytest.mark.parametrize("modname", list(_calendar_modules()))
def test_calendar_commands_emit_dry_run_signal(modname, capsys, monkeypatch, tmp_path):
    # For calendar_auth, force a deterministic token path
    if modname.endswith(".calendar_auth"):
        monkeypatch.setenv("COTERIE_TOKEN_FILE", str(tmp_path / "token.pickle"))

    mod = importlib.import_module(modname)
    run = getattr(mod, "run", None)
    assert callable(run), f"{modname} missing run()"

    # Default/no-arg path must not raise and must signal dry-run
    run([], SimpleNamespace(store={}))
    out = capsys.readouterr().out.lower()

    # Gentle but explicit: require 'dry' (covers 'dry-run', 'dry run', etc.)
    assert "dry" in out, f"{modname} output lacks dry-run signal: {out!r}"

    # Extra checks for calendar_auth
    if modname.endswith(".calendar_auth"):
        assert "path" in out, "calendar_auth should display token path"
        assert ("present" in out) or ("missing" in out), "calendar_auth should show token state"
