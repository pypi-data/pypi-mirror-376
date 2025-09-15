from __future__ import annotations

from coterie_agents.utils.migrations import upgrade_member_shape, upgrade_store_shape


def test_upgrade_member_shape_task_to_tasks():
    up = upgrade_member_shape({"name": "Jet", "role": "runner", "task": "One-off"})
    assert up["tasks"] == ["One-off"]


def test_upgrade_store_shape_list_and_dict():
    up = upgrade_store_shape(
        [
            {"name": "A", "role": "r", "tasks": []},
            {"role": "r2", "task": "x"},
        ]
    )
    assert set(up.keys()) == {"A", "unknown"}
    assert up["unknown"]["tasks"] == ["x"]
