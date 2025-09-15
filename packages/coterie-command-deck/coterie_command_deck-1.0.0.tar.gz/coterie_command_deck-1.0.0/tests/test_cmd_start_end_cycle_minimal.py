import importlib
from types import SimpleNamespace


def test_start_then_end_job(capsys):
    start = importlib.import_module("coterie_agents.commands.start_job")
    end = importlib.import_module("coterie_agents.commands.end_job")

    ctx = SimpleNamespace(
        store={"Jet": {"name": "Jet", "role": "runner", "status": "idle", "tasks": []}}
    )

    # start a job
    start.run(["Jet", "Task A"], ctx)
    out1 = capsys.readouterr().out.lower()
    assert "jet" in out1 and ("start" in out1 or "began" in out1 or "running" in out1)

    # end the job
    end.run(["Jet"], ctx)
    out2 = capsys.readouterr().out.lower()
    assert "jet" in out2 and ("end" in out2 or "done" in out2 or "stopp" in out2)
