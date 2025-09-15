from __future__ import annotations

# stdlib
import json
import os
from collections.abc import Callable
from datetime import date, datetime
from types import SimpleNamespace as Namespace
from typing import Any

# first-party
from coterie_agents.utils import helper_funcs as _log

from ._cli import has_unknown_flags, print_help, wants_help

# optional third-party (safe fallback)
try:
    import googlemaps  # type: ignore

    GOOGLEMAPS_AVAILABLE = True
except Exception:
    googlemaps = None  # type: ignore
    GOOGLEMAPS_AVAILABLE = False

API_KEY = os.environ.get("GOOGLE_MAPS_API_KEY", "")


def _noop_debug_log(*_a: Any, **_k: Any) -> None:
    return None


debug_log: Callable[..., None] = getattr(_log, "debug_log", _noop_debug_log)


def gather_interactive_input() -> tuple[str, str, str, str, str, str]:
    try:
        customer = input("Customer name: ").strip()
        while not customer:
            customer = input("Customer name required: ").strip()
        print(f"Available tiers: {', '.join(TIERS)}")
        tier = input("Tier: ").strip().title()
        while tier not in TIERS:
            tier = input(f"Invalid tier. Choose from {TIERS}: ").strip().title()
        print(f"Vehicle sizes: {', '.join(VEHICLE_SIZES[:-1])} (Fleet available in wizard)")
        size = input("Size: ").strip().title()
        while size not in VEHICLE_SIZES:
            if size.lower() == "fleet":
                size = "Fleet"
                break
            size = input(f"Invalid size. Choose from {VEHICLE_SIZES[:-1]}: ").strip().title()
        vehicles = input("Number of vehicles: ").strip()
        dt_str = input("Date/time (YYYY-MM-DDTHH:MM): ").strip()
        location = input("Location: ").strip()
        return customer, tier, size, vehicles, dt_str, location
    except (KeyboardInterrupt, Exception) as e:
        print("\n[⚠️] Booking cancelled or failed.")
        debug_log(f"[❌] book interactive - {e}")
        return "", "", "", "", "", ""


def validate_booking_fields(
    customer: str, tier: str, size: str, vehicles: str, dt_str: str, location: str
) -> bool:
    if not all([customer, tier, size, vehicles, dt_str, location]):
        print(
            "[ERROR] Usage: book <customer> <tier> <size> <vehicles> <YYYY-MM-DDTHH:MM> <location>"
        )
        return False
    return True


def parse_datetime(dt_str: str) -> datetime | None:
    try:
        return datetime.fromisoformat(dt_str)
    except Exception:
        print("[ERROR] Invalid date format. Use YYYY-MM-DDTHH:MM")
        return None


def parse_vehicles(vehicles: str) -> int | None:
    try:
        return int(vehicles)
    except Exception:
        print("[ERROR] Invalid vehicle count.")
        return None


BOOKING_FILE: str = "bookings.json"
API_KEY: str | None = os.getenv("GOOGLE_MAPS_API_KEY")
TIERS: list[str] = ["Everyday", "Payday", "Mayday", "Subscription"]
VEHICLE_SIZES: list[str] = ["Small", "Medium", "Large", "Fleet"]
DAILY_VEHICLE_CAP: int = 3  # Max non-fleet vehicles per day

# Pricing: interior + exterior per vehicle size for each tier
PRICING: dict[str, dict[str, int]] = {
    "Everyday": {"Small": (80 + 85), "Medium": (95 + 100), "Large": (110 + 120)},
    "Payday": {"Small": (110 + 95), "Medium": (140 + 120), "Large": (175 + 145)},
    "Mayday": {"Small": (110 + 95), "Medium": (140 + 120), "Large": (175 + 145)},
    # Subscription/fleet handled separately
}

LOCATION_SHORTCUTS: dict[str, str] = {
    "downtown fwb": "100 Miracle Strip Pkwy, Fort Walton Beach, FL",
    "destin commons": "4801 Commons Dr, Destin, FL",
    "boardwalk": "1540 Miracle Strip Pkwy, Fort Walton Beach, FL",
}


def load_bookings() -> list[dict[str, Any]]:
    try:
        if os.path.exists(BOOKING_FILE):
            with open(BOOKING_FILE) as f:
                return json.load(f)
    except Exception as e:
        debug_log(f"[❌] load_bookings - {e}")
    return []


def save_bookings(bookings: list[dict[str, Any]]) -> bool:
    try:
        with open(BOOKING_FILE, "w") as f:
            json.dump(bookings, f, indent=2)
        return True
    except Exception as e:
        debug_log(f"[❌] save_bookings - {e}")
        return False


def validate_address(gmaps_client: Any, address: str) -> tuple[bool, str | None]:
    try:
        result = gmaps_client.geocode(address)
        if result:
            return True, result[0]["formatted_address"]
        return False, None
    except Exception:
        return False, None


def daily_count(bookings: list[dict[str, Any]], target_date: date) -> int:
    total = 0
    for b in bookings:
        try:
            dt = datetime.fromisoformat(b["datetime"])
            if dt.date() == target_date and b.get("size") != "Fleet":
                vehicles = b.get("vehicles", 1)
                if isinstance(vehicles, int):
                    total += vehicles
        except (ValueError, KeyError) as e:
            print(f"[\u26a0\ufe0f] Skipping booking due to error: {e}")
            continue
    return total


def _parse_args(args: list[str]) -> Namespace:
    """
    Positional parsing without argparse (avoids SystemExit).
    Order: customer, tier, size, vehicles, datetime, location...
    Location may contain spaces (we join the rest).
    """
    ns = Namespace(customer=None, tier=None, size=None, vehicles=None, datetime=None, location=None)
    parts = [a for a in args if not a.startswith("-")]  # flags handled separately
    if parts:
        ns.customer = parts[0] if len(parts) >= 1 else None
        ns.tier = parts[1] if len(parts) >= 2 else None
        ns.size = parts[2] if len(parts) >= 3 else None
        ns.vehicles = parts[3] if len(parts) >= 4 else None
        ns.datetime = parts[4] if len(parts) >= 5 else None
        ns.location = " ".join(parts[5:]) if len(parts) >= 6 else None
    return ns


def _get_booking_args(args: list[str]) -> tuple[str, str, str, str, str, str]:
    ns = _parse_args(args)
    if not args:
        return gather_interactive_input()
    return (
        ns.customer or "",
        (ns.tier or "").title(),
        (ns.size or "").title(),
        ns.vehicles or "1",
        ns.datetime or "",
        ns.location or "",
    )


def _validate_and_parse(
    customer: str,
    tier: str,
    size: str,
    vehicles: str,
    dt_str: str,
    location: str,
    bookings: list[dict[str, Any]],
) -> tuple[bool, int | None, datetime | None, str]:
    if not validate_booking_fields(customer, tier, size, vehicles, dt_str, location):
        return False, None, None, location
    dt = parse_datetime(dt_str)
    if not dt:
        return False, None, None, location
    vehicles_int = parse_vehicles(vehicles)
    if vehicles_int is None:
        return False, None, None, location
    current = daily_count(bookings, dt.date())
    if size != "Fleet" and current + vehicles_int > DAILY_VEHICLE_CAP:
        print(
            f"[ERROR] Exceeds daily cap of {DAILY_VEHICLE_CAP} vehicles. "
            f"Currently booked: {current}."
        )
        return False, None, None, location
    return True, vehicles_int, dt, location


def _resolve_location(location: str) -> str:
    return LOCATION_SHORTCUTS.get(location.lower(), location)


def _validate_address_if_needed(location: str) -> str:
    if GOOGLEMAPS_AVAILABLE and API_KEY:
        # Type: ignore is used because googlemaps.Client is dynamically imported
        gmaps_client: Any = googlemaps.Client(key=API_KEY)  # type: ignore
        valid, formatted = validate_address(gmaps_client, location)
        if not valid:
            print("[ERROR] Invalid address. Please check and try again.")
            return location
        return formatted or location
    return location


def _create_booking(
    customer: str,
    tier: str,
    size: str,
    vehicles_int: int,
    dt_str: str,
    location: str,
) -> dict[str, Any]:
    return {
        "customer": customer,
        "tier": tier,
        "size": size,
        "vehicles": vehicles_int,
        "datetime": dt_str,
        "location": location,
    }


COMMAND = "book"
DESCRIPTION = "Book a job with customer, timing, and crew assignments."
USAGE = f"{COMMAND} [--help] <job_title> --at <YYYY-MM-DDTHH:MM> [--duration <minutes>] [--assignees <names>]"


def _parse_booking_args(
    args: list[str],
) -> tuple[str | None, str | None, int | None, list[str]]:
    """Parse booking arguments from command line."""
    job_title = None
    at_time = None
    duration = None
    assignees = []

    i = 0
    while i < len(args):
        arg = args[i]
        if arg.startswith("--"):
            continue  # Skip flags handled elsewhere
        elif not job_title:
            job_title = arg
        i += 1

    # Extract --at flag
    if "--at" in args:
        try:
            at_idx = args.index("--at")
            if at_idx + 1 < len(args):
                at_time = args[at_idx + 1]
        except (ValueError, IndexError):
            pass

    # Extract --duration flag
    if "--duration" in args:
        try:
            dur_idx = args.index("--duration")
            if dur_idx + 1 < len(args):
                duration = int(args[dur_idx + 1])
        except (ValueError, IndexError):
            pass

    # Extract --assignees flag
    if "--assignees" in args:
        try:
            ass_idx = args.index("--assignees")
            if ass_idx + 1 < len(args):
                assignees_str = args[ass_idx + 1]
                assignees = [name.strip() for name in assignees_str.split(",")]
        except (ValueError, IndexError):
            pass

    return job_title, at_time, duration, assignees


def run(argv: list[str] | None = None, ctx: object = None) -> int:
    argv = argv or []
    known_flags = {"--help", "-h", "--at", "--duration", "--assignees", "--retries"}

    if wants_help(argv):
        print_help(COMMAND, DESCRIPTION, USAGE)
        print("\nExamples:")
        print(f"  {COMMAND} 'Rig wash' --at 2025-09-15T08:30")
        print(f"  {COMMAND} 'Rig wash' --at 2025-09-15T08:30 --duration 90 --assignees 'Jet,Mixie'")
        print(f"  {COMMAND} 'Rig wash' --at 2025-09-15T08:30 --retries 3")
        return 0

    if has_unknown_flags(argv, known_flags):
        print("Not found")
        print_help(COMMAND, DESCRIPTION, USAGE)
        return 0

    # Parse arguments
    job_title, at_time, duration, assignees = _parse_booking_args(argv)

    if not job_title:
        print("[ERROR] Job title is required")
        print_help(COMMAND, DESCRIPTION, USAGE)
        return 1

    if not at_time:
        print("[ERROR] --at <YYYY-MM-DDTHH:MM> is required")
        print_help(COMMAND, DESCRIPTION, USAGE)
        return 1

    # Validate and parse datetime
    try:
        booking_dt = datetime.fromisoformat(at_time)
    except ValueError:
        print(f"[ERROR] Invalid datetime format: {at_time}. Use YYYY-MM-DDTHH:MM")
        return 1

    # Load existing bookings
    bookings = load_bookings()

    # Create booking entry
    booking: dict[str, Any] = {
        "id": len(bookings) + 1,
        "job_title": job_title,
        "datetime": booking_dt.isoformat(),
        "duration_minutes": duration or 60,
        "assignees": assignees,
        "created_at": datetime.now().isoformat(),
        "status": "scheduled",
    }

    bookings.append(booking)

    # Save bookings
    if save_bookings(bookings):
        print(f"✅ Booked: '{job_title}' at {booking_dt.strftime('%Y-%m-%d %H:%M')}")
        if duration:
            print(f"   Duration: {duration} minutes")
        if assignees:
            print(f"   Assignees: {', '.join(assignees)}")
        return 0
    else:
        print("[ERROR] Failed to save booking")
        return 1
