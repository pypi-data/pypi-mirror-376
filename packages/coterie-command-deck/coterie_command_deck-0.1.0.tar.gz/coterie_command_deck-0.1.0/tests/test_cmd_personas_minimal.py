"""Minimal tests for persona commands to ensure CLI compatibility."""

from __future__ import annotations

import os
from unittest import mock

from coterie_agents.commands.create_persona import run as create_run
from coterie_agents.commands.list_personas import run as list_run


def test_create_persona_help() -> None:
    """Test that create_persona --help works without error."""
    result = create_run(["--help"])
    assert result == 0


def test_create_persona_no_args() -> None:
    """Test that create_persona with no args shows error."""
    result = create_run([])
    assert result == 1


def test_create_persona_dry_run() -> None:
    """Test that create_persona runs in DRY-RUN mode by default."""
    with mock.patch.dict(os.environ, {}, clear=True):
        result = create_run(["alice", "--role", "cleaner", "--skills", "deep-clean,windows"])
        assert result == 0


@mock.patch("coterie_agents.commands.create_persona._create_persona")
def test_create_persona_enabled(mock_create: mock.Mock) -> None:
    """Test that create_persona works when enabled."""
    with mock.patch.dict(os.environ, {"PERSONAS_ENABLED": "true"}):
        result = create_run(["bob", "--role", "runner", "--availability", "M-F 9-5"])

        assert result == 0
        mock_create.assert_called_once_with("bob", "runner", None, "M-F 9-5")


@mock.patch("coterie_agents.commands.create_persona._create_persona")
def test_create_persona_error(mock_create: mock.Mock) -> None:
    """Test that create_persona handles errors gracefully."""
    mock_create.side_effect = Exception("Database error")

    with mock.patch.dict(os.environ, {"PERSONAS_ENABLED": "true"}):
        result = create_run(["alice", "--role", "cleaner"])

        assert result == 1


def test_list_personas_help() -> None:
    """Test that list_personas --help works without error."""
    result = list_run(["--help"])
    assert result == 0


def test_list_personas_dry_run() -> None:
    """Test that list_personas runs in DRY-RUN mode by default."""
    with mock.patch.dict(os.environ, {}, clear=True):
        result = list_run([])
        assert result == 0


def test_list_personas_with_filters() -> None:
    """Test that list_personas handles filters in DRY-RUN mode."""
    with mock.patch.dict(os.environ, {}, clear=True):
        result = list_run(["--role", "cleaner", "--skills", "windows"])
        assert result == 0


def test_list_personas_with_member() -> None:
    """Test that list_personas handles member name in DRY-RUN mode."""
    with mock.patch.dict(os.environ, {}, clear=True):
        result = list_run(["alice"])
        assert result == 0


@mock.patch("coterie_agents.commands.list_personas._list_personas")
@mock.patch("coterie_agents.commands.list_personas._display_personas")
def test_list_personas_enabled(mock_display: mock.Mock, mock_list: mock.Mock) -> None:
    """Test that list_personas works when enabled."""
    mock_list.return_value = [{"name": "alice", "role": "cleaner"}]

    with mock.patch.dict(os.environ, {"PERSONAS_ENABLED": "true"}):
        result = list_run(["alice"])

        assert result == 0
        mock_list.assert_called_once_with("alice", None, None)
        mock_display.assert_called_once()


@mock.patch("coterie_agents.commands.list_personas._list_personas")
def test_list_personas_error(mock_list: mock.Mock) -> None:
    """Test that list_personas handles errors gracefully."""
    mock_list.side_effect = Exception("Storage error")

    with mock.patch.dict(os.environ, {"PERSONAS_ENABLED": "true"}):
        result = list_run([])

        assert result == 1
