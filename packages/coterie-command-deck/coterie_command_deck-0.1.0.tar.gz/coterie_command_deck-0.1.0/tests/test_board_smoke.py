from __future__ import annotations

from coterie_agents.commands import board
from coterie_agents.types import CrewStore


def test_board_print_crew_capsys(capsys):
    crew: CrewStore = {
        "Jet": {
            "name": "Jet",
            "role": "runner",
            "status": "busy",
            "tasks": ["Wrap hose"],
        },
        "Mixie": {"name": "Mixie", "role": "chemist", "status": "idle", "tasks": []},
    }
    # `_print_crew` is an internal helper but safe to call directly for smoke coverage.
    assert hasattr(board, "_print_crew")
    board._print_crew(crew)  # type: ignore[attr-defined]
    out = capsys.readouterr().out
    assert "Crew Board" in out
    assert "Jet" in out and "Mixie" in out
