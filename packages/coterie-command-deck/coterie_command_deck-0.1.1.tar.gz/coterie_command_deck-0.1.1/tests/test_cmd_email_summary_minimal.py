import importlib


def test_email_summary_help_and_run_soft(monkeypatch, capsys):
    mod = importlib.import_module("coterie_agents.commands.email_summary")

    # monkeypatch one of several likely processing fns if present
    def fake_summary(*a, **k):
        return "Summary: 2 unread, 1 flagged"

    for name in (
        "get_email_alerts",
        "summarize_emails",
        "build_summary",
        "run_summary",
    ):
        if hasattr(mod, name):
            monkeypatch.setattr(mod, name, fake_summary, raising=True)
            break

    # help should be safe
    code = mod.run(["--help"])
    out = capsys.readouterr().out
    assert code == 0
    assert "email" in out.lower()
    assert "usage" in out.lower()

    # run with a tiny inbox-like context; modules usually tolerate empty/loose ctx
    code = mod.run([])
    out = capsys.readouterr().out
    assert "usage" in out.lower()
    assert code == 0
