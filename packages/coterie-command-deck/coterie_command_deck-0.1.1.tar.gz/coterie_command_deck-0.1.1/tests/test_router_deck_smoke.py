from __future__ import annotations

import importlib


def test_import_command_router():
    importlib.import_module("coterie_agents.command_router")


def test_import_command_deck():
    importlib.import_module("coterie_agents.command_deck")
