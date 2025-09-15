import importlib


def test_assign_handles_missing_store_and_bad_priority(capsys):
    mod = importlib.import_module("coterie_agents.commands.assign")

    # no store
    mod.run(["Jet", "Task"], {})
    out1 = capsys.readouterr().out.lower()
    assert "no crew store" in out1

    # bad priority falls back (no crash)
    ctx = {"store": {"Jet": {"name": "Jet", "role": "runner", "status": "idle", "tasks": []}}}
    mod.run(["Jet", "Task", "--priority", "ultra"], ctx)
    out2 = capsys.readouterr().out.lower()
    assert "unknown priority" in out2
    mod.run(["Jet", "Task"], ctx)  # second time should dedupe
    out3 = capsys.readouterr().out.lower()
    assert "already" in out3
