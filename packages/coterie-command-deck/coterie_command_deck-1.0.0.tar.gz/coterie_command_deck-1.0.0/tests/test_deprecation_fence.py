import pytest

from coterie_agents.runtime_guard import configure_deprecation_handling


def test_deprecation_becomes_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AGENTS_DEPRECATION_STRICT", "1")
    configure_deprecation_handling()
    with pytest.raises(DeprecationWarning):
        import warnings

        warnings.warn("deprecated", DeprecationWarning, stacklevel=2)
