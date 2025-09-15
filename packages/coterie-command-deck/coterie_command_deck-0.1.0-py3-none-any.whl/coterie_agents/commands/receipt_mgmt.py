from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Any

from coterie_agents.commands.inventory import load_inventory, save_inventory

from ._cli import has_unknown_flags, print_help, wants_help

__all__ = ["run"]

COMMAND = "receipt_mgmt"
DESCRIPTION = "Manage receipts: import/list/tag."
USAGE = "deck receipt_mgmt [list|import|tag] [options]"


def run(argv: list[str] | None = None, _ctx: dict | None = None) -> int:
    argv = argv or []
    known = {"-h", "--help", "list", "import", "tag"}
    if wants_help(argv):
        print_help(COMMAND, DESCRIPTION, USAGE)
        return 0
    if has_unknown_flags(argv, known):
        print("[ERROR] Unknown flag.")
        print_help(COMMAND, DESCRIPTION, USAGE)
        return 2
    print("[DRY-RUN] receipt_mgmt executed.")
    return 0


if __name__ == "__main__":
    import sys

    exit(run(sys.argv[1:], None))

# debug_log not used or not available in this module

# File paths
RECEIPTS_FILE = "receipts.json"
RECEIPTS_DIR = "receipts"
MSDS_DIR = "msds"


def ensure_directories():
    """Ensure receipt and MSDS directories exist"""
    for directory in [RECEIPTS_DIR, MSDS_DIR]:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"[✅] Created directory: {directory}")


def load_receipts() -> dict[str, Any]:
    """Load receipts database"""
    if os.path.exists(RECEIPTS_FILE):
        try:
            with open(RECEIPTS_FILE) as f:
                return json.load(f)
        except Exception as e:
            print(f"[❌] load_receipts: {e}")
    return {}


def save_receipts(receipts: dict[str, Any]) -> None:
    """Save receipts database atomically"""
    try:
        temp_file = f"{RECEIPTS_FILE}.tmp"
        with open(temp_file, "w") as f:
            json.dump(receipts, f, indent=2)
        os.rename(temp_file, RECEIPTS_FILE)
        print(f"[✅] receipts - saved {len(receipts)} receipts")
    except Exception as e:
        print(f"[❌] save_receipts: {e}")


def integrate_receipt(receipt_id: str) -> None:
    # Integrate receipt with inventory system.
    receipts = load_receipts()

    if receipt_id not in receipts:
        print(f"[❌] Receipt {receipt_id} not found")
        return

    receipt_data = receipts[receipt_id]

    if receipt_data.get("integrated"):
        print(f"[⚠️] Receipt {receipt_id} already integrated")
        return

    if not receipt_data["items"]:
        print("[❌] Cannot integrate - no items in receipt")
        return

    print(f"\n🔄 INTEGRATING RECEIPT {receipt_id} WITH INVENTORY")
    print("=" * 50)

    try:
        inv = load_inventory()
        items_added = 0
        items_updated = 0

        for item in receipt_data["items"]:
            product_id = item["product_id"]

            if product_id in inv:
                # Update existing product with weighted average cost
                old_qty = inv[product_id]["quantity"]
                old_cost = inv[product_id]["unit_cost"]
                new_qty = item["quantity"]
                new_cost = item["unit_price"]

                total_qty = old_qty + new_qty
                weighted_cost = ((old_qty * old_cost) + (new_qty * new_cost)) / total_qty

                inv[product_id]["quantity"] = total_qty
                inv[product_id]["unit_cost"] = weighted_cost
                inv[product_id]["last_updated"] = datetime.now().isoformat()

                items_updated += 1
                print(
                    f"✅ Updated {product_id}: {old_qty} → {total_qty} {inv[product_id].get('unit', '')}"
                )

            else:
                # Add new product
                inv[product_id] = {
                    "name": item["product_name"],
                    "quantity": item["quantity"],
                    "unit": item.get("unit", ""),
                    "unit_cost": item["unit_price"],
                    "reorder_level": 0.0,  # Set manually later
                    "created": datetime.now().isoformat(),
                    "last_updated": datetime.now().isoformat(),
                }

                items_added += 1
                print(f"✅ Added {product_id}: {item['quantity']} {item.get('unit', '')}")

        # Save updated inventory
        save_inventory(inv)

        # Mark receipt as integrated
        receipts[receipt_id]["integrated"] = True
        receipts[receipt_id]["integrated_date"] = datetime.now().isoformat()
        save_receipts(receipts)

        print("\n📊 INTEGRATION COMPLETE:")
        print(f"  • {items_added} new products added")
        print(f"  • {items_updated} existing products updated")
        print(f"  • Total value: ${receipt_data['total_amount']:.2f}")

        if items_added > 0:
            print("\n💡 Tip: Set reorder levels for new products with 'inv_update'")

    except ImportError:
        print("[❌] Could not import inventory system")
    except Exception as e:
        print(f"[❌] Integration failed: {e}")
        print(f"[❌] integrate_receipt: {e}")


def handle_msds_commands(context: object | None = None) -> None:
    """Minimal MSDS command handler (stub for lint/type compliance)."""
    print("MSDS MANAGEMENT SYSTEM\nUse: msds add|list|check ...")
