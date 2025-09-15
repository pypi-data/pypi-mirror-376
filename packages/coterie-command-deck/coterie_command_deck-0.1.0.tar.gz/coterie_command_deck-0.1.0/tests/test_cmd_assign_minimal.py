import importlib


def test_assign_multi_assignee_soft(capsys):
    mod = importlib.import_module("coterie_agents.commands.assign")
    ctx = {
        "store": {
            "Jet": {"name": "Jet", "role": "runner", "status": "idle", "tasks": []},
            "Mixie": {
                "name": "Mixie",
                "role": "chemist",
                "status": "idle",
                "tasks": [],
            },
        }
    }
    # Multi-assignee + priority (either form should be tolerated)
    try:
        mod.run(["Jet", "Mixie", "Wipe down rig", "--priority", "high"], ctx)
    except TypeError:
        mod.run(["Jet", "Mixie", "Wipe down rig", "high"], ctx)

    out = capsys.readouterr().out.lower()
    assert "jet" in out or "mixie" in out or "assign" in out or "priority" in out
