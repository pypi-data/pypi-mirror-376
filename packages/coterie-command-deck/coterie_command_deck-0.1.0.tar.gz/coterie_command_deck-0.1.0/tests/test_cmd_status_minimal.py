import importlib
from types import SimpleNamespace


def test_status_lists_member(capsys):
    mod = importlib.import_module("coterie_agents.commands.status")
    ctx = SimpleNamespace(
        store={"Jet": {"name": "Jet", "role": "runner", "status": "idle", "tasks": ["A"]}}
    )
    mod.run([], ctx)
    out = capsys.readouterr().out
    assert "Jet" in out and "idle" in out
