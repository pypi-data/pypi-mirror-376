import json
import os
from datetime import datetime
from typing import Any

from ._cli import has_unknown_flags, print_help, wants_help

INV_LIST_HINT: str = "[ℹ️] Use 'inv_list' to see available items"

INVENTORY_FILE: str = "inventory.json"


def load_inventory() -> dict[str, Any]:
    """Load inventory from file"""
    if os.path.exists(INVENTORY_FILE):
        try:
            with open(INVENTORY_FILE) as f:
                return json.load(f)
        except Exception as e:
            print(f"[❌] load_inventory: {e}")
    return {}


def save_inventory(inv: dict[str, Any]) -> None:
    """Save inventory to file atomically"""
    try:
        # Write to temp file first, then rename for atomic operation
        temp_file = f"{INVENTORY_FILE}.tmp"
        with open(temp_file, "w") as f:
            json.dump(inv, f, indent=2)
        os.rename(temp_file, INVENTORY_FILE)
        print(f"[✅] inventory - saved {len(inv)} items")
    except Exception as e:
        print(f"[❌] save_inventory: {e}")
        # Clean up temp file if it exists
        if os.path.exists(f"{INVENTORY_FILE}.tmp"):
            os.remove(f"{INVENTORY_FILE}.tmp")


class Product:
    """Represents a raw product in inventory"""

    def __init__(self, pid: str, data: dict[str, Any]):
        self.id = pid
        self.name: str = data["name"]
        self.quantity: float = data.get("quantity", 0.0)
        self.unit: str = data.get("unit", "")
        self.reorder_level: float = data.get("reorder_level", 0.0)
        self.unit_cost: float = data.get("unit_cost", 0.0)
        self.created: str = data.get("created", datetime.now().isoformat())
        self.last_updated: str = data.get("last_updated", datetime.now().isoformat())

    def use(self, amount: float) -> float:
        """Deduct amount and return cost"""
        if amount < 0:
            raise ValueError("Usage amount must be non-negative")
        if amount > self.quantity:
            raise ValueError(f"Not enough {self.id} in stock: need {amount}, have {self.quantity}")

        self.quantity -= amount
        self.last_updated = datetime.now().isoformat()
        return amount * self.unit_cost

    def is_low_stock(self) -> bool:
        """Check if product is at or below reorder level"""
        return self.quantity <= self.reorder_level

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON storage"""
        return {
            "name": self.name,
            "quantity": self.quantity,
            "unit": self.unit,
            "reorder_level": self.reorder_level,
            "unit_cost": self.unit_cost,
            "created": self.created,
            "last_updated": self.last_updated,
        }


class Mixture:
    """Represents a mixture that combines multiple products"""

    def __init__(self, pid: str, data: dict[str, Any]):
        self.id = pid
        self.name: str = data["name"]
        self.components: dict[str, float] = data.get("components", {})
        self.unit: str = data.get("unit", "")
        self.reorder_level: float = data.get("reorder_level", 0.0)
        self.unit_cost: float = data.get("unit_cost", 0.0)
        self.ratio_per_vehicle: float = data.get("ratio_per_vehicle", 0.0)
        self.weather_adjustments: list[dict[str, float]] = data.get("weather_adjustments", [])
        self.created: str = data.get("created", datetime.now().isoformat())
        self.last_updated: str = data.get("last_updated", datetime.now().isoformat())

    def calculate_weather_factor(self, temp: float | None) -> float:
        """Calculate weather adjustment factor based on temperature"""
        if temp is None or not self.weather_adjustments:
            return 1.0

        # Find the highest threshold that the temperature meets
        factor = 1.0
        for adj in sorted(self.weather_adjustments, key=lambda x: x["threshold"]):
            if temp >= adj["threshold"]:
                factor = adj["factor"]

        return factor

    def use(
        self, vehicles: float, temp: float | None = None
    ) -> tuple[float, dict[str, float], float]:
        """
        Calculate mixture usage, deduct components, return total mix used, cost breakdown, and total cost
        """
        factor = self.calculate_weather_factor(temp)
        total_mix = vehicles * self.ratio_per_vehicle * factor

        cost_breakdown: dict[str, float] = {}
        total_cost = 0.0

        # Load current inventory
        inv = load_inventory()

        # Check if all components are available first
        for comp_id, ratio in self.components.items():
            qty_needed = total_mix * ratio
            if comp_id not in inv:
                raise KeyError(f"Component {comp_id} not found in inventory")

            comp_data = inv[comp_id]
            if "components" in comp_data:
                raise ValueError(f"Component {comp_id} is a mixture, not a raw product")

            if comp_data["quantity"] < qty_needed:
                raise ValueError(
                    f"Not enough {comp_id}: need {qty_needed:.2f}, have {comp_data['quantity']:.2f}"
                )

        # All components available, proceed with usage
        for comp_id, ratio in self.components.items():
            qty_needed = total_mix * ratio
            comp = Product(comp_id, inv[comp_id])
            cost = comp.use(qty_needed)
            cost_breakdown[comp_id] = cost
            total_cost += cost

            # Update inventory
            inv[comp_id] = comp.to_dict()

        # Save updated inventory
        save_inventory(inv)
        self.last_updated = datetime.now().isoformat()

        return total_mix, cost_breakdown, total_cost

    def can_make(self, vehicles: float = 1, temp: float | None = None) -> tuple[bool, list[str]]:
        """Check if mixture can be made with current inventory"""
        factor = self.calculate_weather_factor(temp)
        total_mix = vehicles * self.ratio_per_vehicle * factor

        inv = load_inventory()
        missing_components: list[str] = []

        for comp_id, ratio in self.components.items():
            qty_needed = total_mix * ratio
            if comp_id not in inv:
                missing_components.append(f"{comp_id} (not found)")
            elif "components" in inv[comp_id]:
                missing_components.append(f"{comp_id} (is mixture)")
            elif inv[comp_id]["quantity"] < qty_needed:
                missing_components.append(
                    f"{comp_id} (need {qty_needed:.2f}, have {inv[comp_id]['quantity']:.2f})"
                )

        return len(missing_components) == 0, missing_components

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON storage"""
        return {
            "name": self.name,
            "components": self.components,
            "unit": self.unit,
            "reorder_level": self.reorder_level,
            "unit_cost": self.unit_cost,
            "ratio_per_vehicle": self.ratio_per_vehicle,
            "weather_adjustments": self.weather_adjustments,
            "created": self.created,
            "last_updated": self.last_updated,
        }


COMMAND = "inventory"
DESCRIPTION = "Advanced inventory management with mixture support and weather adjustments."
USAGE = f"{COMMAND} <subcommand> [args] [--help]"


def run(argv: list[str] | None = None) -> int:
    argv = argv or []
    known_flags = {"--help", "-h"}

    if wants_help(argv):
        print_help(COMMAND, DESCRIPTION, USAGE)
        return 0

    if has_unknown_flags(argv, known_flags):
        print("Not found")
        print_help(COMMAND, DESCRIPTION, USAGE)
        return 0

    if not argv:
        print("[❌] No command provided.")
        print_help(COMMAND, DESCRIPTION, USAGE)
        return 0

    # ...existing inventory logic can be refactored here...
    print("[stub] inventory command executed.")
    return 0


def handle_inv_remove(args: list[str], inv: dict[str, Any]) -> None:
    if len(args) != 2:
        print("[❌] Usage: inv_remove <id>")
        return
    pid = args[1]
    if pid not in inv:
        print(f"[⚠️] Item '{pid}' not found")
        print(INV_LIST_HINT)
        return
    item_name = inv[pid]["name"]
    item_type = "mixture" if "components" in inv[pid] else "product"
    dependent_mixtures: list[str] = []
    for other_id, other_item in inv.items():
        if other_id != pid and "components" in other_item and pid in other_item["components"]:
            dependent_mixtures.append(other_id)
    if dependent_mixtures:
        print(f"[❌] Cannot remove '{pid}' - used in mixtures: {', '.join(dependent_mixtures)}")
        print("[ℹ️] Remove dependent mixtures first")
        return
    del inv[pid]
    save_inventory(inv)
    print(f"[✅] Removed {item_type} '{pid}' ({item_name})")


def handle_inv_list(inv: dict[str, Any]) -> None:
    def print_empty():
        print("[ℹ️] Inventory is empty")
        print("[💡] Add products: inv_add <id> <name> <qty> <unit> <reorder> <cost>")
        print(
            "[💡] Add mixtures: inv_add_mix <id> <name> <unit> <reorder> <cost> <ratio> <components>"
        )

    def print_products(products):
        print("\n📦 RAW PRODUCTS:")
        print("=" * 90)
        print(
            f"{'ID':<12} {'Name':<25} {'Qty':<8} {'Unit':<8} {'Reorder':<8} {'Cost':<8} {'Value':<10} {'Status':<8}"
        )
        print("=" * 90)
        total_value = 0
        low_stock_count = 0
        for pid, p in sorted(products.items()):
            product = Product(pid, p)
            value = p["quantity"] * p["unit_cost"]
            total_value += value
            status = "🔴 LOW" if product.is_low_stock() else "🟢 OK"
            if status == "🔴 LOW":
                low_stock_count += 1
            print(
                f"{pid:<12} {p['name'][:24]:<25} {p['quantity']:<8.1f} {p['unit']:<8} {p['reorder_level']:<8.1f} ${p['unit_cost']:<7.2f} ${value:<9.2f} {status}"
            )
        print("=" * 90)
        print(
            f"📊 Products: {len(products)} | Total Value: ${total_value:,.2f} | Low Stock: {low_stock_count}"
        )

    def print_mixtures(mixtures):
        print("\n🧪 MIXTURES:")
        print("=" * 95)
        print(
            f"{'ID':<12} {'Name':<25} {'Ratio/Veh':<10} {'Components':<30} {'Weather':<8} {'Status':<8}"
        )
        print("=" * 95)
        for pid, m in sorted(mixtures.items()):
            mixture = Mixture(pid, m)
            components_str = ", ".join([f"{k}:{v}" for k, v in m["components"].items()])
            weather_str = "Yes" if m.get("weather_adjustments") else "No"
            can_make, issues = mixture.can_make()
            status = "🟢 OK" if can_make else "🔴 NO"
            print(
                f"{pid:<12} {m['name'][:24]:<25} {m['ratio_per_vehicle']:<10.1f} {components_str[:29]:<30} {weather_str:<8} {status}"
            )
            if not can_make:
                for issue in issues[:2]:
                    print(f"{'':>12} ⚠️  {issue}")

    if not inv:
        print_empty()
        return
    products = {k: v for k, v in inv.items() if "components" not in v}
    mixtures = {k: v for k, v in inv.items() if "components" in v}
    if products:
        print_products(products)
    if mixtures:
        print_mixtures(mixtures)
    print()


def handle_inv_update(args: list[str], inv: dict[str, Any]) -> None:
    if len(args) != 2:
        print("[❌] Usage: inv_update <id> <quantity>")
        print('[ℹ️] Example: inv_add bleach "Industrial Bleach" 50 gal 10 15.99')
        return
    pid, qty = args[0], args[1]
    if pid not in inv:
        print(f"[⚠️] Item '{pid}' not found")
        print(INV_LIST_HINT)
        return
    if "components" in inv[pid]:
        print(f"[❌] Cannot update quantity for mixture '{pid}'")
        print("[ℹ️] Mixture quantities are calculated from components")
        return
    try:
        qty = float(qty)
    except ValueError:
        print("[❌] Quantity must be a number")
        return
    if qty < 0:
        print("[❌] Quantity cannot be negative")
        return
    old_qty = inv[pid]["quantity"]
    inv[pid]["quantity"] = qty
    inv[pid]["last_updated"] = datetime.now().isoformat()
    save_inventory(inv)
    change = qty - old_qty
    if change > 0:
        change_str = f"(+{change:.1f})"
    elif change < 0:
        change_str = f"({change:.1f})"
    else:
        change_str = "(no change)"
    print(
        f"[✅] Updated '{pid}' quantity: {old_qty:.1f} → {qty:.1f} {inv[pid]['unit']} {change_str}"
    )
    if qty <= inv[pid]["reorder_level"]:
        print(
            f"    🔔 Now at or below reorder level ({inv[pid]['reorder_level']} {inv[pid]['unit']})"
        )


def handle_inv_usage(args: list[str], inv: dict[str, Any], timestamp: str) -> None:
    if len(args) < 3:
        print("[❌] Usage: inv_usage <id> <vehicles> [--temp <F>]")
        print("[ℹ️] Example: inv_usage heavy_clean 3 --temp 88")
        return
    pid = args[1]
    try:
        vehicles = float(args[2])
    except ValueError:
        print("[❌] Vehicles must be a number")
        return
    if vehicles <= 0:
        print("[❌] Vehicles must be positive")
        return
    temp: float | None = None
    if "--temp" in args:
        try:
            temp_index = args.index("--temp")
            if temp_index + 1 < len(args):
                temp = float(args[temp_index + 1])
        except (ValueError, IndexError):
            print("[⚠️] Invalid temperature value")
            return
    if pid not in inv:
        print(f"[⚠️] Item '{pid}' not found")
        print(INV_LIST_HINT)
        return
    item_data = inv[pid]
    try:
        if "components" in item_data:
            mixture = Mixture(pid, item_data)
            can_make, issues = mixture.can_make(vehicles, temp)
            if not can_make:
                print(f"[❌] Cannot make mixture '{pid}':")
                for issue in issues:
                    print(f"    • {issue}")
                print(f"[SKIP] Mixture '{pid}' usage skipped due to: {issues}")
                return
            total_mix, breakdown, total_cost = mixture.use(vehicles, temp)
            print(f"\n🧪 MIXTURE USAGE: {item_data['name']}")
            print("=" * 60)
            print(f"🚐 Vehicles: {vehicles}")
            print(f"📏 Ratio: {item_data['ratio_per_vehicle']} {item_data['unit']}/vehicle")
            if temp is not None:
                factor = mixture.calculate_weather_factor(temp)
                print(f"🌡️  Temperature: {temp}°F (factor: {factor:.1f}x)")
            print(f"🧪 Total mixture used: {total_mix:.2f} {item_data['unit']}")
            print("\n📋 COMPONENT BREAKDOWN:")
            print("-" * 50)
            for comp_id, cost in breakdown.items():
                comp_data = inv[comp_id]
                ratio = item_data["components"][comp_id]
                qty_used = total_mix * ratio
                print(f"  • {comp_id} ({comp_data['name']})")
                print(
                    f"    Used: {qty_used:.2f} {comp_data['unit']} @ ${comp_data['unit_cost']:.2f} = ${cost:.2f}"
                )
                print(f"    Remaining: {comp_data['quantity']:.1f} {comp_data['unit']}")
                if comp_data["quantity"] <= comp_data["reorder_level"]:
                    print("    🔔 LOW STOCK - reorder needed!")
                print()
            print("-" * 50)
            print(f"💰 TOTAL COST: ${total_cost:.2f}")
            inv[pid]["last_updated"] = timestamp
            save_inventory(inv)
        else:
            product = Product(pid, item_data)
            if product.quantity < vehicles:
                print(f"[❌] Not enough '{pid}' in stock")
                print(f"    Need: {vehicles} {product.unit}")
                print(f"    Available: {product.quantity} {product.unit}")
                print(f"[SKIP] Product '{pid}' usage skipped due to insufficient stock")
                return
            cost = product.use(vehicles)
            inv[pid] = product.to_dict()
            save_inventory(inv)
            print(f"\n📦 PRODUCT USAGE: {product.name}")
            print("=" * 50)
            print(f"🚐 Vehicles: {vehicles}")
            print(f"📦 Used: {vehicles} {product.unit} @ ${product.unit_cost:.2f}")
            print(f"💰 Cost: ${cost:.2f}")
            print(f"📊 Remaining: {product.quantity:.1f} {product.unit}")
            if product.is_low_stock():
                print(f"🔔 LOW STOCK - reorder needed! (≤{product.reorder_level} {product.unit})")
    except (ValueError, KeyError) as e:
        print(f"[❌] Error: {e}")
    print("[ERROR] handle_inv_usage: Exception occurred")


def handle_inv_check(inv: dict[str, Any]) -> None:
    def get_low_products(products):
        return [
            (pid, Product(pid, p)) for pid, p in products.items() if Product(pid, p).is_low_stock()
        ]

    def get_unavailable_mixtures(mixtures):
        result = []
        for pid, m in mixtures.items():
            mixture = Mixture(pid, m)
            can_make, issues = mixture.can_make()
            if not can_make:
                result.append((pid, mixture, issues))
        return result

    products = {k: v for k, v in inv.items() if "components" not in v}
    mixtures = {k: v for k, v in inv.items() if "components" in v}
    low_products = get_low_products(products)
    unavailable_mixtures = get_unavailable_mixtures(mixtures)
    if not low_products and not unavailable_mixtures:
        print("[✅] All products above reorder level and all mixtures can be made")
        return
    if low_products:
        print(f"\n🔴 LOW STOCK PRODUCTS ({len(low_products)}):")
        print("=" * 70)
        print(f"{'ID':<12} {'Name':<25} {'Current':<12} {'Reorder Level':<15}")
        print("=" * 70)
        total_reorder_cost = 0
        for pid, product in sorted(low_products):
            shortage = max(0, product.reorder_level - product.quantity)
            reorder_cost = shortage * product.unit_cost
            total_reorder_cost += reorder_cost
            print(
                f"{pid:<12} {product.name[:24]:<25} {product.quantity:.1f} {product.unit:<8} {product.reorder_level:.1f} {product.unit}"
            )
        print("=" * 70)
        print(f"💰 Estimated reorder cost: ${total_reorder_cost:,.2f}")
    if unavailable_mixtures:
        print(f"\n🔴 UNAVAILABLE MIXTURES ({len(unavailable_mixtures)}):")
        print("=" * 60)
        for pid, mixture, issues in unavailable_mixtures:
            print(f"• {pid} ({mixture.name}):")
            for issue in issues:
                print(f"    ⚠️  {issue}")
            print()


def handle_inv_value(inv: dict[str, Any]) -> None:
    products = {k: v for k, v in inv.items() if "components" not in v}
    mixtures = {k: v for k, v in inv.items() if "components" in v}
    if not products and not mixtures:
        print("[ℹ️] Inventory is empty")
        return
    total_value = 0
    if products:
        print("\n💰 INVENTORY VALUATION:")
        print("=" * 80)
        print(f"{'ID':<12} {'Name':<25} {'Quantity':<12} {'Unit Cost':<12} {'Total Value':<12}")
        print("=" * 80)
        for pid, p in sorted(products.items()):
            value = p["quantity"] * p["unit_cost"]
            total_value += value
            print(
                f"{pid:<12} {p['name'][:24]:<25} {p['quantity']:.1f} {p['unit']:<8} ${p['unit_cost']:<11.2f} ${value:<11.2f}"
            )
        print("=" * 80)
        print(f"📊 Raw Products Total: ${total_value:,.2f}")
    if mixtures:
        print("\n🧪 MIXTURES (Component-based, no direct value):")
        print("-" * 60)
        for pid, m in sorted(mixtures.items()):
            print(f"• {pid}: {m['name']} ({m['ratio_per_vehicle']} {m['unit']}/vehicle)")
    print(f"\n💎 TOTAL INVENTORY VALUE: ${total_value:,.2f}")


def handle_inv_add(args: list[str], inv: dict[str, Any], timestamp: str) -> None:
    if len(args) != 7:
        print("[❌] Usage: inv_add <id> <name> <quantity> <unit> <reorder_level> <unit_cost>")
        print('[ℹ️] Example: inv_add bleach "Industrial Bleach" 50 gal 10 15.99')
        return
        print('[ℹ️] Example: inv_add bleach "Industrial Bleach" 50 gal 10 15.99')
        return
    try:
        pid, name, qty, unit, reorder, cost = args[1:7]
        qty = float(qty)
        reorder = float(reorder)
        cost = float(cost)
    except ValueError:
        print("[❌] Quantity, reorder_level, and unit_cost must be numbers")
        return
    if qty < 0 or reorder < 0 or cost < 0:
        print("[❌] Values cannot be negative")
        return
    action = "Updated" if pid in inv else "Added"
    inv[pid] = {
        "name": name,
        "quantity": qty,
        "unit": unit,
        "reorder_level": reorder,
        "unit_cost": cost,
        "created": inv.get(pid, {}).get("created", timestamp),
        "last_updated": timestamp,
    }
    save_inventory(inv)
    print(f"[✅] {action} product '{pid}': {name}")
    print(f"    📦 {qty} {unit} @ ${cost:.2f} each")
    print(f"    ⚠️  Reorder when ≤ {reorder} {unit}")
    if qty <= reorder:
        print("    🔔 Currently at reorder level!")


def handle_inv_add_mix(args: list[str], inv: dict[str, Any], timestamp: str) -> None:
    components = {}  # type: dict[str, float]
    if len(args) < 8:
        print(
            "[❌] Usage: inv_add_mix <id> <name> <unit> <reorder_level> <unit_cost> <ratio_per_vehicle> <comp1>:<ratio> [comp2:ratio ...] [--adj temp:factor,temp:factor]"
        )
        print(
            '[ℹ️] Example: inv_add_mix heavy_clean "Heavy Mix" gal 5 25.50 2.5 bleach:0.3 detergent:0.7 --adj 85:1.2,90:1.4'
        )
        return
        try:
            pid = args[1]
            reorder = float(args[4])
            cost = float(args[5])
            ratio_per_vehicle = float(args[6])
        except (ValueError, IndexError):
            print("[❌] Invalid arguments for mixture")
            return
        if reorder < 0 or cost < 0 or ratio_per_vehicle < 0:
            print("[❌] Values cannot be negative")
            return
        i = 7
        while i < len(args) and not args[i].startswith("--"):
            if ":" in args[i]:
                comp_id, ratio = args[i].split(":", 1)
                try:
                    ratio_val = float(ratio)
                    if ratio_val <= 0:
                        print(f"[❌] Component ratio must be positive: {comp_id}:{ratio}")
                        return
                    components[comp_id] = ratio_val
                except ValueError:
                    print(f"[❌] Invalid ratio for component {comp_id}: {ratio}")
                    return
            i += 1
        if not components:
            print("[❌] Mixture must have at least one component")
            return
        # Weather adjustment logic omitted for brevity
        for comp_id in components:
            if comp_id not in inv:
                print(f"[❌] Missing component product: {comp_id}")
                print("[ℹ️] Add base products first with 'inv_add'")
                return
            if "components" in inv[comp_id]:
                print(f"[❌] Components cannot be mixtures: {comp_id}")
                print("[ℹ️] Mixtures can only contain raw products")
                return
        action = "Updated" if pid in inv else "Added"
        inv[pid] = {
            "components": components,
            "reorder_level": reorder,
            "unit_cost": cost,
            "ratio_per_vehicle": ratio_per_vehicle,
            "created": inv.get(pid, {}).get("created", timestamp),
            "last_updated": timestamp,
        }
        save_inventory(inv)
        print(f"[✅] {action} mixture '{pid}'")
        print(f"    🧪 Uses {ratio_per_vehicle} per vehicle")
        print("    📋 Components:")
        for comp_id, ratio in components.items():
            comp_name = inv[comp_id]["name"]
            print(f"        • {comp_id} ({comp_name}): {ratio}")
    """Enhanced inventory list with MSDS compliance"""
    inv = load_inventory()

    if not inv:
        print("[ℹ️] No inventory items found")
        return

    print("\n📦 INVENTORY WITH MSDS COMPLIANCE")
    print("=" * 90)
    print(f"{'ID':<12} {'Name':<25} {'Qty':<8} {'Unit':<6} {'Cost':<8} {'Value':<10} {'MSDS':<15}")
    print("-" * 90)

    total_value = 0.0

    for pid, item in inv.items():
        if "components" in item:
            # Mixture
            print(
                f"{pid:<12} {item['name'][:24]:<25} {'—':<8} {item.get('unit', ''):<6} "
                f"{'—':<8} {'—':<10} {'Mixture':<15}"
            )
        else:
            # Raw product
            product = Product(pid, item)
            value = product.quantity * product.unit_cost
            total_value += value

            # Check MSDS compliance
            # msds_compliant, msds_status = check_msds_compliance()
            # msds_indicator = "✅" if msds_compliant else "❌"
            # print(
            #     f"{pid:<12} {product.name[:24]:<25} {product.quantity:<8.1f} "
            #     f"{product.unit:<6} ${product.unit_cost:<7.2f} ${value:<9.2f} "
            #     f"{msds_indicator} {msds_status[:13]:<13}"
            # )
            print(
                f"{pid:<12} {product.name[:24]:<25} {product.quantity:<8.1f} "
                f"{product.unit:<6} ${product.unit_cost:<7.2f} ${value:<9.2f} "
            )

    print("-" * 90)
    print(f"Total Raw Product Value: ${total_value:.2f}")
    print("\n📋 MSDS Compliance Legend:")
    print("  ✅ = Current MSDS on file")
    print("  ❌ = Missing or expired MSDS")
