"""Test payment service integration."""

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

from src.coterie_agents.services.payment_service import PaymentService


class TestPaymentService:
    """Test payment service functionality."""

    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.payment_service = PaymentService()
        # Override invoices directory for testing
        self.payment_service.invoices_dir = Path(self.temp_dir) / "invoices"
        self.payment_service.invoices_dir.mkdir(exist_ok=True)

    def test_create_invoice_with_payment_success(self):
        """Test successful invoice creation with payment link."""
        with patch(
            "src.coterie_agents.services.payment_service.create_payment_link"
        ) as mock_create:
            # Mock successful payment link creation
            mock_create.return_value = MagicMock(
                success=True,
                message="Payment link created",
                data={
                    "url": "https://pay.stripe.com/test_link",
                    "id": "plink_123",
                    "test_mode": True,
                },
            )

            result = self.payment_service.create_invoice_with_payment(
                job_id="TEST001",
                amount=150.00,
                customer_name="Test Customer",
                customer_email="test@example.com",
                description="Test service",
            )

            assert result["success"] is True
            assert "INV-TEST001-" in result["invoice_id"]
            assert result["payment_link"] == "https://pay.stripe.com/test_link"
            assert result["payment_success"] is True

            # Check invoice file was created
            invoice_files = list(self.payment_service.invoices_dir.glob("INV-TEST001-*.json"))
            assert len(invoice_files) == 1

    def test_create_invoice_payment_failure(self):
        """Test invoice creation when payment link fails."""
        with patch(
            "src.coterie_agents.services.payment_service.create_payment_link"
        ) as mock_create:
            # Mock payment link failure
            mock_create.return_value = MagicMock(
                success=False, message="Stripe not configured", data={}
            )

            result = self.payment_service.create_invoice_with_payment(
                job_id="TEST002",
                amount=200.00,
            )

            assert result["success"] is True  # Invoice created even if payment fails
            assert result["payment_success"] is False
            assert "Stripe not configured" in result["payment_message"]

    def test_get_invoice_status_existing(self):
        """Test getting status of existing invoice."""
        # Create test invoice
        invoice_data = {
            "invoice_id": "INV-TEST-123",
            "job_id": "TEST003",
            "amount": 100.00,
            "status": "pending",
            "created_at": "2025-01-13T12:00:00",
        }

        invoice_file = self.payment_service.invoices_dir / "INV-TEST-123.json"
        with open(invoice_file, "w") as f:
            json.dump(invoice_data, f)

        result = self.payment_service.get_invoice_status("INV-TEST-123")

        assert result["success"] is True
        assert result["invoice_data"]["job_id"] == "TEST003"
        assert result["invoice_data"]["amount"] == 100.00

    def test_get_invoice_status_missing(self):
        """Test getting status of non-existent invoice."""
        result = self.payment_service.get_invoice_status("INV-MISSING")

        assert result["success"] is False
        assert "not found" in result["error"]

    def test_list_invoices_empty(self):
        """Test listing invoices when none exist."""
        result = self.payment_service.list_invoices()

        assert result["success"] is True
        assert result["count"] == 0
        assert result["invoices"] == []

    def test_list_invoices_with_data(self):
        """Test listing invoices with existing data."""
        # Create test invoices
        invoices_data = [
            {
                "invoice_id": "INV-TEST-001",
                "job_id": "JOB001",
                "amount": 150.00,
                "customer_name": "Customer A",
                "status": "pending",
                "created_at": "2025-01-13T12:00:00",
                "payment_link": {"url": "https://pay.example.com/1"},
            },
            {
                "invoice_id": "INV-TEST-002",
                "job_id": "JOB002",
                "amount": 200.00,
                "customer_name": "Customer B",
                "status": "paid",
                "created_at": "2025-01-13T11:00:00",
                "payment_link": {"url": "https://pay.example.com/2"},
            },
        ]

        for invoice_data in invoices_data:
            invoice_file = self.payment_service.invoices_dir / f"{invoice_data['invoice_id']}.json"
            with open(invoice_file, "w") as f:
                json.dump(invoice_data, f)

        result = self.payment_service.list_invoices()

        assert result["success"] is True
        assert result["count"] == 2
        # Should be sorted by created_at (newest first)
        assert result["invoices"][0]["invoice_id"] == "INV-TEST-001"
        assert result["invoices"][1]["invoice_id"] == "INV-TEST-002"

    def test_list_invoices_filtered_by_job(self):
        """Test listing invoices filtered by job ID."""
        # Create test invoices for different jobs
        invoices_data = [
            {
                "invoice_id": "INV-TEST-001",
                "job_id": "JOB001",
                "amount": 150.00,
                "status": "pending",
                "created_at": "2025-01-13T12:00:00",
            },
            {
                "invoice_id": "INV-TEST-002",
                "job_id": "JOB002",
                "amount": 200.00,
                "status": "paid",
                "created_at": "2025-01-13T11:00:00",
            },
        ]

        for invoice_data in invoices_data:
            invoice_file = self.payment_service.invoices_dir / f"{invoice_data['invoice_id']}.json"
            with open(invoice_file, "w") as f:
                json.dump(invoice_data, f)

        result = self.payment_service.list_invoices(job_id="JOB001")

        assert result["success"] is True
        assert result["count"] == 1
        assert result["invoices"][0]["job_id"] == "JOB001"

    def test_update_invoice_status_success(self):
        """Test successful invoice status update."""
        # Create test invoice
        invoice_data = {
            "invoice_id": "INV-TEST-UPDATE",
            "job_id": "TEST004",
            "amount": 175.00,
            "status": "pending",
            "created_at": "2025-01-13T12:00:00",
        }

        invoice_file = self.payment_service.invoices_dir / "INV-TEST-UPDATE.json"
        with open(invoice_file, "w") as f:
            json.dump(invoice_data, f)

        result = self.payment_service.update_invoice_status(
            "INV-TEST-UPDATE", "paid", "Payment received via cash"
        )

        assert result["success"] is True
        assert result["old_status"] == "pending"
        assert result["new_status"] == "paid"

        # Verify file was updated
        with open(invoice_file) as f:
            updated_data = json.load(f)

        assert updated_data["status"] == "paid"
        assert "updated_at" in updated_data
        assert len(updated_data["notes"]) == 1
        assert "Payment received via cash" in updated_data["notes"][0]["note"]

    def test_update_invoice_status_missing(self):
        """Test updating status of non-existent invoice."""
        result = self.payment_service.update_invoice_status("INV-MISSING", "paid", "Test note")

        assert result["success"] is False
        assert "not found" in result["error"]

    def test_process_payment_webhook_payment_link(self):
        """Test processing payment link webhook."""
        # Create test invoice
        invoice_data = {
            "invoice_id": "INV-WEBHOOK-TEST",
            "job_id": "WEBHOOK001",
            "amount": 99.00,
            "status": "pending",
            "created_at": "2025-01-13T12:00:00",
        }

        invoice_file = self.payment_service.invoices_dir / "INV-WEBHOOK-TEST.json"
        with open(invoice_file, "w") as f:
            json.dump(invoice_data, f)

        webhook_data = {
            "type": "payment_link.updated",
            "data": {
                "object": {
                    "metadata": {"invoice_id": "INV-WEBHOOK-TEST"},
                    "after_completion": {"type": "redirect"},
                }
            },
        }

        result = self.payment_service.process_payment_webhook(webhook_data)

        assert result["success"] is True
        assert "payment_link.updated" in result["message"]

    def test_process_payment_webhook_unknown_event(self):
        """Test processing unknown webhook event."""
        webhook_data = {"type": "unknown.event", "data": {"object": {}}}

        result = self.payment_service.process_payment_webhook(webhook_data)

        assert result["success"] is True
        assert result["handled"] is False
        assert "unknown.event" in result["message"]
