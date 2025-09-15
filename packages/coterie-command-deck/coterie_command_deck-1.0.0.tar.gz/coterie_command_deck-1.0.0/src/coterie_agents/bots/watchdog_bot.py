# agents/bots/watchdog_bot.py

import json
import time
from pathlib import Path

# Path to the crew status JSON file
CREW_STATUS_PATH = Path(__file__).parents[2] / "state" / "crew_status.json"

# Interval in seconds between checks
POLL_INTERVAL = 1.0


def load_status():
    """
    Load and return the parsed JSON status, or None if loading fails.
    """
    try:
        return json.loads(CREW_STATUS_PATH.read_text(encoding="utf-8"))
    except Exception:
        return None


def format_status_change(status):
    """
    Format the status data in a more readable way for notifications.
    """
    if not status:
        return "Status file is empty or invalid"

    lines = []
    from coterie_agents.utils.helper_funcs import primary_task

    for crew_name, data in status.items():
        status_text = data.get("status", "UNKNOWN")
        task = primary_task(data)
        role = data.get("role", "")

        line = f"  2 {crew_name}: {status_text}"
        if role:
            line += f" ({role})"
        if task:
            line += f' - "{task}"'
        lines.append(line)

    return "\n".join(lines)


def run(poll_interval=POLL_INTERVAL):
    """
    WatchdogBot: Monitors crew_status.json for modifications and prints updates when it changes.
    """
    print(f"[🤖] WatchdogBot starting, monitoring {CREW_STATUS_PATH.name}...")
    print(f"[📍] Watching: {CREW_STATUS_PATH}")

    last_mtime = None
    last_status = None

    try:
        while True:
            try:
                mtime = CREW_STATUS_PATH.stat().st_mtime
            except FileNotFoundError:
                print(f"[⚠️] {CREW_STATUS_PATH.name} not found. Retrying in {poll_interval}s...")
                time.sleep(poll_interval)
                continue

            if last_mtime is None:
                # First time - just record the modification time
                last_mtime = mtime
                last_status = load_status()
                print(f"[✅] Initial crew status loaded ({len(last_status or {})} members)")
            elif mtime != last_mtime:
                # File has been modified
                last_mtime = mtime
                current_status = load_status()
                timestamp = time.strftime("%Y-%m-%d %H:%M:%S")

                print(f"\n[🚨] {timestamp} - {CREW_STATUS_PATH.name} changed!")

                if current_status:
                    # Show the changes in a readable format
                    print("[👥] Current crew status:")
                    print(format_status_change(current_status))

                    # Detect specific changes if we have previous status
                    if last_status:
                        # Check for new members
                        new_members = set(current_status.keys()) - set(last_status.keys())
                        removed_members = set(last_status.keys()) - set(current_status.keys())

                        if new_members:
                            print(f"[➕] New crew members: {', '.join(new_members)}")
                        if removed_members:
                            print(f"[➖] Removed crew members: {', '.join(removed_members)}")

                        # Check for status changes
                        for name in current_status:
                            if name in last_status:
                                old_data = last_status[name]
                                new_data = current_status[name]

                                if old_data.get("status") != new_data.get("status"):
                                    status_from = old_data.get("status", "UNKNOWN")
                                    status_to = new_data.get("status", "UNKNOWN")
                                    print(f"[🔄] {name}: {status_from} → {status_to}")

                                if old_data.get("task") != new_data.get("task"):
                                    old_task = old_data.get("task", "")
                                    new_task = new_data.get("task", "")
                                    print(f'[📋] {name} task: "{old_task}" → "{new_task}"')
                else:
                    print("[❌] Failed to load status data")

                last_status = current_status
                print()  # Add blank line for readability

            time.sleep(poll_interval)

    except KeyboardInterrupt:
        print("\n[🤖] WatchdogBot stopped by user.")
    except Exception as e:
        print(f"[❌] WatchdogBot error: {e}")


if __name__ == "__main__":
    run()
