from __future__ import annotations

import importlib

from coterie_agents.types import Crew


def test_view_prints_basic(capsys) -> None:
    mod = importlib.import_module("coterie_agents.commands.view")
    member: Crew = {"name": "Jet", "role": "runner", "status": "idle", "tasks": ["A"]}
    # Try flexible call styles
    try:
        mod.run(member)  # type: ignore[misc]
    except TypeError:
        mod.run([], {"member": member})  # type: ignore[misc]
    out = capsys.readouterr().out
    assert "Jet" in out


def test_view_prints_fallback(capsys) -> None:
    mod = importlib.import_module("coterie_agents.commands.view")
    # Call with no member, should print fallback message
    try:
        mod.run([])  # type: ignore[misc]
    except Exception:
        mod.run([], {})  # type: ignore[misc]
    out = capsys.readouterr().out
    assert "No member" in out or "not found" in out or "crew" in out
