from __future__ import annotations

from typing import Any

from coterie_agents.types import Crew, CrewStatus, CrewStore

_VALID: set[CrewStatus] = {"idle", "busy", "off", "unknown"}


def validate_crew(member: dict[str, Any]) -> Crew:
    """
    Coerce/validate arbitrary mapping into a canonical Crew TypedDict.
    Raises ValueError only if a required key is unrecoverable.
    """
    name = str(member.get("name", "unknown"))
    role = str(member.get("role", "worker"))
    status = member.get("status", "unknown")
    status = status if status in _VALID else "unknown"  # type: ignore[assignment]

    if "tasks" in member:
        tasks_raw = member["tasks"]
        if isinstance(tasks_raw, list):
            tasks = [str(t) for t in tasks_raw]
        else:
            tasks = [] if tasks_raw in (None, "", []) else [str(tasks_raw)]
    elif "task" in member:
        # migrate legacy 'task' to 'tasks' list
        task_val = member["task"]
        tasks = [] if task_val in (None, "", []) else [str(task_val)]
    else:
        tasks = []

    result: Crew = {"name": name, "role": role, "status": status, "tasks": tasks}

    # Optional fields
    if "attachments" in member and isinstance(member["attachments"], list):
        result["attachments"] = [str(x) for x in member["attachments"]]
    if "last_completed" in member:
        lc = member["last_completed"]
        result["last_completed"] = None if lc in (None, "") else str(lc)
    if "flag" in member:
        result["flag"] = bool(member["flag"])

    return result


def validate_store(store: dict[str, Any] | list[Any]) -> CrewStore:
    out: CrewStore = {}
    if isinstance(store, dict):
        for key, val in store.items():
            if isinstance(val, dict):
                c = validate_crew(val)
                out[c["name"] or str(key)] = c
    else:
        for item in store:
            if isinstance(item, dict):
                c = validate_crew(item)
                out[c["name"]] = c
    return out
