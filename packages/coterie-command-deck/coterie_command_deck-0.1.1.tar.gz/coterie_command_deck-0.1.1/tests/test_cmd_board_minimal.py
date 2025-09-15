"""Minimal smoke test for board command."""

from __future__ import annotations

import json
import os
import tempfile
from unittest import mock

from coterie_agents.commands import board


def test_board_help():
    """Test board command help."""
    result = board.run(["--help"])
    assert result == 0


def test_board_unknown_flag():
    """Test board command with unknown flag."""
    result = board.run(["--unknown"])
    assert result == 0


def test_board_no_crew_file():
    """Test board command with no crew status file."""
    with tempfile.TemporaryDirectory() as temp_dir:
        crew_file = os.path.join(temp_dir, "crew_status.json")

        with mock.patch.object(board, "CREW_STATUS_FILE", crew_file):
            result = board.run([])
            assert result == 0  # Should handle missing file gracefully


def test_board_with_crew_data():
    """Test board command with sample crew data."""
    with tempfile.TemporaryDirectory() as temp_dir:
        crew_file = os.path.join(temp_dir, "crew_status.json")

        sample_data = {
            "crew": {
                "Jet": {
                    "role": "runner",
                    "status": "active",
                    "tasks": ["Rig wash", "Deck clean"],
                },
                "Mixie": {"role": "finisher", "status": "idle", "tasks": []},
            },
            "jobs": [
                {
                    "title": "Weekly maintenance",
                    "status": "pending",
                    "assignee": "unassigned",
                },
                {"title": "Equipment check", "status": "done", "assignee": "Jet"},
            ],
        }

        with open(crew_file, "w") as f:
            json.dump(sample_data, f)

        with mock.patch.object(board, "CREW_STATUS_FILE", crew_file):
            result = board.run([])
            assert result == 0


def test_board_empty_crew_data():
    """Test board command with empty crew data."""
    with tempfile.TemporaryDirectory() as temp_dir:
        crew_file = os.path.join(temp_dir, "crew_status.json")

        with open(crew_file, "w") as f:
            json.dump({}, f)

        with mock.patch.object(board, "CREW_STATUS_FILE", crew_file):
            result = board.run([])
            assert result == 0


def test_board_narrow_terminal():
    """Test board command with narrow terminal width."""
    with tempfile.TemporaryDirectory() as temp_dir:
        crew_file = os.path.join(temp_dir, "crew_status.json")

        sample_data = {"crew": {"Jet": {"role": "runner", "status": "active", "tasks": ["Task 1"]}}}

        with open(crew_file, "w") as f:
            json.dump(sample_data, f)

        with (
            mock.patch.object(board, "CREW_STATUS_FILE", crew_file),
            mock.patch.object(board, "_get_terminal_width", return_value=70),
        ):
            result = board.run([])
            assert result == 0
