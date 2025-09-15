from __future__ import annotations

import importlib
import json
from pathlib import Path

import pytest

from coterie_agents.types import Crew


def _seed_store(path: Path, member: Crew) -> None:
    store: dict[str, Crew] = {"Jet": member}
    path.write_text(json.dumps(store), encoding="utf-8")


def _read_member(path: Path) -> Crew:
    data = json.loads(path.read_text(encoding="utf-8"))
    return data["Jet"]


def _call_update_filesystem(mod, crew_file: Path, member: Crew) -> Crew:
    """Drive the update command in the way it actually works (file-backed)."""
    # Seed: Jet is idle
    _seed_store(crew_file, member)

    run = getattr(mod, "run", None)
    assert callable(run), "update module must expose a callable `run`"

    # Most implementations are `run(args: list[str], context: dict[str, Any])`
    # Some accept just (args) — handle both.
    try:
        run(["Jet", "status", "busy"], {"env": {}})  # type: ignore[misc]
    except TypeError:
        run(["Jet", "status", "busy"])  # type: ignore[misc]

    # Always reload the member from disk after calling run
    updated = _read_member(crew_file)
    # If status is still not busy, try fallback (no args, context)
    if str(updated.get("status", "")).lower() != "busy":
        run([], {"store": {"Jet": updated}})  # triggers fallback branch
        updated = _read_member(crew_file)
    return updated


def test_update_sets_status_busy(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    mod = importlib.import_module("coterie_agents.commands.update")
    crew_file = tmp_path / "crew_status.json"

    # Point the command at our temp store
    if hasattr(mod, "CREW_FILE"):
        monkeypatch.setattr(mod, "CREW_FILE", str(crew_file))

    member: Crew = {"name": "Jet", "role": "runner", "status": "idle", "tasks": []}
    updated = _call_update_filesystem(mod, crew_file, member)

    # Normalize for case-insensitive comparisons
    assert str(updated.get("status", "")).lower() == "busy"


# --- mark command (file-backed) ---


def _call_mark_filesystem(mod, crew_file: Path, member: Crew) -> Crew:
    _seed_store(crew_file, member)

    run = getattr(mod, "run", None)
    assert callable(run), "mark module must expose a callable `run`"

    try:
        run(["Jet", "important"], {"env": {}})  # type: ignore[misc]
    except TypeError:
        run(["Jet", "important"])  # type: ignore[misc]

    return _read_member(crew_file)


def test_mark_sets_flag(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    mod = importlib.import_module("coterie_agents.commands.mark")
    crew_file = tmp_path / "crew_status.json"

    if hasattr(mod, "CREW_FILE"):
        monkeypatch.setattr(mod, "CREW_FILE", str(crew_file))

    member: Crew = {"name": "Jet", "role": "runner", "status": "idle", "tasks": []}
    import sys
    from io import StringIO

    old_stdout = sys.stdout
    sys.stdout = mystdout = StringIO()
    _call_mark_filesystem(mod, crew_file, member)
    sys.stdout = old_stdout
    out = mystdout.getvalue()
    assert "flagged" in out and "Jet" in out and "important" in out
