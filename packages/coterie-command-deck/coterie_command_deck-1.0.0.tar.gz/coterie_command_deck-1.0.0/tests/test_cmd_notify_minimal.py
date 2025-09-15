"""Minimal test for notify command to ensure CLI compatibility."""

from __future__ import annotations

import os
from unittest import mock

from coterie_agents.commands.notify import run


def test_notify_help() -> None:
    """Test that notify --help works without error."""
    result = run(["--help"])
    assert result == 0


def test_notify_no_args() -> None:
    """Test that notify with no args shows error."""
    result = run([])
    assert result == 1


def test_notify_unknown_flag() -> None:
    """Test that notify handles unknown flags gracefully."""
    result = run(["--unknown"])
    assert result == 0


def test_notify_missing_recipient() -> None:
    """Test that notify requires --to recipient."""
    result = run(["Hello world"])
    assert result == 1


def test_notify_invalid_channel() -> None:
    """Test that notify rejects invalid channels."""
    result = run(["Hello", "--to", "user@example.com", "--channel", "invalid"])
    assert result == 1


def test_notify_dry_run_default() -> None:
    """Test that notify runs in DRY-RUN mode by default."""
    with mock.patch.dict(os.environ, {}, clear=True):
        result = run(["Hello world", "--to", "+1234567890"])
        assert result == 0


def test_notify_dry_run_explicit_false() -> None:
    """Test that notify runs in DRY-RUN mode when COMMS_ENABLED is false."""
    with mock.patch.dict(os.environ, {"COMMS_ENABLED": "false"}):
        result = run(["Test message", "--to", "user@example.com", "--channel", "email"])
        assert result == 0


@mock.patch("coterie_agents.commands.notify._send_sms")
def test_notify_real_sms(mock_send: mock.Mock) -> None:
    """Test that notify actually sends SMS when enabled."""
    with mock.patch.dict(os.environ, {"COMMS_ENABLED": "true"}):
        result = run(["Test SMS", "--to", "+1234567890", "--channel", "sms"])

        assert result == 0
        mock_send.assert_called_once_with("Test SMS", "+1234567890")


@mock.patch("coterie_agents.commands.notify._send_email")
def test_notify_real_email(mock_send: mock.Mock) -> None:
    """Test that notify actually sends email when enabled."""
    with mock.patch.dict(os.environ, {"COMMS_ENABLED": "true"}):
        result = run(["Test email", "--to", "user@example.com", "--channel", "email"])

        assert result == 0
        mock_send.assert_called_once_with("Test email", "user@example.com")


@mock.patch("coterie_agents.commands.notify._send_slack")
def test_notify_real_slack(mock_send: mock.Mock) -> None:
    """Test that notify actually sends Slack message when enabled."""
    with mock.patch.dict(os.environ, {"COMMS_ENABLED": "true"}):
        result = run(["Test Slack", "--to", "#general", "--channel", "slack"])

        assert result == 0
        mock_send.assert_called_once_with("Test Slack", "#general")


@mock.patch("coterie_agents.commands.notify._send_sms")
def test_notify_send_error(mock_send: mock.Mock) -> None:
    """Test that notify handles send errors gracefully."""
    mock_send.side_effect = Exception("Network error")

    with mock.patch.dict(os.environ, {"COMMS_ENABLED": "true"}):
        result = run(["Failed message", "--to", "+1234567890"])

        assert result == 1
        mock_send.assert_called_once_with("Failed message", "+1234567890")
