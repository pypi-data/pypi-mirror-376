from __future__ import annotations

import importlib

from coterie_agents.types import Crew


def test_edit_task_happy_path() -> None:
    mod = importlib.import_module("coterie_agents.commands.edit_task")
    member: Crew = {
        "name": "Jet",
        "role": "runner",
        "status": "idle",
        "tasks": ["A", "B"],
    }
    updated = mod.run(member, 1, "C")  # edit index 1
    assert updated["tasks"] == ["A", "C"]


def test_edit_task_index_out_of_range_noop() -> None:
    mod = importlib.import_module("coterie_agents.commands.edit_task")
    member: Crew = {"name": "Jet", "role": "runner", "status": "idle", "tasks": ["A"]}
    updated = mod.run(member, 5, "Z")  # out of range -> no change
    assert updated["tasks"] == ["A"]
