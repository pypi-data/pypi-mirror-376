from types import SimpleNamespace

import coterie_agents.commands.email_summary as email_mod


def test_email_summary_success(monkeypatch):
    monkeypatch.setattr(email_mod, "send_email_summary", lambda *a, **kw: True)
    ctx = SimpleNamespace()
    result = email_mod.run(["recipient@example.com"], ctx)
    assert result is None or result == 0


def test_email_summary_failure(monkeypatch):
    monkeypatch.setattr(email_mod, "send_email_summary", lambda *a, **kw: False)
    ctx = SimpleNamespace()
    result = email_mod.run(["recipient@example.com"], ctx)
    assert result is None or result == 0
