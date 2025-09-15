import json
import os
from typing import Any

# Define the default crew file location
CREW_FILE = os.getenv("CREW_FILE", "crew_status.json")  # Default to crew_status.json if not set


def load_crew() -> dict[str, Any]:
    if os.path.exists(CREW_FILE):
        try:
            with open(CREW_FILE) as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_crew(data: dict[str, Any]) -> None:
    tmp = CREW_FILE + ".tmp"
    with open(tmp, "w") as f:
        json.dump(data, f, indent=2)
    os.replace(tmp, CREW_FILE)


def ensure_crew(crew: dict[str, Any], names: list[str], autovivify: bool = True) -> dict[str, Any]:
    if not autovivify:
        return crew
    changed = False
    for n in names:
        if n not in crew:
            crew[n] = {"status": "READY", "tasks": [""], "priority": "NORMAL"}
            changed = True
    if changed:
        save_crew(crew)
    return crew
