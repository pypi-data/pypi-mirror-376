from __future__ import annotations

# stdlib
import time
from collections.abc import Callable, MutableMapping
from typing import Any

# first-party
from ._cli import has_unknown_flags, print_help, wants_help


def _noop_debug_log(*_a: Any, **_k: Any) -> None:
    return None


debug_log: Callable[..., None] = _noop_debug_log

COMMAND = "assign"
DESCRIPTION = "Assign a task to one or more crew members (supports --priority)."
USAGE = f'{COMMAND} <name>... "task text" [--priority|-p <high|medium|low>]'

_PRIORITY_VALUES = {"high", "medium", "low"}


def _parse(argv: list[str]) -> tuple[list[str], str, str | None] | None:
    """Return (names, task_text, priority) or None if insufficient args."""
    names_and_task: list[str] = []
    priority: str | None = None
    i = 0
    while i < len(argv):
        tok = argv[i]
        if tok in ("--priority", "-p"):
            if i + 1 >= len(argv):
                return None
            priority = argv[i + 1].lower()
            i += 2
            continue
        names_and_task.append(tok)
        i += 1

    if len(names_and_task) < 2:
        return None
    task_text = names_and_task[-1]
    names = names_and_task[:-1]
    return (names, task_text, priority)


def _ensure_tasks(member: MutableMapping[str, Any]) -> list[dict[str, Any]]:
    tasks = member.get("tasks")
    if not isinstance(tasks, list):
        tasks = []
        member["tasks"] = tasks
    return tasks  # type: ignore[return-value]


def _already_has(tasks: list[dict[str, Any]] | list[str], text: str) -> bool:
    for t in tasks:
        if isinstance(t, dict) and t.get("text") == text:
            return True
        if isinstance(t, str) and t == text:  # legacy shape
            return True
    return False


def run(argv: list[str] | None = None, ctx: Any | None = None) -> int:
    argv = argv or []
    known_flags = {"--help", "-h", "--priority", "-p"}

    if wants_help(argv):
        print_help(COMMAND, DESCRIPTION, USAGE)
        return 0

    if has_unknown_flags(argv, known_flags):
        print("Not found")
        print_help(COMMAND, DESCRIPTION, USAGE)
        return 0

    parsed = _parse(argv)
    if not parsed:
        print_help(COMMAND, DESCRIPTION, USAGE)
        return 0

    names, task_text, priority = parsed
    if priority is not None and priority not in _PRIORITY_VALUES:
        print(f"[ℹ️] Unknown priority '{priority}'. Allowed: high, medium, low.")
        priority = None

    # resolve store from ctx
    store_obj: Any = getattr(ctx, "store", None) if ctx is not None else None
    if store_obj is None and isinstance(ctx, dict):
        store_obj = ctx.get("store")
    if not isinstance(store_obj, dict):
        print("[ℹ️] No crew store available.")
        return 0

    store: dict[str, dict[str, Any]] = store_obj  # type: ignore[assignment]

    assigned = 0
    ts = int(time.time())

    for name in names:
        member = store.get(name)
        if not isinstance(member, dict):
            print(f"{name}: not found")
            continue

        tasks = _ensure_tasks(member)
        if _already_has(tasks, task_text):
            print(f"[=] {name}: already has '{task_text}'")
            continue

        record: dict[str, Any] = {"text": task_text, "ts": ts}
        if priority:
            record["priority"] = priority
        tasks.append(record)
        assigned += 1

        if priority:
            print(f"[➕] {name}: assigned '{task_text}' (priority: {priority})")
        else:
            print(f"[➕] {name}: assigned '{task_text}'")

    if assigned == 0:
        debug_log(f"[ℹ️] assign: no assignments created for {names!r}")
    return 0
