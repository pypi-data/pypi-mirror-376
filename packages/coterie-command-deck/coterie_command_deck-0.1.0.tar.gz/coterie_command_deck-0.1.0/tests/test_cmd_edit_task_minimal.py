import importlib


def test_edit_task_smoke(capsys):
    mod = importlib.import_module("coterie_agents.commands.edit_task")
    member = {"name": "Jet", "role": "runner", "status": "idle", "tasks": ["A"]}
    ctx = {"store": {"Jet": member}}
    mod.run(["Jet", "0", "B"], ctx)
    out = capsys.readouterr().out
    assert "jet" in out.lower() or "update" in out.lower() or "b" in out.lower()
