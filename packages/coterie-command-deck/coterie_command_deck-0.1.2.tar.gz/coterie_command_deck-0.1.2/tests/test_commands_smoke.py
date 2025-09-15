from typing import Any


class _DummyResp:
    def __init__(self, payload: dict[str, Any] | None = None) -> None:
        self._payload = payload or {}

    def raise_for_status(self) -> None:
        return None
