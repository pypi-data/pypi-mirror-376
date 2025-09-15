from __future__ import annotations

from typing import Any

from coterie_agents.utils.memory import load_memory, save_memory

from ._cli import has_unknown_flags, print_help, wants_help

COMMAND = "memory"
DESCRIPTION = "Shows or manages crew memory."
USAGE = f"{COMMAND} [<Crew>] [--clear] [--help]"


def run(argv: list[str] | None = None) -> int:
    argv = argv or []
    known_flags = {"--help", "-h"}

    if wants_help(argv):
        print_help(COMMAND, DESCRIPTION, USAGE)
        return 0
    if has_unknown_flags(argv, known_flags):
        print("Not found")
        print_help(COMMAND, DESCRIPTION, USAGE)
        return 0

    # clear memory
    if argv and argv[0] == "--clear":
        confirm = input("Clear all memory? (yes/no): ").strip().lower()
        if confirm in ("y", "yes"):
            save_memory({})
            print("[🗑️] Memory cleared.")
        else:
            print("[✋] Aborted.")
        return 0

    mem: dict[str, dict[str, Any]] = load_memory()
    if not mem:
        print("[📭] No crew memory found.")
        return 0

    if not argv:
        print("[📋] Crew in memory:")
        for name in sorted(mem.keys()):
            print(f"  🔹 {name}")
        return 0
    crew = argv[0]
    if crew not in mem:
        print(f"[⚠️] No memory for {crew}")
        return 0
    p: dict[str, Any] = mem[crew]
    print(f"[👤] {crew}")
    print("  Current tasks:")
    for t in p.get("tasks", []):
        t_str: str = str(t)
        print(f"   • {t_str}")
    print("  History:")
    for e in p["history"]:
        e_dict: dict[str, Any] = e
        ts: str = str(e_dict.get("ts", ""))
        task: str = str(e_dict.get("task", ""))
        pr: str = str(e_dict.get("priority", ""))
        print(f"   ↳ {ts} | {task} [priority: {pr}]")
    return 0
