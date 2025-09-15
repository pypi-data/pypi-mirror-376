"""Minimal smoke test for view command."""

from __future__ import annotations

import json
import os
import tempfile
from unittest import mock

from coterie_agents.commands import view


def test_view_help():
    """Test view command help."""
    result = view.run(["--help"])
    assert result == 0


def test_view_unknown_flag():
    """Test view command with unknown flag."""
    result = view.run(["--unknown"])
    assert result == 0


def test_view_missing_id():
    """Test view command with missing log ID."""
    result = view.run([])
    assert result == 1


def test_view_no_log_file():
    """Test view command with no log file."""
    with tempfile.TemporaryDirectory() as temp_dir:
        log_file = os.path.join(temp_dir, "command_log.json")

        with mock.patch.object(view, "LOG_FILE", log_file):
            result = view.run(["1"])
            assert result == 0  # Should handle missing file gracefully


def test_view_invalid_id():
    """Test view command with invalid log ID."""
    with tempfile.TemporaryDirectory() as temp_dir:
        log_file = os.path.join(temp_dir, "command_log.json")

        sample_entries = [
            {
                "timestamp": "2025-09-12T08:30:00",
                "command": "book",
                "args": ["Rig wash", "--at", "2025-09-15T08:30"],
            }
        ]

        with open(log_file, "w") as f:
            json.dump(sample_entries, f)

        with mock.patch.object(view, "LOG_FILE", log_file):
            # Test non-existent ID
            result = view.run(["999"])
            assert result == 1

            # Test invalid ID format
            result = view.run(["invalid"])
            assert result == 1


def test_view_valid_entry():
    """Test view command with valid log entry."""
    with tempfile.TemporaryDirectory() as temp_dir:
        log_file = os.path.join(temp_dir, "command_log.json")

        sample_entries = [
            {
                "id": 1,
                "timestamp": "2025-09-12T08:30:00",
                "command": "book",
                "args": ["Rig wash", "--at", "2025-09-15T08:30"],
                "assignee": "Jet",
            },
            {
                "timestamp": "2025-09-12T09:15:00",
                "command": "assign",
                "args": ["Mixie", "Polish deck"],
                "assignee": "Mixie",
            },
        ]

        with open(log_file, "w") as f:
            json.dump(sample_entries, f)

        with mock.patch.object(view, "LOG_FILE", log_file):
            # Test by explicit ID
            result = view.run(["1"])
            assert result == 0

            # Test by index (1-based)
            result = view.run(["2"])
            assert result == 0


def test_view_dict_format():
    """Test view command with dict-format log file."""
    with tempfile.TemporaryDirectory() as temp_dir:
        log_file = os.path.join(temp_dir, "command_log.json")

        sample_data = {
            "entries": [
                {
                    "timestamp": "2025-09-12T08:30:00",
                    "command": "book",
                    "args": ["Rig wash"],
                }
            ]
        }

        with open(log_file, "w") as f:
            json.dump(sample_data, f)

        with mock.patch.object(view, "LOG_FILE", log_file):
            result = view.run(["1"])
            assert result == 0
