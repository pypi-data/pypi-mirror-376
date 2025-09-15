from coterie_agents.utils.memory import load_memory, save_memory


def run(args, context):
    """
    Shows or manages crew memory.
    Usage:
      memory             – list all crew members
      memory <Crew>      – show that member’s state
      memory --clear     – reset all memory
    """
    # clear memory
    if args and args[0] == "--clear":
        confirm = input("Clear all memory? (yes/no): ").strip().lower()
        if confirm in ("y", "yes"):
            save_memory({})
            print("[🗑️] Memory cleared.")
        else:
            print("[✋] Aborted.")
        return

    mem = load_memory()
    if not args:
        for name in sorted(mem):
            print(f"Crew: {name}")
            p = mem[name]
            print(f"  Tasks: {p.get('tasks', [])}")
            print("  History:")
            for e in p["history"]:
                ts = e.get("ts", "")
                task = e.get("task", "")
                pr = e.get("priority", "")
                print(f"    {ts}: {task} (Priority: {pr})")
    else:
        crew = args[0]
        if crew in mem:
            p = mem[crew]
            print(f"Crew: {crew}")
            print(f"  Tasks: {p.get('tasks', [])}")
            print("  History:")
            for e in p["history"]:
                ts = e.get("ts", "")
                task = e.get("task", "")
                pr = e.get("priority", "")
                print(f"    {ts}: {task} (Priority: {pr})")
        else:
            print(f"Crew {crew} not found.")
