import json
import os
from datetime import datetime
from typing import Any

import requests

from ._cli import has_unknown_flags, print_help, wants_help

try:
    from coterie_agents.utils.helper_funcs import debug_log
except ImportError:

    def debug_log(*args, **kwargs):
        # fallback no-op for debug_log
        pass


COMMAND = "weather_check"
DESCRIPTION = "Check weather and forecast for crew operations."
USAGE = f"{COMMAND} [--location LOC] [--threshold THRESH] [--rain RAIN] [--days N] [--cache-status] [--clear-cache] [--help]"


# Cache configuration
CACHE_FILE = "weather_cache.json"
CACHE_TTL = 3600  # 1 hour cache
DEFAULT_LOCATION = "Mobile, AL"  # Gulf Coast default


def _save_cache(cache: dict[str, Any]) -> None:
    """Save weather cache to disk"""
    try:
        with open(CACHE_FILE, "w") as f:
            json.dump(cache, f, indent=2)
        debug_log(f"[✅] weather_cache saved {len(cache)} entries")
    except Exception as e:
        debug_log(f"[❌] weather_cache save failed: {e}")


def _fetch_current_weather(location: str, api_key: str) -> dict[str, Any]:
    """Fetch current weather"""
    url = "http://api.openweathermap.org/data/2.5/weather"
    params = {"q": location, "appid": api_key, "units": "imperial"}
    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()
    return response.json()


def _fetch_forecast(location: str, api_key: str, days: int = 5) -> dict[str, Any]:
    """Fetch forecast data"""
    url = "http://api.openweathermap.org/data/2.5/forecast"
    params = {
        "q": location,
        "appid": api_key,
        "units": "imperial",
        "cnt": days * 8,
    }
    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()
    return response.json()


def _analyze_weather_impact(weather_data: dict[str, Any], threshold: float) -> dict[str, Any]:
    """Analyze weather impact on cleaning operations"""
    current = weather_data.get("main", {})
    weather = weather_data.get("weather", [{}])[0]
    temp = current.get("temp", 0)
    humidity = current.get("humidity", 0)
    condition = weather.get("main", "Clear")
    description = weather.get("description", "")
    impact = "LOW"
    alerts = []
    if temp > threshold:
        impact = "HIGH"
        alerts.append(f"High temperature ({temp:.1f}°F) - increased water usage expected")
    elif temp < 50:
        impact = "MEDIUM"
        alerts.append(f"Cold temperature ({temp:.1f}°F) - slower drying times")
    if condition in ["Rain", "Thunderstorm", "Drizzle"]:
        impact = "HIGH"
        alerts.append(f"Precipitation ({description}) - outdoor work may be delayed")
    elif condition in ["Clouds"]:
        impact = "MEDIUM"
        alerts.append(f"Cloudy conditions ({description}) - good for outdoor cleaning")
    elif condition == "Clear":
        alerts.append("Clear conditions - optimal for all cleaning operations")
    if humidity > 80:
        impact = "MEDIUM" if impact == "LOW" else impact
        alerts.append(f"High humidity ({humidity}%) - slower drying times")
    return {
        "impact": impact,
        "alerts": alerts,
        "temp": temp,
        "humidity": humidity,
        "condition": condition,
        "description": description,
    }


def _load_cache() -> dict[str, Any]:
    """Load weather cache from disk"""
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE) as f:
                return json.load(f)
        except Exception as e:
            debug_log(f"[❌] weather_cache load failed: {e}")
    return {}


def run(argv: list[str] | None = None, ctx: object | None = None) -> int:
    _ = ctx  # CLI parity, intentionally unused
    argv = argv or []
    rc = 0
    known_flags = {"--help", "-h"}

    if wants_help(argv):
        print_help(COMMAND, DESCRIPTION, USAGE)
        return 0

    if has_unknown_flags(argv, known_flags):
        print("Not found")
        print_help(COMMAND, DESCRIPTION, USAGE)
        return 0

    try:
        location, threshold, days = _parse_args(argv)
        api_key = os.getenv("OPENWEATHER_API_KEY")
        if not api_key:
            print("[❌] OpenWeather API key not found")
            print("[ℹ️] Set OPENWEATHER_API_KEY environment variable")
            print("[ℹ️] Get your free API key at: https://openweathermap.org/api")
            return 1

        print("\n📊 Fetching weather data...")
        current_data = _fetch_current_weather(location, api_key)
        analysis = _analyze_weather_impact(current_data, threshold)
        _print_current_conditions(analysis)
        if days > 1:
            forecast_data = _fetch_forecast(location, api_key, days)
            _print_forecast_impact(forecast_data, threshold, days)
        cache = _load_cache()
        cache_entries = len(cache)
        if cache_entries > 0:
            print(f"\n📋 Cache: {cache_entries} entries (saves API calls & costs)")
    except requests.exceptions.RequestException as e:
        print(f"[❌] Weather API error: {e}")
        print("[ℹ️] Check your internet connection and API key")
        rc = 1
    except Exception as e:
        print(f"[❌] Weather check failed: {e}")
        debug_log(f"[❌] weather_check error: {e}")
        rc = 1
    return rc


def _parse_args(argv: list[str]) -> tuple[str, float, int]:
    # TODO: parse flags for location, threshold, days, etc.
    location = DEFAULT_LOCATION
    threshold = 85.0
    days = 5
    # ...parse argv for overrides...
    return location, threshold, days


def _print_current_conditions(analysis: dict[str, Any]) -> None:
    print("\n🌡️  CURRENT CONDITIONS")
    print("-" * 30)
    print(f"Temperature: {analysis['temp']:.1f}°F")
    print(f"Humidity: {analysis['humidity']}%")
    print(f"Conditions: {analysis['condition']} - {analysis['description']}")
    print(f"Impact Level: {analysis['impact']}")
    if analysis["alerts"]:
        print("\n⚠️  OPERATIONAL ALERTS:")
        for alert in analysis["alerts"]:
            print(f"  • {alert}")


def _print_forecast_impact(forecast_data: dict[str, Any], threshold: float, days: int) -> None:
    print(f"\n🗓️ {days}-DAY FORECAST IMPACT")
    print("-" * 40)
    forecasts = forecast_data.get("list", [])
    daily_forecasts = {}
    for forecast in forecasts:
        dt = datetime.fromtimestamp(forecast["dt"])
        day_key = dt.strftime("%Y-%m-%d")
        if day_key not in daily_forecasts:
            daily_forecasts[day_key] = []
        daily_forecasts[day_key].append(forecast)
    high_impact_days = 0
    for day, day_forecasts in list(daily_forecasts.items())[:days]:
        midday_forecast: dict[str, Any] = (
            day_forecasts[len(day_forecasts) // 2]
            if day_forecasts
            else {"temperature": None, "condition": None}
        )
        day_analysis = _analyze_weather_impact(midday_forecast, threshold)
        date_obj = datetime.strptime(day, "%Y-%m-%d")
        day_name = date_obj.strftime("%A")
        impact_icon = {"LOW": "✅", "MEDIUM": "⚠️", "HIGH": "🔴"}[day_analysis["impact"]]
        print(
            f"{impact_icon} {day_name} ({day}): {day_analysis['temp']:.1f}°F, {day_analysis['condition']}"
        )
        if day_analysis["impact"] == "HIGH":
            high_impact_days += 1
            for alert in day_analysis["alerts"][:1]:
                print(f"    └─ {alert}")
    print("\n💡 BUSINESS RECOMMENDATIONS:")
    if high_impact_days == 0:
        print("  ✅ Excellent conditions for all cleaning operations")
        print("  📈 Consider booking additional outdoor jobs")
    elif high_impact_days <= 2:
        print(f"  ⚠️ {high_impact_days} day(s) with challenging conditions")
        print("  🔄 Plan indoor jobs for high-impact days")
        print("  📦 Stock extra supplies for weather-related delays")
    else:
        print(f"  🔴 {high_impact_days} day(s) with difficult conditions")
        print("  🏠 Focus on indoor cleaning operations")
        print("  📞 Proactive customer communication recommended")
        print("  💧 Increased supply usage expected")
