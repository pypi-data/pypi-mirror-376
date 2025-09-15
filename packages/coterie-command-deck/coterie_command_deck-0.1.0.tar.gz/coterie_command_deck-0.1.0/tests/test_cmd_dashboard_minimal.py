import importlib
from types import SimpleNamespace


def test_dashboard_basic(capsys):
    try:
        mod = importlib.import_module("coterie_agents.commands.dashboard")
    except ModuleNotFoundError:
        mod = importlib.import_module("coterie_agents.commands.board")
    ctx = SimpleNamespace(store={"board": {"today": 1, "open": 2}})
    mod.run([], ctx)
    out = capsys.readouterr().out.lower()
    assert "board" in out or "dashboard" in out
