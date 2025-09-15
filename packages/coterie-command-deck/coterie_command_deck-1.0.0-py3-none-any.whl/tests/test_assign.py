from typing import Any

import pytest

from coterie_agents.commands.assign import run  # type: ignore


@pytest.mark.parametrize(
    "raw_input,args,expected",
    [
        (
            'assign Jet "SimpleTask"',
            ["Jet", "SimpleTask"],
            "[✅] Assigned to Jet: SimpleTask [Priority: medium]",
        ),
        (
            'assign A B "TwoCrewTask" --priority high',
            ["A", "B", "TwoCrewTask", "--priority", "high"],
            "[✅] Assigned to A: TwoCrewTask [Priority: high]",
        ),
    ],
)
def test_assign_basic(capsys: Any, raw_input: str, args: list[str], expected: str):
    # Prepare context with our dummy log_func and raw_input
    logs = []
    ctx = {
        "log_func": lambda cmd, a, details=None: logs.append((cmd, a, details or {})),  # type: ignore
        "raw_input": raw_input,
    }
    # Run the command
    run(args, ctx)  # type: ignore
    out = capsys.readouterr().out
    assert expected in out
    # Ensure logging happened
    assert any(entry[0] == "assign" for entry in logs)  # type: ignore
