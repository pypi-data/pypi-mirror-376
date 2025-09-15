"""Tests for error handling utilities."""

from __future__ import annotations

from coterie_agents.utils.errors import (
    NetworkError,
    PermanentError,
    RetryableError,
    TemporaryError,
    format_error_message,
    suggest_retry_command,
)


def test_error_hierarchy():
    """Test error class hierarchy."""
    # RetryableError should be base for specific retryable errors
    assert issubclass(NetworkError, RetryableError)
    assert issubclass(TemporaryError, RetryableError)

    # PermanentError should not be retryable
    assert not issubclass(PermanentError, RetryableError)


def test_format_error_message():
    """Test error message formatting."""
    error = ValueError("Invalid input")

    # Basic error message
    msg = format_error_message(error)
    assert "[❌] ValueError" in msg
    assert "Invalid input" in msg

    # With context
    msg = format_error_message(error, "book command")
    assert "in book command" in msg


def test_format_error_message_with_suggestions():
    """Test error message with contextual suggestions."""
    # Network error should suggest retries
    error = NetworkError("Connection failed")
    msg = format_error_message(error)
    assert "[💡] Try:" in msg
    assert "retries" in msg.lower()

    # File not found should suggest path verification
    error = FileNotFoundError("No such file")
    msg = format_error_message(error)
    assert "[💡] Try:" in msg
    assert "path" in msg.lower()


def test_suggest_retry_command():
    """Test retry command suggestion."""
    # Command without retries
    original = "deck book 'Rig wash' --at 2025-09-15T08:30"
    suggestion = suggest_retry_command(original, 3)
    assert "--retries 3" in suggestion

    # Command already has retries
    original_with_retries = "deck book 'Rig wash' --retries 5"
    suggestion = suggest_retry_command(original_with_retries)
    assert suggestion == original_with_retries
