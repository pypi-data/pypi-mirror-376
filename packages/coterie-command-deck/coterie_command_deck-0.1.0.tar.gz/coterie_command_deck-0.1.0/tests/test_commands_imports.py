from __future__ import annotations

import importlib
import pkgutil

import coterie_agents.commands as commands_pkg


def test_import_all_command_modules():
    # Import all submodules under coterie_agents.commands
    for m in pkgutil.iter_modules(commands_pkg.__path__, commands_pkg.__name__ + "."):
        importlib.import_module(m.name)
