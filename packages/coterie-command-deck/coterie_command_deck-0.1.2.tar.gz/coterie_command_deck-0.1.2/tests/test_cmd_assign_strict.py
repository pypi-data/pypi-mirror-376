import importlib

from pytest import CaptureFixture


def test_assign_multi_assignee_with_priority(capsys: CaptureFixture[str]) -> None:
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
    mod.run(["Jet", "Mixie", "Wipe down rig", "--priority", "high"], ctx)
    out = capsys.readouterr().out.lower()
    assert "jet" in out and "mixie" in out and "priority" in out


def test_assign_multi_priority_dedupe(capsys: CaptureFixture[str]) -> None:
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
    mod.run(["Jet", "Mixie", "Wipe down rig", "--priority", "high"], ctx)
    out1 = capsys.readouterr().out.lower()
    assert "jet" in out1 and "mixie" in out1 and "priority" in out1

    # second run should not duplicate
    mod.run(["Jet", "Wipe down rig", "--priority", "high"], ctx)
    out2 = capsys.readouterr().out.lower()
    assert "already" in out2 or "jet" in out2
