from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from coterie_agents.types import Crew, CrewStatus, CrewStore, StrPath
from coterie_agents.validators import validate_crew, validate_store

_VALID_STATUS: set[CrewStatus] = {"idle", "busy", "off", "unknown"}
DEFAULT_PATH = Path.home() / "Documents" / "coterie_ops" / "crew_status.json"


def upgrade_member_shape(raw: dict[str, Any]) -> Crew:
    return validate_crew(raw)


def upgrade_store_shape(store_raw: dict[str, Any] | list[Any]) -> CrewStore:
    return validate_store(store_raw)


def migrate_json_file(path: StrPath | None = None) -> CrewStore:
    """
    Load, upgrade shape, and persist back atomically.
    Returns the upgraded CrewStore mapping.
    """
    p = Path(path) if path else DEFAULT_PATH
    p.parent.mkdir(parents=True, exist_ok=True)

    if not p.exists():
        p.write_text("{}", encoding="utf-8")
        return {}

    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        # backup corrupt file and start clean
        bak = p.with_suffix(p.suffix + ".bak")
        p.replace(bak)
        p.write_text("{}", encoding="utf-8")
        return {}

    upgraded = upgrade_store_shape(data)

    tmp = p.with_suffix(p.suffix + ".tmp")
    tmp.write_text(json.dumps(upgraded, indent=2, ensure_ascii=False), encoding="utf-8")
    tmp.replace(p)

    return upgraded
