import importlib
import json
import pathlib
import sys
from pathlib import Path

import pytest

# Prepend src/ to sys.path for absolute imports
ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
p = str(SRC)
if p not in sys.path:
    sys.path.insert(0, p)

# Insert project root into sys.path so `import agents.*` works
ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


@pytest.fixture(autouse=True)
def crew_file_isolated(tmp_path, monkeypatch):
    # Set the environment variable for autovivification
    monkeypatch.setenv("CREW_AUTOCREATE", "1")

    # Create a temporary crew status file
    crew_file = tmp_path / "crew_status.json"

    # Seed the crew data to ensure strict handlers pass
    seed = {
        "Jet": {"status": "READY", "task": "—", "priority": "NORMAL"},
        "A": {"status": "READY", "task": "—", "priority": "NORMAL"},
        "B": {"status": "READY", "task": "—", "priority": "NORMAL"},
    }
    crew_file.write_text(json.dumps(seed, indent=2))

    # Patch each command's CREW_FILE to point to the temporary file
    modules_to_patch = [
        "agents.commands.assign",
        "agents.commands.start_job",
        "agents.commands.end_job",
    ]
    for modname in modules_to_patch:
        mod = importlib.import_module(modname)
        if hasattr(mod, "CREW_FILE"):
            monkeypatch.setattr(mod, "CREW_FILE", str(crew_file), raising=False)
        importlib.reload(mod)

    yield
