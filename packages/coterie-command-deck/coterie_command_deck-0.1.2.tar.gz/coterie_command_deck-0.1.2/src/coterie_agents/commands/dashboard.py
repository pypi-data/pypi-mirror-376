from __future__ import annotations

import contextlib
import json
import os
import select
import subprocess
import sys
import termios
import time
import tty
from collections.abc import Callable
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from coterie_agents.utils import helper_funcs as _log

from ._cli import has_unknown_flags, print_help, wants_help


# Clear screen without spawning a shell/process
def _clear_screen() -> None:
    # ANSI full reset; portable enough for our TTY usage
    print("\033c", end="")


# Allowlist of commands we explicitly permit (constant argv = S603-safe)
_SAFE_CMDS: dict[str, list[str]] = {
    # Use absolute paths when present; fall back to bare name
    "clear": [p] if (p := "/usr/bin/clear") and Path(p).exists() else ["clear"],
    "date": [p] if (p := "/bin/date") and Path(p).exists() else ["date"],
}


def _run_safe(name: str) -> int:
    """
    Execute an allowlisted command using a constant argv.
    Using the constant list avoids S603 (untrusted input) and S607 (partial paths).
    """
    cmd = _SAFE_CMDS.get(name)
    if not cmd:
        print(f"[warn] command not allowed: {name!r}")
        return 0
    # Constant argv list ⇒ no shell, no user injection surface
    return subprocess.run(cmd, check=False).returncode  # noqa: S603


def _noop_debug_log(*args: Any, **kwargs: Any) -> None:
    return None


debug_log: Callable[..., None] = getattr(_log, "debug_log", _noop_debug_log)

try:
    from rich import box
    from rich.console import Console
    from rich.layout import Layout
    from rich.live import Live
    from rich.panel import Panel
    from rich.table import Table

    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

CREW_FILE = "crew_status.json"
BOOKING_FILE = "bookings.json"


def get_key_simple():
    """Simplified key capture that's more reliable"""
    try:
        # Set terminal to raw mode
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        tty.setraw(fd)

        # Check if input is available (non-blocking)
        if select.select([sys.stdin], [], [], 0.1)[0]:
            key = sys.stdin.read(1)
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
            return key

        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return None
    except Exception:
        return None


def load_crew() -> dict[str, dict]:
    """Load crew status with error handling"""
    try:
        if os.path.exists(CREW_FILE):
            with open(CREW_FILE) as f:
                return json.load(f)
    except Exception as e:
        debug_log(f"[❌] dashboard - load crew failed: {e}")
        # S110: suppress block, log and continue
    return {}


def load_bookings(limit: int | None = None) -> list[dict]:
    """Load upcoming bookings sorted by datetime"""
    try:
        if os.path.exists(BOOKING_FILE):
            with open(BOOKING_FILE) as f:
                bs = json.load(f)
        else:
            return []
    except Exception as e:
        debug_log(f"[❌] dashboard - load bookings failed: {e}")
        # S110: suppress block, log and continue
        return []

    # Parse and filter for upcoming bookings only
    now = datetime.now()
    valid = []

    for b in bs:
        try:
            dt = datetime.fromisoformat(b["datetime"])
            if dt >= now:  # Only upcoming bookings
                valid.append((dt, b))
        except Exception as e:
            debug_log(f"[❌] dashboard - bad booking datetime: {b.get('datetime')} error: {e}")
            # S110: suppress block, log and continue
            continue

    valid.sort(key=lambda x: x[0])
    if limit:
        valid = valid[:limit]
    return [b for _, b in valid]


def make_crew_table(crew: dict[str, dict]) -> Table:
    """Create crew status table"""
    table = Table(box=box.ROUNDED)
    table.add_column("Name", style="cyan", no_wrap=True)
    table.add_column("Task")
    table.add_column("Status")
    table.add_column("Due")

    for name, info in crew.items():
        task = info.get("task", "—")
        status = info.get("status", "—")
        due = info.get("due_time", "—")

        # Truncate long tasks
        if len(task) > 25:
            task = task[:22] + "..."

        table.add_row(name, task, status, due)

    if not crew:
        table.add_row("—", "No crew data", "—", "—")

    return table


def make_bookings_table(bookings: list[dict]) -> Table:
    """Create bookings table"""
    table = Table(box=box.ROUNDED)
    table.add_column("Date/Time", style="magenta")
    table.add_column("Customer")
    table.add_column("Location")
    table.add_column("Revenue", justify="right", style="green")

    total = 0
    for b in bookings:
        try:
            dt = datetime.fromisoformat(b["datetime"])
            dt_str = dt.strftime("%m/%d %H:%M")
            customer = b.get("customer", "Unknown")[:15]
            location = b.get("location", "—")[:20]
            price = b.get("total_price", 0)
            total += price

            table.add_row(dt_str, customer, location, f"${price:,.0f}")
        except Exception as e:
            debug_log(f"[❌] dashboard - bad booking row: {b.get('datetime')} error: {e}")
            # S110: suppress block, log and continue
            continue

    if not bookings:
        table.add_row("—", "No bookings", "—", "—")
    else:
        table.add_section()
        table.add_row("TOTAL", "", "", f"${total:,.0f}")

    return table


def make_simple_sparkline(bookings):
    """Simple text-based capacity display"""
    now = datetime.now().date()
    lines = []

    for offset in range(7):
        date = now + timedelta(days=offset)
        count = 0

        for b in bookings:
            try:
                dt = datetime.fromisoformat(b["datetime"])
                if dt.date() == date:
                    count += b.get("vehicles", 1)
            except Exception as e:
                debug_log(f"[❌] dashboard - bad sparkline booking: {b.get('datetime')} error: {e}")
                continue

        day = date.strftime("%a")
        bar = "█" * min(count, 10) + "░" * (10 - min(count, 10))
        lines.append(f"{day}: {bar} ({count})")

    return "\n".join(lines)


def get_schedule_summary(bookings):
    """Get quick schedule summary"""
    try:
        if not bookings:
            return "No upcoming bookings"

        next_booking = bookings[0]
        dt = datetime.fromisoformat(next_booking["datetime"])
        days_out = (dt.date() - datetime.now().date()).days

        summary = f"Next: {dt.strftime('%m/%d %H:%M')}\n"
        summary += f"Customer: {next_booking.get('customer', 'Unknown')}\n"
        summary += f"Days out: {days_out}\n"
        summary += f"Total bookings: {len(bookings)}"

        return summary
    except Exception as e:
        debug_log(f"[❌] dashboard - schedule summary error: {e}")
        # S110: suppress block, log and continue
        return "Schedule data unavailable"


def get_weather_summary():
    """Get basic weather info"""
    return "Weather check available\nUse 'weather_check' for details"


def run_simple_live_dashboard(interval, context):
    """Simple dashboard with basic keybindings"""
    console = Console()
    last_key = ""

    layout = Layout()
    layout.split_column(
        Layout(name="header", size=3),
        Layout(name="main", ratio=1),
        Layout(name="footer", size=3),
    )

    layout["main"].split_row(Layout(name="left"), Layout(name="right"))

    layout["left"].split_column(Layout(name="crew", ratio=1), Layout(name="bookings", ratio=1))

    layout["right"].split_column(
        Layout(name="capacity", size=10),
        Layout(name="schedule", ratio=1),
        Layout(name="weather", ratio=1),
    )

    try:
        # Slower refresh rate for smoother appearance
        with Live(layout, refresh_per_second=0.5, screen=True):
            while True:
                # Simple key check
                key = get_key_simple()
                if key:
                    last_key = key
                    if key.lower() == "q":
                        break
                    elif key.lower() == "r":
                        pass
                    elif key.lower() == "h":
                        # Brief help message without disrupting layout
                        last_key = "h (help shown)"

                # Load data (cache unchanged data to reduce flicker)
                crew = load_crew()
                bookings = load_bookings(10)

                # Update header (only timestamp changes)
                timestamp = datetime.now().strftime("%H:%M:%S")  # Just time, not full date
                header_text = f"🏢 COTERIE COMMAND DECK - {timestamp}"
                if last_key:
                    header_text += f" | Key: {last_key}"

                layout["header"].update(Panel(header_text, style="bold blue"))

                # Update panels (these only change when data changes)
                layout["crew"].update(Panel(make_crew_table(crew), title="👥 Crew Status"))

                layout["bookings"].update(Panel(make_bookings_table(bookings), title="📅 Bookings"))

                layout["capacity"].update(
                    Panel(make_simple_sparkline(bookings), title="🚐 7-Day Capacity")
                )

                layout["schedule"].update(
                    Panel(get_schedule_summary(bookings), title="📊 Schedule")
                )

                layout["weather"].update(Panel(get_weather_summary(), title="🌤️ Weather"))

                # Footer with commands (static)
                footer_text = "[q] Quit  [r] Refresh  [h] Help  |  ⏱️ Auto-refresh every 60s"
                layout["footer"].update(Panel(footer_text, style="dim"))

                time.sleep(1)  # Longer sleep between updates

    except KeyboardInterrupt:
        pass
    except Exception as e:
        console.print(f"\n[❌] Dashboard error: {e}", style="red")
        # S110: suppress block, log and continue

    console.print("\n[ℹ️] Dashboard closed", style="cyan")


def run(argv: list[str] | None = None, ctx: object | None = None):
    argv = argv or []

    # Local definitions for SonarLint/type compliance
    COMMAND = "dashboard"
    DESCRIPTION = "Live dashboard with crew, bookings, and schedule overview."
    USAGE = "dashboard [--simple] [--interval N]"

    known_flags = {"--help", "-h"}

    def handle_cli_flags(argv: list[str], known_flags: set[str]) -> bool:
        """Handle help and unknown flags, return True if handled"""
        if wants_help(argv):
            print_help(COMMAND, DESCRIPTION, USAGE)
            return True
        if has_unknown_flags(argv, known_flags):
            print("Not found")
            print_help(COMMAND, DESCRIPTION, USAGE)
            return True
        return False

    if handle_cli_flags(argv, known_flags):
        return 0

    """
    Live dashboard with simplified keybindings.
    Usage: dashboard [--simple] [--interval N]

    Commands:
      q - Quit dashboard
      r - Force refresh
      h - Show help
    """
    interval = 60
    simple_mode = False

    def parse_args(args: list[str]) -> tuple[int, bool]:
        """Parse CLI args for interval and simple mode"""
        interval = 60
        simple_mode = False
        i = 0
        while i < len(args):
            if args[i] == "--interval" and i + 1 < len(args):
                with contextlib.suppress(Exception):
                    interval = int(args[i + 1])
                i += 2
            elif args[i] == "--simple":
                simple_mode = True
                i += 1
            else:
                i += 1
        return interval, simple_mode

    def render_simple_dashboard():
        print("[ℹ️] Using simple dashboard mode")
        try:
            while True:
                _clear_screen()
                _run_safe("date")
                print("🏢 COTERIE COMMAND DECK")
                print("=" * 50)
                print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                print()

                crew = load_crew()
                bookings = load_bookings(5)

                print("👥 CREW:")
                for name, info in crew.items():
                    status = info.get("status", "—") if isinstance(info, dict) else "—"
                    print(f"  {name}: {status}")

                print(f"\n📅 BOOKINGS ({len(bookings)}):")
                for b in bookings[:3]:
                    try:
                        dt_val = b["datetime"] if isinstance(b, dict) and "datetime" in b else None
                        dt = datetime.fromisoformat(dt_val) if dt_val else None
                        customer = (
                            b.get("customer", "Unknown") if isinstance(b, dict) else "Unknown"
                        )
                        if dt:
                            print(f"  {dt.strftime('%m/%d %H:%M')}: {customer}")
                        else:
                            print(f"  [Invalid datetime]: {customer}")
                    except Exception as e:
                        debug_log(
                            f"[❌] dashboard - bad simple booking: {b.get('datetime', None) if isinstance(b, dict) else None} error: {e}"
                        )
                        continue

                print("\n[Ctrl+C to exit]")
                time.sleep(10)

        except KeyboardInterrupt:
            print("\n[ℹ️] Dashboard closed")

    # Removed redundant return

    # Ensure context is defined
    context = ctx if ctx is not None else None

    # Parse CLI args
    interval, simple_mode = parse_args(argv)

    if not RICH_AVAILABLE or simple_mode:
        render_simple_dashboard()
        # Removed redundant return
    else:
        # Rich live dashboard
        run_simple_live_dashboard(interval, context)
