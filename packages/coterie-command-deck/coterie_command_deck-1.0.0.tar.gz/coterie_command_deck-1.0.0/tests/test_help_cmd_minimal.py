from __future__ import annotations

import importlib
from types import SimpleNamespace


class DummyRouter:
    def __init__(self):
        # Some implementations look at router.commands for targeted help
        self.commands = {"status": lambda *a, **k: None}

    def get_available_commands(self, verbose=True):
        return [("status", "Show crew status"), ("clean", "Clear tasks")]


def test_help_cmd_uses_router_table(capsys) -> None:
    mod = importlib.import_module("coterie_agents.commands.help_cmd")
    ctx = SimpleNamespace(router=DummyRouter())
    mod.run([], ctx)  # list all
    out = capsys.readouterr().out
    assert "Available Commands" in out
    assert "status" in out and "clean" in out


def test_help_cmd_specific_not_found(capsys) -> None:
    mod = importlib.import_module("coterie_agents.commands.help_cmd")
    ctx = SimpleNamespace(router=DummyRouter())
    mod.run(["nope"], ctx)
    out = capsys.readouterr().out.lower()
    assert "not found" in out


def test_help_cmd_specific_found(capsys) -> None:
    mod = importlib.import_module("coterie_agents.commands.help_cmd")

    class DummyRouter:
        commands = {"status": lambda *a, **k: None}

        def get_available_commands(self, verbose=True):
            return [("status", "Show crew status"), ("clean", "Clear tasks")]

    ctx = type("Ctx", (), {"router": DummyRouter()})()
    mod.run(["status"], ctx)
    out = capsys.readouterr().out
    assert "Show crew status" in out
