from __future__ import annotations

import json
import os
from collections.abc import Callable, Iterable
from datetime import datetime
from pathlib import Path
from typing import Any

try:
    from coterie_agents.types import JSONDict
except ImportError:
    JSONDict = dict


def primary_task(member: dict) -> str | None:
    tasks = member.get("tasks")
    return tasks[0] if isinstance(tasks, list) and tasks else None


def add_task(member: dict, text: str) -> None:
    tasks = list(member.get("tasks") or [])
    if text not in tasks:
        tasks.append(text)
    member["tasks"] = tasks


__all__ = [
    "debug_log",
    "primary_task",
    "set_primary_task",
    "add_task",
    "_read_json_entries",
    "_read_jsonl_entries",
    "load_crew_status",
    "save_crew_status",
    "log_command_to_json",
    "read_command_log",
    "normalize_name",
    "ensure_list",
    "resolve_crew_name",
    "main",
    "interactive_loop",
]


def _read_json_entries(path: Path) -> list[dict[str, Any]]:
    try:
        if path.suffix == ".jsonl":
            entries: list[dict[str, Any]] = []
            with path.open("r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    obj = json.loads(line)
                    if isinstance(obj, dict):
                        entries.append(obj)
            return entries
        # default: .json
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            return [x for x in data if isinstance(x, dict)]
        if isinstance(data, dict):
            return [data]
        return []
    except Exception:
        return []


def set_primary_task(member: dict, text: str) -> None:
    tasks = list(member.get("tasks") or [])
    if text not in tasks:
        tasks.append(text)
    member["tasks"] = tasks


command_log_json = Path(os.environ.get("COMMAND_LOG_JSON", "command_log.json")).resolve()
crew_aliases: dict[str, str] = {
    "og": "OG Shine",
    "micro": "Mizz Micro",
    "mix": "Mixie",
    "jet": "Jet",
}
debug_mode = False
info = "[i]"
ok = "[OK]"
reset = ""


# ---- Command log path (single source of truth) ----


def _read_jsonl_entries(jsonl_path: Path) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    try:
        with jsonl_path.open("r", encoding="utf-8") as f:
            for line in f:
                try:
                    obj = json.loads(line.strip())
                    entries.append(obj)
                except json.JSONDecodeError as e:
                    print(f"[\u274c] helper_funcs - bad JSONL entry: {line.strip()} error: {e}")
                    # S110: suppress block, log and continue
                    continue
    except Exception as e:
        print(f"[\u274c] helper_funcs - failed to read JSONL: {jsonl_path} error: {e}")
        # S110: suppress block, log and continue
    return entries


debug_log_to_file = False


# ------------------
# Crew Status Helpers
# ------------------


def load_crew_status() -> dict[str, dict]:
    p = Path("crew_status.json")
    try:
        if not p.exists():
            return {}
        with p.open() as f:
            data = json.load(f)
        return data
    except Exception as e:
        print(f"[\u274c] helper_funcs - failed to load crew status: {e}")
        # S110: suppress block, log and continue
        return {}


def save_crew_status(data: dict[str, dict]) -> None:
    p = Path("crew_status.json")
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# ---------------------
# Command Log Helpers
# ---------------------
def log_command_to_json(
    command: str, args: list[str] | tuple[str, ...], path: str | Path | None = None
) -> None:
    p = Path(path or command_log_json)
    p.parent.mkdir(parents=True, exist_ok=True)
    entry: dict[str, Any] = {
        "timestamp": datetime.now().isoformat(),
        "command": command,
        "args": list(args),
    }
    with p.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def read_command_log(limit: int | None = None) -> list[dict]:
    BASE_PATH = Path(__file__).parents[2]  # Go up to project root
    JSONL_PATH = BASE_PATH / "command_log.jsonl"
    JSON_PATH = BASE_PATH / "logs" / "command_log.json"

    if JSONL_PATH.exists():
        entries = _read_jsonl_entries(JSONL_PATH)
        if entries:
            return entries[-limit:] if limit is not None else entries
    if JSON_PATH.exists():
        data = _read_json_entries(JSON_PATH)
        return data[-limit:] if limit is not None else data
    return []


# -----------------------
# Debug Logging Helper
# -----------------------


def debug_log(message: str):
    """
    Print or save debug messages based on DEBUG settings.
    """
    if "debug_log_to_file" in globals() and debug_log_to_file:
        debug_path = os.path.normpath(
            os.path.join(os.path.dirname(__file__), os.pardir, os.pardir, "logs", "debug_log.txt")
        )
        os.makedirs(os.path.dirname(debug_path), exist_ok=True)
        with open(debug_path, "a") as f:
            f.write(f"{datetime.now().isoformat()} {message}\n")
    elif debug_mode:
        print(message)


# -----------------------
# Alias Resolution Helper
# -----------------------


def normalize_name(name: str) -> str:
    key = name.strip().lower()
    return crew_aliases.get(key, name).strip()


def ensure_list(x: str | list[str]) -> list[str]:
    return x if isinstance(x, list) else [x]


def resolve_crew_name(raw: str, known: Iterable[str] | None = None) -> str:
    candidate = normalize_name(raw)
    if known:
        lower_map = {k.lower(): k for k in known}
        return lower_map.get(candidate.lower(), candidate)
    return candidate


def main():
    print(f"{ok}[🔥] Welcome to the Coterie Command Deck.{reset}")
    print(f"{info}[⌨️] Type 'help' to see commands. 'exit' to quit.\n{reset}")
    # The main loop requires a handle_command function to be passed in from the caller.


def interactive_loop(handle_command: Callable[[str], None]) -> None:
    while True:
        try:
            input_str = input(">> ")
            handle_command(input_str)
        except KeyboardInterrupt:
            print("\n[OK] Ctrl+C detected. Exiting Command Deck.")
            break
        except BrokenPipeError:
            break
