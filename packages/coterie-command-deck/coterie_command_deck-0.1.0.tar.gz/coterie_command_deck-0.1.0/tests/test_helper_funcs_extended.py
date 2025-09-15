from coterie_agents.types import Crew
from coterie_agents.utils.helper_funcs import (
    add_task,
    primary_task,
    resolve_crew_name,
    set_primary_task,
)


def test_task_helpers_extend_and_replace() -> None:
    m: Crew = {"name": "Jet", "role": "runner", "status": "idle", "tasks": []}
    assert primary_task(m) is None
    add_task(m, "A")
    add_task(m, "B")
    assert primary_task(m) == "A"
    set_primary_task(m, "C")
    assert m["tasks"] == ["C"]


def test_resolve_crew_name_case_insensitive() -> None:
    assert resolve_crew_name("jet", known=["Jet", "Mixie"]) == "Jet"
