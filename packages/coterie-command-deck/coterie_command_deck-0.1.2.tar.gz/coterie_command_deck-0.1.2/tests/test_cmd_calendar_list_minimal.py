from types import SimpleNamespace

import pytest

mod = pytest.importorskip("coterie_agents.commands.calendar_list")


def test_calendar_list_help_and_noop(capsys):
    ctx = SimpleNamespace(store={})
    mod.run(["--help"], ctx)
    out = capsys.readouterr().out.lower()
    assert "help" in out or "usage" in out or "calendar" in out

    mod.run([], ctx)
    out = capsys.readouterr().out.lower()
    assert out.strip() != ""
