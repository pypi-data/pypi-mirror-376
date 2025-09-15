from __future__ import annotations

import os
from pathlib import Path
from typing import Final

# Base directories first
DATA_DIR: Final[Path] = Path(os.environ.get("COTERIE_DATA_DIR", "data")).resolve()
LOG_DIR: Final[Path] = Path(os.environ.get("COTERIE_LOG_DIR", "coterie_ops/logs")).resolve()

# Files derived from directories
MEMORY_FILE: Final[Path] = DATA_DIR / "memory.json"

# Debug flags
DEBUG_LOG_TO_FILE: bool = False
DEBUG_MODE: bool = False

# Aliases (your existing map)
CREW_ALIASES: dict[str, str] = {
    "jet": "Jet",
    "jetty": "Jet",
    "mizz": "Mizz Micro",
    "mixie": "Mixie",
    "emerald": "Emerald Ghost",
    "emerald ghost": "Emerald Ghost",
    "og": "OG Shine",
    "og shine": "OG Shine",
}
KNOWN_CREW_ALIASES: dict[str, str] = CREW_ALIASES
