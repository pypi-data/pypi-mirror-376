import json
import os
from datetime import datetime
from typing import Any

from ._cli import has_unknown_flags, print_help, wants_help

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None  # type: ignore

COMMAND = "config"
DESCRIPTION = "Enterprise configuration management and system diagnostics."
USAGE = f"{COMMAND} [subcommand] [--help]"


def run(arg: list[str] | dict[str, Any] | None = None) -> int | dict[str, Any]:
    """
    Dual API/CLI entrypoint:
    - If arg is a dict, treat as API call and route to appropriate config logic
    - If arg is a list (CLI argv), run CLI logic and return int
    """
    if isinstance(arg, dict):
        # API mode: implement API logic here as needed
        # Example: return system status as dict
        return {"status": "ok", "config": "API mode not yet implemented"}

    argv: list[str] = arg if isinstance(arg, list) else []
    known_flags = {"--help", "-h", "--apis", "--files", "--business", "--set", "--env"}
    if wants_help(argv):
        print_help(COMMAND, DESCRIPTION, USAGE)
        return 0
    if has_unknown_flags(argv, known_flags):
        print("Not found")
        print_help(COMMAND, DESCRIPTION, USAGE)
        return 0

    # Load environment variables
    if load_dotenv:
        load_dotenv()

    # Parse command arguments
    if "--apis" in argv:
        show_api_status()
        return 0
    elif "--files" in argv:
        show_file_status()
        return 0
    elif "--business" in argv:
        show_business_info()
        return 0
    elif "--set" in argv:
        handle_env_set(argv)
        return 0
    elif "--env" in argv:
        show_env_info()
        return 0
    print("[ℹ️] No subcommand provided. Showing full system status.")
    show_api_status()
    show_file_status()
    show_business_info()
    return 0


def show_api_status():
    """Display API configuration status"""
    print("\n🌐 API CONFIGURATION:")
    print("-" * 40)

    # Weather API
    openweather_key = os.getenv("OPENWEATHER_API_KEY")
    if openweather_key:
        masked_key = openweather_key[:8] + "..." + openweather_key[-4:]
        print(f"🌤️  OpenWeatherMap: ✅ Configured ({masked_key})")
    else:
        print("🌤️  OpenWeatherMap: ❌ Missing")

    # Google Maps API
    maps_key = os.getenv("GOOGLE_MAPS_API_KEY")
    if maps_key:
        masked_key = maps_key[:8] + "..." + maps_key[-4:]
        print(f"🗺️  Google Maps: ✅ Configured ({masked_key})")
    else:
        print("🗺️  Google Maps: ❌ Missing (clustering will use free OSM)")

    # SMTP Configuration
    smtp_user = os.getenv("SMTP_USERNAME") or os.getenv("SMTP_USER")
    smtp_pass = os.getenv("SMTP_PASSWORD") or os.getenv("SMTP_PASS")
    if smtp_user and smtp_pass:
        print(f"📧 SMTP Email: ✅ Configured ({smtp_user})")
    else:
        print("📧 SMTP Email: ❌ Missing")

    # Twilio SMS
    twilio_sid = os.getenv("TWILIO_ACCOUNT_SID")
    twilio_token = os.getenv("TWILIO_AUTH_TOKEN")
    if twilio_sid and twilio_token:
        masked_sid = twilio_sid[:8] + "..." + twilio_sid[-4:]
        print(f"📱 Twilio SMS: ✅ Configured ({masked_sid})")
    else:
        print("📱 Twilio SMS: ❌ Missing (using email-to-SMS)")


def show_business_info():
    """Display business configuration"""
    print("\n🏢 BUSINESS CONFIGURATION:")
    print("-" * 40)

    business_name = os.getenv("BUSINESS_NAME", "Coterie Cleaning Services")
    business_location = os.getenv("BUSINESS_LOCATION", "Gulf Coast, FL")
    business_phone = os.getenv("BUSINESS_PHONE", "(850) 555-0123")
    business_email = os.getenv("BUSINESS_EMAIL", "info@coterieclean.com")

    print(f"🏷️  Name: {business_name}")
    print(f"📍 Location: {business_location}")
    print(f"📞 Phone: {business_phone}")
    print(f"📧 Email: {business_email}")


def show_system_settings():
    """Display system configuration"""
    print("\n⚙️  SYSTEM SETTINGS:")
    print("-" * 40)

    log_level = os.getenv("COTERIE_LOG_LEVEL", "INFO")
    dev_mode = os.getenv("COTERIE_DEV_MODE", "false").lower() == "true"
    cache_enabled = os.getenv("CACHE_ENABLED", "true").lower() == "true"

    print(f"📋 Log Level: {log_level}")
    print(f"🔧 Dev Mode: {'✅ Enabled' if dev_mode else '❌ Disabled'}")
    print(f"💾 Cache: {'✅ Enabled' if cache_enabled else '❌ Disabled'}")
    import sys

    print(f"🐍 Python: {sys.version.split()[0]}")


def show_file_status():
    """Display critical file status"""
    print("\n📁 DATA FILE STATUS:")
    print("-" * 40)

    critical_files = [
        ("crew_status.json", "Crew Management"),
        ("bookings.json", "Booking System"),
        ("inventory.json", "Inventory Management"),
        ("receipts.json", "Receipt Tracking"),
        ("weather_cache.json", "Weather Cache"),
        ("geocode_cache.json", "Geocoding Cache"),
        ("coterie.log", "System Logs"),
        (".env", "Environment Config"),
    ]

    total_size = 0
    active_files = 0

    for filename, description in critical_files:
        if os.path.exists(filename):
            size = os.path.getsize(filename)
            total_size += size
            active_files += 1

            if size < 1024:
                size_str = f"{size} bytes"
            elif size < 1024 * 1024:
                size_str = f"{size / 1024:.1f} KB"
            else:
                size_str = f"{size / (1024 * 1024):.1f} MB"

            print(f"✅ {filename:<20} {size_str:<10} ({description})")
        else:
            print(f"❌ {filename:<20} {'Missing':<10} ({description})")

    print(
        f"\n📊 Summary: {active_files}/{len(critical_files)} files active, {total_size:,} bytes total"
    )


def show_cache_status():
    """Display cache performance"""
    print("\n💾 CACHE STATUS:")
    print("-" * 40)

    cache_files = [
        ("weather_cache.json", "Weather API"),
        ("geocode_cache.json", "Geocoding API"),
    ]

    for cache_file, description in cache_files:
        if os.path.exists(cache_file):
            try:
                with open(cache_file) as f:
                    cache_data = json.load(f)
                    entries = len(cache_data)
                    print(f"✅ {description}: {entries} cached entries")
            except Exception:
                print(f"⚠️  {description}: Cache file corrupted")
        else:
            print(f"❌ {description}: No cache file")


def show_system_health():
    """Display overall system health"""
    print("\n🎯 SYSTEM HEALTH SUMMARY:")
    print("-" * 40)

    # Check critical components
    weather_api = bool(os.getenv("OPENWEATHER_API_KEY"))
    crew_data = os.path.exists("crew_status.json")
    booking_data = os.path.exists("bookings.json")
    inventory_data = os.path.exists("inventory.json")

    health_score = sum([weather_api, crew_data, booking_data, inventory_data])

    if health_score == 4:
        status = "🟢 EXCELLENT"
        message = "All systems operational"
    elif health_score >= 3:
        status = "🟡 GOOD"
        message = "Minor configuration needed"
    elif health_score >= 2:
        status = "🟠 FAIR"
        message = "Some systems need attention"
    else:
        status = "🔴 NEEDS ATTENTION"
        message = "Critical systems missing"

    print(f"Overall Status: {status}")
    print(f"Health Score: {health_score}/4")
    print(f"Assessment: {message}")

    if not weather_api:
        print("⚠️  Weather API key needed for intelligent scheduling")

    print("=" * 70)


def show_env_info():
    """Show environment file information"""
    env_file = ".env"
    if os.path.exists(env_file):
        size = os.path.getsize(env_file)
        modified = datetime.fromtimestamp(os.path.getmtime(env_file))
        print("\n📄 ENVIRONMENT FILE:")
        print(f"Location: {os.path.abspath(env_file)}")
        print(f"Size: {size} bytes")
        print(f"Modified: {modified.strftime('%Y-%m-%d %H:%M:%S')}")
    else:
        print("\n❌ No .env file found")
        print(f"💡 Create {os.path.abspath('.env')} for custom configuration")


def handle_env_set(args: list[str]) -> None:
    """Handle setting environment variables"""
    try:
        set_idx = args.index("--set")
        if set_idx + 2 < len(args):
            key = args[set_idx + 1]
            value = args[set_idx + 2]

            # For demonstration - in production, this would update .env file
            print(f"[ℹ️] Would set {key}={value}")
            print("[💡] Add this to your .env file manually")
        else:
            print("[❌] Usage: config --set KEY VALUE")
    except ValueError:
        print("[❌] Invalid --set command")
