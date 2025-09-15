"""Minimal smoke test for history command."""

from __future__ import annotations

import json
import os
import tempfile
from unittest import mock

from coterie_agents.commands import history


def test_history_help():
    """Test history command help."""
    result = history.run(["--help"])
    assert result == 0


def test_history_unknown_flag():
    """Test history command with unknown flag."""
    result = history.run(["--unknown"])
    assert result == 0


def test_history_empty_log():
    """Test history command with empty log."""
    with tempfile.TemporaryDirectory() as temp_dir:
        log_file = os.path.join(temp_dir, "command_log.json")

        with mock.patch.object(history, "LOG_FILE", log_file):
            result = history.run([])
            assert result == 0


def test_history_with_entries():
    """Test history command with actual log entries."""
    with tempfile.TemporaryDirectory() as temp_dir:
        log_file = os.path.join(temp_dir, "command_log.json")

        # Create sample log entries
        sample_entries = [
            {
                "timestamp": "2025-09-12T08:30:00",
                "command": "book",
                "args": ["Rig wash", "--at", "2025-09-15T08:30"],
            },
            {
                "timestamp": "2025-09-12T09:15:00",
                "command": "assign",
                "args": ["Jet", "Clean deck"],
                "assignee": "Jet",
            },
        ]

        with open(log_file, "w") as f:
            json.dump(sample_entries, f)

        with mock.patch.object(history, "LOG_FILE", log_file):
            result = history.run(["--limit", "5"])
            assert result == 0


def test_history_filters():
    """Test history command with filters."""
    with tempfile.TemporaryDirectory() as temp_dir:
        log_file = os.path.join(temp_dir, "command_log.json")

        sample_entries = [
            {
                "timestamp": "2025-09-10T08:30:00",
                "command": "book",
                "args": ["Rig wash"],
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

        with mock.patch.object(history, "LOG_FILE", log_file):
            # Test assignee filter
            result = history.run(["--assignee", "Jet"])
            assert result == 0

            # Test contains filter
            result = history.run(["--contains", "wash"])
            assert result == 0

            # Test since filter
            result = history.run(["--since", "2025-09-11"])
            assert result == 0
