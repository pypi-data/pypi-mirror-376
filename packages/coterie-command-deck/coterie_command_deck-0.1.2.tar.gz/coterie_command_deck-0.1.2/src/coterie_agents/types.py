from __future__ import annotations

from os import PathLike
from types import ModuleType
from typing import Any, Literal, NotRequired, Protocol, TypedDict

# --- core enums/aliases ---
CrewStatus = Literal["idle", "busy", "off", "unknown"]
Status = CrewStatus  # alias if some files import Status instead


# --- data shapes ---
class Crew(TypedDict):
    name: str
    role: str
    status: CrewStatus
    tasks: list[str]
    # optional/extended fields used around the codebase
    flag: NotRequired[bool]
    attachments: NotRequired[list[str]]
    last_completed: NotRequired[str | None]


CrewStore = dict[str, Crew]


# --- command router types ---
class CommandModule(Protocol):
    def run(self, *args: Any, **kwargs: Any) -> Any: ...


CommandMap = dict[str, ModuleType | CommandModule]  # flexible for modules or Protocol


# --- shared dict/path types ---
JSONDict = dict[str, Any]
__all__ = ["JSONDict"]
StrPath = str | PathLike[str]
