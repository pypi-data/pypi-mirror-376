"""Payment processing service - integrates Stripe with invoice generation."""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from ..utils.logger_config import get_logger
from .stripe_service import create_payment_link, get_payment_status, store_payment_link

logger = get_logger(__name__)


class PaymentService:
    """Service for handling payment processing and invoice integration."""

    def __init__(self):
        """Initialize payment service."""
        self.invoices_dir = Path("invoices")
        self.invoices_dir.mkdir(exist_ok=True)

    def create_invoice_with_payment(
        self,
        job_id: str,
        amount: float,
        customer_name: str | None = None,
        customer_email: str | None = None,
        description: str | None = None,
    ) -> dict[str, Any]:
        """Create an invoice with payment link integration."""
        try:
            # Generate unique invoice ID
            invoice_id = f"INV-{job_id}-{datetime.now().strftime('%Y%m%d%H%M%S')}"

            # Prepare invoice description
            invoice_description = description or f"Services for job {job_id}"
            if customer_name:
                invoice_description += f" - Customer: {customer_name}"

            # Create payment link via Stripe
            payment_result = create_payment_link(
                amount=amount,
                description=invoice_description,
                invoice_id=invoice_id,
                customer_email=customer_email,
            )

            # Create invoice record
            invoice_data = {
                "invoice_id": invoice_id,
                "job_id": job_id,
                "amount": amount,
                "customer_name": customer_name,
                "customer_email": customer_email,
                "description": invoice_description,
                "created_at": datetime.now().isoformat(),
                "status": "pending",
                "payment_link": {
                    "url": (payment_result.data.get("url") if payment_result.success else None),
                    "id": (payment_result.data.get("id") if payment_result.success else None),
                    "test_mode": payment_result.data.get("test_mode", True),
                },
                "payment_result": {
                    "success": payment_result.success,
                    "message": payment_result.message,
                },
            }

            # Store invoice
            invoice_file = self.invoices_dir / f"{invoice_id}.json"
            with open(invoice_file, "w") as f:
                json.dump(invoice_data, f, indent=2)

            # Store payment link data if successful
            if payment_result.success:
                store_payment_link(invoice_id, payment_result.data)

            logger.info(f"Invoice created: {invoice_id}")
            return {
                "success": True,
                "invoice_id": invoice_id,
                "invoice_file": str(invoice_file),
                "payment_link": (
                    payment_result.data.get("url") if payment_result.success else None
                ),
                "payment_success": payment_result.success,
                "payment_message": payment_result.message,
                "data": invoice_data,
            }

        except Exception as e:
            logger.error(f"Invoice creation failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "invoice_id": None,
                "payment_link": None,
            }

    def get_invoice_status(self, invoice_id: str) -> dict[str, Any]:
        """Get invoice and payment status."""
        try:
            invoice_file = self.invoices_dir / f"{invoice_id}.json"

            if not invoice_file.exists():
                return {
                    "success": False,
                    "error": f"Invoice {invoice_id} not found",
                }

            # Load invoice data
            with open(invoice_file) as f:
                invoice_data = json.load(f)

            # Check payment status if payment link exists
            payment_status = None
            if invoice_data.get("payment_link", {}).get("id") and invoice_data.get(
                "payment_result", {}
            ).get("success"):
                payment_link_id = invoice_data["payment_link"]["id"]
                payment_result = get_payment_status(payment_link_id)
                payment_status = {
                    "success": payment_result.success,
                    "message": payment_result.message,
                    "data": payment_result.data,
                }

            return {
                "success": True,
                "invoice_data": invoice_data,
                "payment_status": payment_status,
            }

        except Exception as e:
            logger.error(f"Failed to get invoice status: {e}")
            return {
                "success": False,
                "error": str(e),
            }

    def list_invoices(self, job_id: str | None = None) -> dict[str, Any]:
        """List all invoices, optionally filtered by job_id."""
        try:
            invoices = []

            for invoice_file in self.invoices_dir.glob("INV-*.json"):
                try:
                    with open(invoice_file) as f:
                        invoice_data = json.load(f)

                    # Filter by job_id if specified
                    if job_id and invoice_data.get("job_id") != job_id:
                        continue

                    invoices.append(
                        {
                            "invoice_id": invoice_data.get("invoice_id"),
                            "job_id": invoice_data.get("job_id"),
                            "amount": invoice_data.get("amount"),
                            "customer_name": invoice_data.get("customer_name"),
                            "status": invoice_data.get("status"),
                            "created_at": invoice_data.get("created_at"),
                            "payment_link": invoice_data.get("payment_link", {}).get("url"),
                        }
                    )

                except (json.JSONDecodeError, KeyError) as e:
                    logger.warning(f"Skipping invalid invoice file {invoice_file}: {e}")
                    continue

            # Sort by creation date (newest first)
            invoices.sort(key=lambda x: x.get("created_at", ""), reverse=True)

            return {
                "success": True,
                "invoices": invoices,
                "count": len(invoices),
            }

        except Exception as e:
            logger.error(f"Failed to list invoices: {e}")
            return {
                "success": False,
                "error": str(e),
                "invoices": [],
                "count": 0,
            }

    def update_invoice_status(
        self, invoice_id: str, status: str, notes: str | None = None
    ) -> dict[str, Any]:
        """Update invoice status (paid, cancelled, etc.)."""
        try:
            invoice_file = self.invoices_dir / f"{invoice_id}.json"

            if not invoice_file.exists():
                return {
                    "success": False,
                    "error": f"Invoice {invoice_id} not found",
                }

            # Load and update invoice data
            with open(invoice_file) as f:
                invoice_data = json.load(f)

            old_status = invoice_data.get("status")
            invoice_data["status"] = status
            invoice_data["updated_at"] = datetime.now().isoformat()

            if notes:
                if "notes" not in invoice_data:
                    invoice_data["notes"] = []
                invoice_data["notes"].append(
                    {
                        "timestamp": datetime.now().isoformat(),
                        "note": notes,
                        "status_change": f"{old_status} -> {status}",
                    }
                )

            # Save updated invoice
            with open(invoice_file, "w") as f:
                json.dump(invoice_data, f, indent=2)

            logger.info(f"Invoice {invoice_id} status updated: {old_status} -> {status}")
            return {
                "success": True,
                "invoice_id": invoice_id,
                "old_status": old_status,
                "new_status": status,
                "notes": notes,
            }

        except Exception as e:
            logger.error(f"Failed to update invoice status: {e}")
            return {
                "success": False,
                "error": str(e),
            }

    def process_payment_webhook(self, webhook_data: dict[str, Any]) -> dict[str, Any]:
        """Process Stripe webhook for payment events."""
        try:
            event_type = webhook_data.get("type")

            if event_type == "payment_link.updated":
                # Handle payment link events
                payment_link = webhook_data.get("data", {}).get("object", {})
                invoice_id = payment_link.get("metadata", {}).get("invoice_id")

                if invoice_id:
                    # Update invoice status based on payment
                    notes = f"Payment link webhook: {event_type}"
                    status = "paid" if payment_link.get("after_completion") else "pending"

                    return self.update_invoice_status(invoice_id, status, notes)

            elif event_type == "invoice.payment_succeeded":
                # Handle successful payments
                invoice = webhook_data.get("data", {}).get("object", {})
                invoice_id = invoice.get("metadata", {}).get("invoice_id")

                if invoice_id:
                    notes = f"Payment succeeded: {invoice.get('amount_paid', 0) / 100:.2f}"
                    return self.update_invoice_status(invoice_id, "paid", notes)

            return {
                "success": True,
                "message": f"Webhook processed: {event_type}",
                "handled": False,
            }

        except Exception as e:
            logger.error(f"Webhook processing failed: {e}")
            return {
                "success": False,
                "error": str(e),
            }


# Global payment service instance
payment_service = PaymentService()
