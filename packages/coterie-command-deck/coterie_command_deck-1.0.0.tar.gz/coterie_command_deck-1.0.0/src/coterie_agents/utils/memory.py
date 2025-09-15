import json
from datetime import datetime

from filelock import FileLock

from coterie_agents.utils.config import DATA_DIR, MEMORY_FILE


def load_memory():
    lock = FileLock(str(MEMORY_FILE) + ".lock")
    with lock:
        if MEMORY_FILE.exists():
            return {}  # Updated to use correct type annotation
        return {}


def save_memory(mem: dict):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    lock = FileLock(str(MEMORY_FILE) + ".lock")
    with lock:
        MEMORY_FILE.write_text(json.dumps(mem, indent=2))  # Updated to use correct type annotation


def add_task(crew: str, task: str, priority: str):
    mem = load_memory()
    from coterie_agents.utils.helper_funcs import add_task as add_task_helper

    entry = {"task": task, "priority": priority, "ts": datetime.now().isoformat()}
    person = mem.setdefault(crew, {"tasks": [], "history": []})
    add_task_helper(crew, task)
    person["history"].append(entry)
    save_memory(mem)
