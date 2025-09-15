from __future__ import annotations

from coterie_agents.types import Crew
from coterie_agents.utils.helper_funcs import (
    add_task,
    primary_task,
    resolve_crew_name,
    set_primary_task,
)


def test_tasks_helpers_roundtrip():
    m: Crew = {"name": "Jet", "role": "runner", "status": "idle", "tasks": []}
    assert primary_task(m) is None
    add_task(m, "Wipe down rig")
    assert primary_task(m) == "Wipe down rig"
    set_primary_task(m, "Re-wrap hoses")
    assert m["tasks"] == ["Re-wrap hoses"]


def test_resolve_crew_name_with_alias():
    name = resolve_crew_name("jet", known=["Jet", "Mixie"])
    assert name == "Jet"
