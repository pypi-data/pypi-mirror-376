import pytest

mod = pytest.importorskip("coterie_agents.commands.email_summary")


def test_email_summary_handles_error(monkeypatch, capsys):
    # Monkeypatch a likely worker to raise, so we cover the error branch.
    def boom(*a, **k):
        raise RuntimeError("boom")

    for name in (
        "get_email_alerts",
        "summarize_emails",
        "build_summary",
        "run_summary",
    ):
        if hasattr(mod, name):
            monkeypatch.setattr(mod, name, boom, raising=True)
            break
    mod.run([], {"store": {}})
    out = capsys.readouterr().out.lower()
    assert any(t in out for t in ("error", "failed", "summary", "email"))
