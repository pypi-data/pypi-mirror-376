import tempfile

from src.coterie_agents.commands import sync_calendar


def test_sync_calendar_help(capsys):
    code = sync_calendar.run(["--help"], None)
    out = capsys.readouterr().out
    assert code == 0
    assert "calendar" in out.lower()
    assert "usage" in out.lower()


def test_sync_calendar_no_token(monkeypatch, capsys):
    with tempfile.NamedTemporaryFile() as tmp:
        monkeypatch.setattr(sync_calendar, "TOKEN_PATH", sync_calendar.Path(tmp.name))
        code = sync_calendar.run([], None)
        out = capsys.readouterr().out
        assert "no token found" in out.lower()
        assert code is None
