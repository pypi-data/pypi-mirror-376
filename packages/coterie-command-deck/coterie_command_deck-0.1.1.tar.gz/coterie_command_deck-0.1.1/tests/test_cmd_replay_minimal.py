"""Minimal smoke test for replay command."""

from __future__ import annotations

import json
import os
import tempfile
from unittest import mock

from coterie_agents.commands import replay


def test_replay_help():
    """Test replay command help."""
    result = replay.run(["--help"])
    assert result == 0


def test_replay_unknown_flag():
    """Test replay command with unknown flag."""
    result = replay.run(["--unknown"])
    assert result == 0


def test_replay_missing_id():
    """Test replay command with missing log ID."""
    result = replay.run([])
    assert result == 1


def test_replay_no_log_file():
    """Test replay command with no log file."""
    with tempfile.TemporaryDirectory() as temp_dir:
        log_file = os.path.join(temp_dir, "command_log.json")

        with mock.patch.object(replay, "LOG_FILE", log_file):
            result = replay.run(["1"])
            assert result == 0  # Should handle missing file gracefully


def test_replay_invalid_id():
    """Test replay command with invalid log ID."""
    with tempfile.TemporaryDirectory() as temp_dir:
        log_file = os.path.join(temp_dir, "command_log.json")

        sample_entries = [
            {
                "timestamp": "2025-09-12T08:30:00",
                "command": "history",
                "args": ["--limit", "5"],
            }
        ]

        with open(log_file, "w") as f:
            json.dump(sample_entries, f)

        with mock.patch.object(replay, "LOG_FILE", log_file):
            # Test non-existent ID
            result = replay.run(["999"])
            assert result == 1

            # Test invalid ID format
            result = replay.run(["invalid"])
            assert result == 1


def test_replay_read_only_command():
    """Test replay of read-only command (should work without --force)."""
    with tempfile.TemporaryDirectory() as temp_dir:
        log_file = os.path.join(temp_dir, "command_log.json")

        sample_entries = [
            {
                "id": 1,
                "timestamp": "2025-09-12T08:30:00",
                "command": "history",
                "args": ["--limit", "5"],
            }
        ]

        with open(log_file, "w") as f:
            json.dump(sample_entries, f)

        # Mock the command execution to avoid actually running commands
        with (
            mock.patch.object(replay, "LOG_FILE", log_file),
            mock.patch.object(replay, "_execute_command", return_value=0),
        ):
            result = replay.run(["1"])
            assert result == 0


def test_replay_state_changing_without_force():
    """Test replay of state-changing command without --force (should fail)."""
    with tempfile.TemporaryDirectory() as temp_dir:
        log_file = os.path.join(temp_dir, "command_log.json")

        sample_entries = [
            {
                "timestamp": "2025-09-12T08:30:00",
                "command": "book",  # State-changing command
                "args": ["Rig wash", "--at", "2025-09-15T08:30"],
            }
        ]

        with open(log_file, "w") as f:
            json.dump(sample_entries, f)

        with mock.patch.object(replay, "LOG_FILE", log_file):
            result = replay.run(["1"])
            assert result == 1  # Should fail without --force


def test_replay_state_changing_with_force():
    """Test replay of state-changing command with --force (should work)."""
    with tempfile.TemporaryDirectory() as temp_dir:
        log_file = os.path.join(temp_dir, "command_log.json")

        sample_entries = [
            {
                "timestamp": "2025-09-12T08:30:00",
                "command": "book",  # State-changing command
                "args": ["Rig wash", "--at", "2025-09-15T08:30"],
            }
        ]

        with open(log_file, "w") as f:
            json.dump(sample_entries, f)

        with (
            mock.patch.object(replay, "LOG_FILE", log_file),
            mock.patch.object(replay, "_execute_command", return_value=0),
        ):
            result = replay.run(["1", "--force"])
            assert result == 0


def test_replay_sanitize_sensitive_args():
    """Test that sensitive arguments are sanitized."""
    test_args = [
        "command",
        "--token",
        "secret123",
        "--password",
        "pass456",
        "--api-key",
        "key789",
        "normal_arg",
    ]

    sanitized = replay._sanitize_args(test_args)

    # Should keep normal args but filter sensitive ones
    assert "command" in sanitized
    assert "normal_arg" in sanitized
    assert "secret123" not in sanitized
    assert "pass456" not in sanitized
    assert "key789" not in sanitized
