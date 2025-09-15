from __future__ import annotations

from coterie_agents.validators import validate_crew, validate_store


def test_validate_crew_task_migrates_to_tasks() -> None:
    c = validate_crew({"name": "Jet", "role": "runner", "status": "busy", "task": "Wrap"})
    assert c["tasks"] == ["Wrap"]
    assert c["status"] == "busy"


def test_validate_store_list_to_mapping_and_unknown() -> None:
    s = validate_store(
        [
            {"name": "Mixie", "role": "chemist", "tasks": []},
            {"role": "tech", "task": "x"},
        ]
    )
    assert "Mixie" in s and "unknown" in s
    assert s["unknown"]["tasks"] == ["x"]
