from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Any

import requests

from ._cli import has_unknown_flags, print_help, wants_help

BOOKING_FILE = "bookings.json"

# Constants for business rules
DAILY_VEHICLE_CAP = 3
WORK_START = 8  # 8:00 AM
WORK_END = 18  # 6:00 PM

# --- constants to quiet PLR2004 (magic numbers) ---
MIN_ARGS = 6
MAX_SUGGESTIONS = 20
POP_RAIN_WARN = 50
TEMP_VERY_HOT = 95
TEMP_HOT = 85
EARLY_MORNING_END = 9
MORNING_END = 12
LUNCH_END = 14
AFTERNOON_END = 17


def load_bookings() -> list[dict[str, Any]]:
    try:
        if os.path.exists(BOOKING_FILE):
            with open(BOOKING_FILE) as f:
                return json.load(f)
    except Exception as e:
        print(f"[❌] optimize_schedule - load failed: {e}")
    return []


def fetch_weather_forecast(location: str, when: datetime) -> dict[str, Any] | None:
    """Helper function to fetch weather forecast for a specific location and datetime."""
    try:
        api_key = os.getenv("OPENWEATHER_API_KEY")
        if not api_key:
            return None

        # Geocode location
        geo_url = (
            f"http://api.openweathermap.org/geo/1.0/direct?q={location}&limit=1&appid={api_key}"
        )
        geo_resp = requests.get(geo_url, timeout=10)
        geo_data = geo_resp.json()

        if not geo_data:
            return None

        lat, lon = geo_data[0]["lat"], geo_data[0]["lon"]

        # Get forecast
        forecast_url = f"http://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&units=imperial&appid={api_key}"
        forecast_resp = requests.get(forecast_url, timeout=10)
        forecast_data = forecast_resp.json()

        # Find closest forecast time
        target_timestamp = when.timestamp()
        closest_forecast = None
        min_time_diff = float("inf")

        for forecast_item in forecast_data.get("list", []):
            forecast_timestamp = forecast_item["dt"]
            time_diff = abs(forecast_timestamp - target_timestamp)

            if time_diff < min_time_diff:
                min_time_diff = time_diff
                closest_forecast = forecast_item

        if closest_forecast:
            temp = closest_forecast["main"]["temp"]
            pop = closest_forecast.get("pop", 0) * 100
            return {"temp": temp, "pop": pop}

    except Exception as e:
        print(f"[❌] _fetch_forecast failed for {location}: {e}")

    return None


def parse_args(args: list[str]) -> tuple[int, str, str, str, datetime, int] | None:
    try:
        vehicles = int(args[0])
        tier = args[1]
        size = args[2]
        location = args[3]
        start_date = datetime.fromisoformat(args[4])
        days_ahead = int(args[5])
        return vehicles, tier, size, location, start_date, days_ahead
    except (ValueError, IndexError):
        return None


def validate_business_rules(vehicles: int, tier: str) -> bool:
    if vehicles > DAILY_VEHICLE_CAP:
        print(f"[⚠️] Requested {vehicles} vehicles exceeds daily capacity of {DAILY_VEHICLE_CAP}")
        return False
    if tier not in ["Everyday", "Payday", "Mayday", "Subscription", "Fleet"]:
        print(f"[⚠️] Unknown tier '{tier}'. Valid: Everyday, Payday, Mayday, Subscription, Fleet")
        return False
    return True


def suggest_slots() -> list[Any]:
    return []


COMMAND = "optimize_schedule"
DESCRIPTION = "Suggest optimal schedule slots for bookings."
USAGE = f"{COMMAND} <vehicles> <tier> <size> <location> <start_date> <days_ahead> [--weather] [--priority]"


def run(argv: list[str] | None = None, ctx: object | None = None) -> int:
    _ = ctx
    argv = argv or []
    rc = 0
    try:
        known = {"--help", "-h"}
        if wants_help(argv):
            print_help(COMMAND, DESCRIPTION, USAGE)
            return 0
        if has_unknown_flags(argv, known):
            print("Not found")
            print_help(COMMAND, DESCRIPTION, USAGE)
            return 0
        print_help(COMMAND, DESCRIPTION, USAGE)
    except Exception as e:
        print(f"[❌] {COMMAND} failed: {e}")
        rc = 1
    return rc
