from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal


def _queue_minutes_for(assignee: str, crew_status: dict[str, Any]) -> int:
    # sum durations of "queued" or "in-progress" tasks for this assignee
    minutes = 0
    for job in crew_status.get("jobs", []):
        if job.get("assignee", "").lower() == assignee.lower() and job.get("status") in {
            "queued",
            "in-progress",
        }:
            minutes += int(job.get("duration_minutes", 0))
    return minutes


def apply_auto_defaults(payload: dict[str, Any], crew_status: dict[str, Any]) -> dict[str, Any]:
    """
    payload keys: 'assignees' list[str], 'duration_minutes' (int|None|"auto"),
    'priority' (str|None|"auto"), optional 'tag' (str), optional 'base_minutes' (int)
    """
    out = payload.copy()
    tag = out.get("tag") or None
    base = out.get("base_minutes")
    auto_dur = (
        str(out.get("duration_minutes", "")).lower() == "auto"
        or out.get("duration_minutes") is None
    )
    auto_pri = str(out.get("priority", "")).lower() == "auto" or out.get("priority") is None

    assignees: list[str] = list(out.get("assignees", []))
    if not assignees:
        return out

    # Apply per-assignee suggestion; if multiple assignees, take the fastest suggestion (min minutes) and highest prio
    mins_list: list[int] = []
    prios: list[Priority] = []
    for who in assignees:
        qmin = _queue_minutes_for(who, crew_status)
        explicit_prio: Priority | None = None if auto_pri else (out.get("priority") or None)
        # Only allow valid Priority values
        if explicit_prio and explicit_prio not in ("low", "normal", "high", "urgent"):
            explicit_prio = None
        minutes, prio = suggest(
            persona=who,
            base_minutes=base if isinstance(base, int) else None,
            queue_minutes_for_persona=qmin,
            tag=tag,
            explicit_priority=explicit_prio,
        )
        mins_list.append(minutes)
        prios.append(prio)

    if auto_dur:
        out["duration_minutes"] = min(mins_list)
    if auto_pri:
        order: list[Priority] = ["low", "normal", "high", "urgent"]
        out["priority"] = max(prios, key=lambda p: order.index(p))

    out["persona_policy"] = {
        a: {"speed": PERSONAS.get(a.lower(), PERSONAS["jet"]).speed} for a in assignees
    }
    return out


Priority = Literal["low", "normal", "high", "urgent"]


@dataclass(frozen=True)
class PersonaPolicy:
    name: str
    speed: float  # <1.0 is faster; >1.0 is slower
    quality_bias: int  # -2..+2; can be used later for QA routing
    default_priority: Priority
    focus: tuple[str, ...]  # tags: ("ops","qa","polish",...)


DEFAULTS: dict[str, PersonaPolicy] = {
    "jet": PersonaPolicy(
        "jet", speed=0.80, quality_bias=0, default_priority="high", focus=("ops",)
    ),
    "mixie": PersonaPolicy(
        "mixie",
        speed=1.05,
        quality_bias=+1,
        default_priority="normal",
        focus=("qa", "polish"),
    ),
    "emerald_ghost": PersonaPolicy(
        "emerald_ghost",
        speed=1.00,
        quality_bias=+2,
        default_priority="normal",
        focus=("polish", "docs"),
    ),
}


def _load_config() -> dict[str, PersonaPolicy]:
    paths = [
        Path.cwd() / "config" / "personas.json",
        Path.home() / ".coterie" / "personas.json",
    ]
    for p in paths:
        if p.exists():
            data = json.loads(p.read_text(encoding="utf-8"))
            out: dict[str, PersonaPolicy] = {}
            for k, v in data.items():
                prio_str = str(v.get("default_priority", "normal")).lower()
                prio: Priority = (
                    prio_str if prio_str in ("low", "normal", "high", "urgent") else "normal"
                )
                out[k.lower()] = PersonaPolicy(
                    name=k.lower(),
                    speed=float(v.get("speed", 1.0)),
                    quality_bias=int(v.get("quality_bias", 0)),
                    default_priority=prio,
                    focus=tuple(map(str, v.get("focus", []))),
                )
            return out
    return {}


PERSONAS: dict[str, PersonaPolicy] = DEFAULTS | _load_config()


def suggest(
    *,
    persona: str,
    base_minutes: int | None,
    queue_minutes_for_persona: int,
    tag: str | None = None,
    explicit_priority: Priority | None = None,
) -> tuple[int, Priority]:
    """
    Returns (duration_minutes, priority) suggestion.
    - If base_minutes is None, assume 60 baseline.
    - Persona speed scales duration: floor(base * speed)
    - If the tag matches persona focus, apply a small speed bonus (0.9x).
    - If queue backlog > 240m, bump one priority level (max urgent).
    - Respect explicit_priority if provided.
    """
    pol = PERSONAS.get(
        persona.lower(),
        DEFAULTS.get(persona.lower(), PersonaPolicy(persona.lower(), 1.0, 0, "normal", ())),
    )
    base = base_minutes if base_minutes is not None else 60
    eff_speed = pol.speed
    if tag and tag in pol.focus:
        eff_speed *= 0.90  # focus bonus
    minutes = max(15, int(base * eff_speed))

    prio = explicit_priority or pol.default_priority

    # bump for backlog
    if queue_minutes_for_persona >= 240:
        prio = _bump_priority(prio)

    return minutes, prio


def _bump_priority(p: Priority) -> Priority:
    order: list[Priority] = ["low", "normal", "high", "urgent"]
    i = min(len(order) - 1, order.index(p) + 1)
    return order[i]
