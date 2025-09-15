"""Test updated invoice generation and payment commands."""

from unittest.mock import patch

from src.coterie_agents.commands.generate_invoice import run as generate_invoice_run
from src.coterie_agents.commands.process_payment import run as process_payment_run


class TestInvoicePaymentCommands:
    """Test updated invoice and payment commands."""

    def test_generate_invoice_help(self):
        """Test generate_invoice help display."""
        result = generate_invoice_run(["--help"])
        assert result == 0

    def test_generate_invoice_empty_args(self):
        """Test generate_invoice with empty args."""
        result = generate_invoice_run([])
        assert result == 0

    def test_generate_invoice_unknown_flags(self):
        """Test generate_invoice with unknown flags."""
        result = generate_invoice_run(["--unknown"])
        assert result == 0

    def test_generate_invoice_missing_job_id(self):
        """Test generate_invoice without job ID."""
        result = generate_invoice_run(["--customer", "Test"])
        assert result == 1

    def test_generate_invoice_invalid_amount(self):
        """Test generate_invoice with invalid amount."""
        result = generate_invoice_run(["JOB001", "--amount", "invalid"])
        assert result == 1

    def test_generate_invoice_negative_amount(self):
        """Test generate_invoice with negative amount."""
        result = generate_invoice_run(["JOB001", "--amount", "-50"])
        assert result == 1

    def test_generate_invoice_dry_run(self):
        """Test generate_invoice in dry run mode."""
        result = generate_invoice_run(
            [
                "JOB001",
                "--customer",
                "Test Customer",
                "--email",
                "test@example.com",
                "--amount",
                "150.00",
            ]
        )
        assert result == 0

    @patch.dict("os.environ", {"PAYMENTS_ENABLED": "true"})
    def test_generate_invoice_payments_enabled_success(self):
        """Test generate_invoice with payments enabled and successful result."""
        with patch("src.coterie_agents.commands.generate_invoice.payment_service") as mock_service:
            mock_service.create_invoice_with_payment.return_value = {
                "success": True,
                "invoice_id": "INV-TEST-123",
                "invoice_file": "invoices/INV-TEST-123.json",
                "payment_success": True,
                "payment_link": "https://pay.stripe.com/test",
                "payment_message": "Payment link created",
            }

            result = generate_invoice_run(
                ["JOB001", "--customer", "Test Customer", "--amount", "99.00"]
            )

            assert result == 0
            mock_service.create_invoice_with_payment.assert_called_once()

    @patch.dict("os.environ", {"PAYMENTS_ENABLED": "true"})
    def test_generate_invoice_payments_enabled_failure(self):
        """Test generate_invoice with payments enabled but failed result."""
        with patch("src.coterie_agents.commands.generate_invoice.payment_service") as mock_service:
            mock_service.create_invoice_with_payment.return_value = {
                "success": False,
                "error": "Database connection failed",
            }

            result = generate_invoice_run(["JOB001", "--amount", "100.00"])

            assert result == 1

    def test_process_payment_help(self):
        """Test process_payment help display."""
        result = process_payment_run(["--help"])
        assert result == 0

    def test_process_payment_empty_args(self):
        """Test process_payment with empty args."""
        result = process_payment_run([])
        assert result == 1

    def test_process_payment_unknown_flags(self):
        """Test process_payment with unknown flags."""
        result = process_payment_run(["--unknown"])
        assert result == 0

    def test_process_payment_invalid_amount(self):
        """Test process_payment with invalid amount."""
        result = process_payment_run(["JOB001", "--amount", "invalid"])
        assert result == 1

    def test_process_payment_negative_amount(self):
        """Test process_payment with negative amount."""
        result = process_payment_run(["JOB001", "--amount", "-100"])
        assert result == 1

    def test_process_payment_invalid_method(self):
        """Test process_payment with invalid payment method."""
        result = process_payment_run(["JOB001", "--method", "crypto"])
        assert result == 1

    def test_process_payment_dry_run_card(self):
        """Test process_payment in dry run mode with card."""
        result = process_payment_run(
            [
                "JOB001",
                "--amount",
                "250.00",
                "--method",
                "card",
                "--customer",
                "Test Customer",
            ]
        )
        assert result == 0

    def test_process_payment_dry_run_cash(self):
        """Test process_payment in dry run mode with cash."""
        result = process_payment_run(["JOB002", "--amount", "150.00", "--method", "cash"])
        assert result == 0

    @patch.dict("os.environ", {"PAYMENTS_ENABLED": "true"})
    def test_process_payment_card_success(self):
        """Test process_payment with card method and successful result."""
        with patch("src.coterie_agents.commands.process_payment.payment_service") as mock_service:
            mock_service.create_invoice_with_payment.return_value = {
                "success": True,
                "invoice_id": "INV-CARD-123",
                "payment_success": True,
                "payment_link": "https://pay.stripe.com/card_test",
                "payment_message": "Payment link created",
            }

            result = process_payment_run(
                [
                    "JOB001",
                    "--amount",
                    "200.00",
                    "--method",
                    "card",
                    "--customer",
                    "Card Customer",
                ]
            )

            assert result == 0
            mock_service.create_invoice_with_payment.assert_called_once()

    @patch.dict("os.environ", {"PAYMENTS_ENABLED": "true"})
    def test_process_payment_cash_success(self):
        """Test process_payment with cash method and successful result."""
        with patch("src.coterie_agents.commands.process_payment.payment_service") as mock_service:
            # Mock successful invoice creation and status update
            mock_service.create_invoice_with_payment.return_value = {
                "success": True,
                "invoice_id": "INV-CASH-123",
            }
            mock_service.update_invoice_status.return_value = {
                "success": True,
            }

            result = process_payment_run(["JOB002", "--amount", "175.00", "--method", "cash"])

            assert result == 0
            mock_service.create_invoice_with_payment.assert_called_once()
            mock_service.update_invoice_status.assert_called_once_with(
                invoice_id="INV-CASH-123",
                status="paid",
                notes="Payment received via cash",
            )

    @patch.dict("os.environ", {"PAYMENTS_ENABLED": "true"})
    def test_process_payment_cash_update_failure(self):
        """Test process_payment with cash method but status update failure."""
        with patch("src.coterie_agents.commands.process_payment.payment_service") as mock_service:
            mock_service.create_invoice_with_payment.return_value = {
                "success": True,
                "invoice_id": "INV-CASH-FAIL",
            }
            mock_service.update_invoice_status.return_value = {
                "success": False,
                "error": "File locked",
            }

            result = process_payment_run(["JOB003", "--method", "cash"])

            assert result == 0  # Still succeeds even if status update fails

    @patch.dict("os.environ", {"PAYMENTS_ENABLED": "true"})
    def test_process_payment_invoice_creation_failure(self):
        """Test process_payment with invoice creation failure."""
        with patch("src.coterie_agents.commands.process_payment.payment_service") as mock_service:
            mock_service.create_invoice_with_payment.return_value = {
                "success": False,
                "error": "Disk full",
            }

            result = process_payment_run(["JOB004", "--amount", "300.00", "--method", "card"])

            assert result == 1

    @patch.dict("os.environ", {"PAYMENTS_ENABLED": "true"})
    def test_process_payment_exception_handling(self):
        """Test process_payment exception handling."""
        with patch("src.coterie_agents.commands.process_payment.payment_service") as mock_service:
            mock_service.create_invoice_with_payment.side_effect = Exception("Database error")

            result = process_payment_run(["JOB005", "--amount", "100.00"])

            assert result == 1

    def test_generate_invoice_default_amount(self):
        """Test generate_invoice uses default amount when not specified."""
        result = generate_invoice_run(["JOB999"])
        assert result == 0

    def test_process_payment_default_amount(self):
        """Test process_payment uses default amount when not specified."""
        result = process_payment_run(["JOB999"])
        assert result == 0
