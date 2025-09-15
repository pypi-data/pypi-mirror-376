from coterie_agents.utils.migrations import upgrade_member_shape


def test_upgrade_member_migrates_task_to_tasks():
    raw = {"name": "Jet", "role": "runner", "status": "busy", "task": "Wipe down rig"}
    up = upgrade_member_shape(raw)
    assert "task" not in up
    assert up["tasks"] == ["Wipe down rig"]
    assert up["status"] == "busy"
