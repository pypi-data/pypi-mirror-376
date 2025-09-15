from __future__ import annotations

import importlib

from coterie_agents.types import Crew


def test_start_sets_busy_and_task() -> None:
    start = importlib.import_module("coterie_agents.commands.start_job")
    member: Crew = {"name": "Mixie", "role": "runner", "status": "idle", "tasks": []}
    try:
        updated = start.run(member, "Mop floors")  # type: ignore[misc]
    except TypeError:
        updated = start.run(["Mixie", "Mop floors"], {"env": {}})  # type: ignore[misc]
    assert str(updated.get("status", "")).lower() in ("busy", "working")
    assert updated.get("tasks") and updated["tasks"][0].lower().startswith("mop")


def test_end_clears_or_marks_done() -> None:
    # Skip this test - end_job now uses state synchronization utilities
    # and doesn't support the old context-based API
    # The new implementation is tested in test_cmd_end_job_minimal.py
    import pytest

    pytest.skip("end_job now uses state synchronization - see test_cmd_end_job_minimal.py")
