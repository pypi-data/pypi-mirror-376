"""Minimal tests for payment commands to ensure CLI compatibility."""

from __future__ import annotations

import os
from unittest import mock

from coterie_agents.commands.generate_invoice import run as invoice_run
from coterie_agents.commands.process_payment import run as payment_run


def test_process_payment_help() -> None:
    """Test that process_payment --help works without error."""
    result = payment_run(["--help"])
    assert result == 0


def test_process_payment_no_args() -> None:
    """Test that process_payment with no args shows error."""
    result = payment_run([])
    assert result == 1


def test_process_payment_dry_run() -> None:
    """Test that process_payment runs in DRY-RUN mode by default."""
    with mock.patch.dict(os.environ, {}, clear=True):
        result = payment_run(["JOB001", "--amount", "250.00", "--method", "card"])
        assert result == 0


def test_process_payment_invalid_amount() -> None:
    """Test that process_payment handles invalid amounts."""
    result = payment_run(["JOB001", "--amount", "invalid"])
    assert result == 1


def test_process_payment_invalid_method() -> None:
    """Test that process_payment handles invalid payment methods."""
    result = payment_run(["JOB001", "--method", "crypto"])
    assert result == 1


@mock.patch("coterie_agents.commands.process_payment._process_payment")
def test_process_payment_enabled(mock_process: mock.Mock) -> None:
    """Test that process_payment works when enabled."""
    with mock.patch.dict(os.environ, {"PAYMENTS_ENABLED": "true"}):
        result = payment_run(["JOB001", "--amount", "150.00", "--method", "cash"])

        assert result == 0
        mock_process.assert_called_once_with("JOB001", 150.00, "cash")


@mock.patch("coterie_agents.commands.process_payment._process_payment")
def test_process_payment_error(mock_process: mock.Mock) -> None:
    """Test that process_payment handles errors gracefully."""
    mock_process.side_effect = Exception("Payment gateway error")

    with mock.patch.dict(os.environ, {"PAYMENTS_ENABLED": "true"}):
        result = payment_run(["JOB001", "--amount", "100.00"])

        assert result == 1


def test_generate_invoice_help() -> None:
    """Test that generate_invoice --help works without error."""
    result = invoice_run(["--help"])
    assert result == 0


def test_generate_invoice_no_args() -> None:
    """Test that generate_invoice with no args shows error."""
    result = invoice_run([])
    assert result == 1


def test_generate_invoice_dry_run() -> None:
    """Test that generate_invoice runs in DRY-RUN mode by default."""
    with mock.patch.dict(os.environ, {}, clear=True):
        result = invoice_run(["JOB001", "--customer", "Test Corp"])
        assert result == 0


@mock.patch("coterie_agents.commands.generate_invoice._generate_invoice")
def test_generate_invoice_enabled(mock_generate: mock.Mock) -> None:
    """Test that generate_invoice works when enabled."""
    mock_generate.return_value = "/path/to/invoice.pdf"

    with mock.patch.dict(os.environ, {"PAYMENTS_ENABLED": "true"}):
        result = invoice_run(["JOB001", "--customer", "John Doe", "--email", "john@example.com"])

        assert result == 0
        mock_generate.assert_called_once_with("JOB001", "John Doe", "john@example.com")


@mock.patch("coterie_agents.commands.generate_invoice._generate_invoice")
def test_generate_invoice_error(mock_generate: mock.Mock) -> None:
    """Test that generate_invoice handles errors gracefully."""
    mock_generate.side_effect = Exception("PDF generation failed")

    with mock.patch.dict(os.environ, {"PAYMENTS_ENABLED": "true"}):
        result = invoice_run(["JOB001"])

        assert result == 1
