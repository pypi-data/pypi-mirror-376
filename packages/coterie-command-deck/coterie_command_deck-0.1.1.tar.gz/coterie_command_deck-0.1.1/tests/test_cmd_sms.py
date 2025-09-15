from __future__ import annotations

import importlib


def test_sms_calls_service(monkeypatch) -> None:
    mod = importlib.import_module("coterie_agents.commands.sms")
    called = {}
    # Patch internal service call regardless of how module imports it
    if hasattr(mod, "send_sms"):
        monkeypatch.setattr(mod, "send_sms", lambda to, msg: called.setdefault("ok", (to, msg)))
    elif hasattr(mod, "sms_service"):
        monkeypatch.setattr(
            mod.sms_service,
            "send_sms",
            lambda to, msg: called.setdefault("ok", (to, msg)),
        )
    # Drive run with flexible signature
    try:
        mod.run(["+15551234567", "hi"], {"env": {}})  # type: ignore[misc]
    except TypeError:
        mod.run("+15551234567", "hi")  # type: ignore[misc]
    assert "ok" in called
