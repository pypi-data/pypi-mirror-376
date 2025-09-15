from __future__ import annotations

import importlib
import json

from coterie_agents.types import Crew


def test_clean_clears_tasks() -> None:
    # Import the command
    from coterie_agents.commands.clean import run as clean_run

    member: Crew = {
        "name": "Jet",
        "role": "runner",
        "status": "idle",
        "tasks": ["A", "B", "C"],
    }
    out = clean_run(member)  # API: run(member: Crew) -> Crew
    # Should clear tasks in place and return the same object
    assert out is member
    assert member["tasks"] == []


def test_status_prints_rows(tmp_path, capsys, monkeypatch) -> None:
    # Import the module so we can patch its CREW_FILE
    status_mod = importlib.import_module("coterie_agents.commands.status")

    # Build a tiny crew_status.json with at least one current task
    data: dict[str, Crew] = {
        "Jet": {
            "name": "Jet",
            "role": "runner",
            "status": "READY",
            "tasks": ["Wipe"],
            "last_completed": "SimpleTask",
        },
        "Mixie": {
            "name": "Mixie",
            "role": "runner",
            "status": "READY",
            "tasks": ["Rewrap"],
        },
    }
    crew_file = tmp_path / "crew_status.json"
    crew_file.write_text(json.dumps(data))

    # Point the command at our temp file
    monkeypatch.setattr(status_mod, "CREW_FILE", str(crew_file))

    # status.run takes (args, context). It doesn't use them, so pass dummies.
    status_mod.run([], {})  # type: ignore[arg-type]

    out = capsys.readouterr().out
    assert "Coterie Crew Status" in out
    assert "Jet" in out and "Wipe" in out
    assert "Mixie" in out and "Rewrap" in out


def test_status_handles_missing_file(tmp_path, capsys, monkeypatch) -> None:
    status_mod = importlib.import_module("coterie_agents.commands.status")

    # Point to a missing path
    missing = tmp_path / "missing.json"
    monkeypatch.setattr(status_mod, "CREW_FILE", str(missing))

    status_mod.run([], {})  # type: ignore[arg-type]
    out = capsys.readouterr().out
    # Loose assertion to avoid brittle exact string match
    assert "No crew" in out or "No crew_status" in out
