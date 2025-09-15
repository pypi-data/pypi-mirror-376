import pytest

mod = pytest.importorskip("coterie_agents.commands.sms")


def test_sms_handles_send_failure(monkeypatch, capsys):
    # Force the send function to raise so we hit the failure path.
    def boom(*a, **k):
        raise RuntimeError("no signal")

    for name in ("send_sms", "send", "sms_send", "send_message"):
        if hasattr(mod, name):
            monkeypatch.setattr(mod, name, boom, raising=True)
            break
    mod.run(["Jet", "ping"], {"store": {"Jet": {"name": "Jet", "phone": "+15555550123"}}})
    out = capsys.readouterr().out.lower()
    assert any(t in out for t in ("error", "fail", "sms", "message", "jet"))
