import copy

import pytest

migrations = pytest.importorskip("coterie_agents.utils.migrations")


def _first_existing(*names: str):
    for n in names:
        fn = getattr(migrations, n, None)
        if callable(fn):
            return fn
    return None


def test_upgrade_member_shape_task_to_tasks_idempotent():
    legacy = {"name": "Jet", "role": "runner", "status": "idle", "task": "A"}
    fn = _first_existing(
        "upgrade_member_shape_task_to_tasks",
        "migrate_member_task_to_tasks",
        "upgrade_member_shape",
        "migrate_member",
    )
    if fn is None:
        pytest.skip("no matching migrator found")

    once = fn(copy.deepcopy(legacy))
    after = once if once is not None else legacy

    assert "tasks" in after and isinstance(after["tasks"], list)
    assert "A" in after["tasks"]
    assert "task" not in after

    twice = fn(copy.deepcopy(after))
    after2 = twice if twice is not None else after

    assert "tasks" in after2 and isinstance(after2["tasks"], list)
    assert "task" not in after2
    assert after2["tasks"].count("A") == after["tasks"].count("A")
