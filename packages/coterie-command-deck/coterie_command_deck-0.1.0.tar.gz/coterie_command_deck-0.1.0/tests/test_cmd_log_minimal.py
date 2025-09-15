from __future__ import annotations

import importlib

from coterie_agents.types import Crew


def test_log_happy_path(capsys) -> None:
    mod = importlib.import_module("coterie_agents.commands.log")
    member: Crew = {"name": "Jet", "role": "runner", "status": "idle", "tasks": []}
    mod.run(["Jet", "did something"], {"store": {"Jet": member}})
    out = capsys.readouterr().out
    assert "Jet" in out and "did something" in out


def test_log_missing_member_noop(capsys) -> None:
    mod = importlib.import_module("coterie_agents.commands.log")
    mod.run(["Nope", "nothing"], {"store": {}})
    out = capsys.readouterr().out
    assert "Nope" in out and "not found" in out
