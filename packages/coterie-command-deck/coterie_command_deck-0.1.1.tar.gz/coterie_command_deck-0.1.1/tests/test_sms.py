import pytest

import coterie_agents.commands.sms as sms_mod
from coterie_agents.types import JSONDict


def test_sms_success(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        sms_mod,
        "send_sms",
        lambda *a: True,  # type: ignore[no-untyped-def]
    )
    ctx: JSONDict = {}
    result = sms_mod.run(["1234567890", "Test message"], ctx)
    assert result is None or result == 0


def test_sms_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        sms_mod,
        "send_sms",
        lambda *a: False,  # type: ignore[no-untyped-def]
    )
    ctx: JSONDict = {}
    result = sms_mod.run(["1234567890", "Test message"], ctx)
    assert result is None or result == 0
