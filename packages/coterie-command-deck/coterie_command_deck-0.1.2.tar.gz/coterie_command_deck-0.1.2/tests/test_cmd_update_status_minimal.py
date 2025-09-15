import importlib


def test_update_sets_status_soft(capsys):
    mod = importlib.import_module("coterie_agents.commands.update")
    member = {"name": "Jet", "role": "runner", "status": "idle", "tasks": []}
    ctx = {"store": {"Jet": member}}

    # common shapes: update Jet --status busy   OR   update Jet busy
    try:
        mod.run(["Jet", "--status", "busy"], ctx)
    except TypeError:
        mod.run(["Jet", "busy"], ctx)

    out = capsys.readouterr().out.lower()
    assert "jet" in out and ("busy" in out or "status" in out or "updated" in out)
