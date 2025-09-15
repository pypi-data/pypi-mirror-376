from agents.commands.end_job import run as end_run
from agents.commands.start_job import run as start_run


def test_start_end_job_basic(capsys, tmp_path, monkeypatch):
    logs = []
    ctx = {"log_func": lambda cmd, a, details=None: logs.append((cmd, a, details or {}))}

    # Start Jet
    start_run(["Jet", "SimpleTask"], ctx)
    out = capsys.readouterr().out
    assert "[✅] Job 'SimpleTask' started for Jet" in out

    # End Jet
    end_run(["Jet"], ctx)
    out2 = capsys.readouterr().out
    assert "[✅] Job ended for Jet" in out2
    assert "Duration:" in out2

    # Logging happened
    kinds = [k for (k, _, __) in logs]
    assert "start_job" in kinds
    assert "end_job" in kinds
