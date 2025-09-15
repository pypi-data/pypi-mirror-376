from __future__ import annotations

import json
import os
from collections.abc import Mapping
from typing import Any

from coterie_agents.types import Crew

from ._cli import has_unknown_flags, print_help, safe_ctx_store, wants_help

# Constants
CREW_FILE = "crew_status.json"
USAGE_STR = "[!!] Usage: update <crew_member> <field> <value>"


def _resolve_store_path(context_or_path: Any) -> str:
    if isinstance(context_or_path, str):
        return context_or_path
    if isinstance(context_or_path, Mapping):
        sp = context_or_path.get("store_path")
        if isinstance(sp, str) and sp:
            return sp
        env = context_or_path.get("env") if isinstance(context_or_path.get("env"), Mapping) else {}
        if isinstance(env, Mapping):
            env_path = env.get("CREW_FILE") or env.get("STORE_PATH")
            if isinstance(env_path, str) and env_path:
                return env_path
    return CREW_FILE


def _load_store(context_or_path: Any) -> dict[str, Crew]:
    path = _resolve_store_path(context_or_path)
    if not os.path.exists(path):
        return {}
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _save_store(context_or_path: Any, store: dict[str, Crew]) -> None:
    path = _resolve_store_path(context_or_path)
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(store, f, indent=2, ensure_ascii=False)


def _coerce_args(*pargs: Any, **kwargs: Any) -> tuple[list[str], dict[str, Any]]:
    ctx: dict[str, Any] = {}
    pos = list(pargs)
    if pos and isinstance(pos[-1], Mapping):
        cand = pos[-1]
        if any(k in cand for k in ("env", "args", "store_path")):
            ctx = dict(cand)
            pos = pos[:-1]
    if "context" in kwargs and isinstance(kwargs["context"], Mapping):
        ctx = dict(kwargs["context"])
    argv: list[str] = []
    if pos and isinstance(pos[0], list | tuple):
        argv = [str(x) for x in pos[0]]
    elif pos and isinstance(pos[0], Mapping) and "args" in pos[0]:
        argv = [str(x) for x in (pos[0]["args"] or [])]
    elif "args" in kwargs and isinstance(kwargs["args"], list | tuple):
        argv = [str(x) for x in kwargs["args"]]
    return argv, ctx


COMMAND = "update"
DESCRIPTION = "Update a crew member's field to a value."
USAGE = f"{COMMAND} <crew_member> <field> <value> [--help]"


def run(argv: list[str] | None = None, ctx: object = None) -> int:
    argv = argv or []
    known_flags = {"--help", "-h"}

    if wants_help(argv):
        print_help(COMMAND, DESCRIPTION, USAGE)
        return 0

    if has_unknown_flags(argv, known_flags):
        print("Not found")
        print_help(COMMAND, DESCRIPTION, USAGE)
        return 0

    if len(argv) < 3:
        print_help(COMMAND, DESCRIPTION, USAGE)
        return 0

    name, field, value = argv[:3]
    store = safe_ctx_store(ctx)
    if name not in store:
        print(f"[⚠️] {name} not found in crew store.")
        return 0
    store[name][field] = value
    print(f"[✅] Updated {name}: set {field} to {value}")
    return new_func()


def new_func():
    return 0
