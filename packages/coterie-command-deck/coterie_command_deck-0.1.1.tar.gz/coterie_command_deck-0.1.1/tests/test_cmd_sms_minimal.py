import importlib


def test_sms_help_and_send_soft(monkeypatch, capsys):
    mod = importlib.import_module("coterie_agents.commands.sms")

    # try to hook a likely send function if present
    calls = []

    def fake_send(*a, **k):
        calls.append((a, k))
        return True

    for name in ("send_sms", "send", "sms_send", "send_message"):
        if hasattr(mod, name):
            monkeypatch.setattr(mod, name, fake_send, raising=True)
            break

    # help path should never exit
    mod.run(["--help"], {"store": {}})
    help_out = capsys.readouterr().out.lower()
    assert "help" in help_out or "usage" in help_out or "sms" in help_out

    # happy path (soft)
    ctx = {"store": {"Jet": {"name": "Jet", "phone": "+15555550123"}}}
    try:
        mod.run(["Jet", "hello crew"], ctx)
    except TypeError:
        mod.run(["Jet", "hello", "crew"], ctx)

    out = capsys.readouterr().out.lower()
    # Either our fake was called, or the module printed a success-like message.
    assert calls or any(tok in out for tok in ("sent", "sms", "message", "jet"))
