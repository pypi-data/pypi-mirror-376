"""Minimal test for end_job command to ensure CLI compatibility."""

from __future__ import annotations

from unittest import mock

from coterie_agents.commands.end_job import run


def test_end_job_help() -> None:
    """Test that end_job --help works without error."""
    result = run(["--help"])
    assert result == 0


def test_end_job_no_args() -> None:
    """Test that end_job with no args shows error."""
    result = run([])
    assert result == 1


def test_end_job_unknown_flag() -> None:
    """Test that end_job handles unknown flags gracefully."""
    result = run(["--unknown"])
    assert result == 0


@mock.patch("coterie_agents.utils.state_store.ensure_idempotent_end_job")
def test_end_job_success(mock_end_job: mock.Mock) -> None:
    """Test successful end_job execution."""
    mock_end_job.return_value = True  # State was changed

    result = run(["alice"])

    assert result == 0
    mock_end_job.assert_called_once_with("alice")


@mock.patch("coterie_agents.utils.state_store.ensure_idempotent_end_job")
def test_end_job_error(mock_end_job: mock.Mock) -> None:
    """Test end_job error handling."""
    mock_end_job.side_effect = Exception("Test error")

    result = run(["alice"])

    assert result == 1
    mock_end_job.assert_called_once_with("alice")
