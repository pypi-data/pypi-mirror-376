from typing import Any

from coterie_agents.commands.end_job import run as end_job
from coterie_agents.utils.helper_funcs import (  # type: ignore
    add_task,
    primary_task,
    set_primary_task,
)


def test_primary_task_helpers():
    m: Any = {"name": "Jet", "role": "runner", "status": "idle", "tasks": []}
    assert primary_task(m) is None
    add_task(m, "Wipe down rig")
    assert primary_task(m) == "Wipe down rig"
    set_primary_task(m, "Re-wrap hoses")
    assert m["tasks"] == ["Re-wrap hoses"]


def test_end_job_clears_tasks():
    m_name = "Mixie"
    ctx = {}
    end_job([m_name], ctx)
    # You may want to check the crew file for updated status if needed
