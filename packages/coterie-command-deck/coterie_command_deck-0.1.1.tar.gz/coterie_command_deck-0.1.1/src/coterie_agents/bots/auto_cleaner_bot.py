#!/usr/bin/env python3
import json
import time
from datetime import datetime, timedelta
from pathlib import Path

# Paths & settings - Fixed to match project structure
LOG_PATH = Path(__file__).parents[2] / "command_log.jsonl"
ARCHIVE_DIR = Path(__file__).parents[2] / "log_archive"
RETENTION_DAYS = 7
POLL_INTERVAL = 24 * 3600  # seconds (once per day)


def archive_old_entries():
    """Archive old log entries and keep recent ones in the main log."""
    if not LOG_PATH.exists():
        print(f"[ℹ️] No log file found at {LOG_PATH}, skipping archive")
        return

    now = datetime.now(datetime.UTC)
    cutoff = now - timedelta(days=RETENTION_DAYS)

    # Ensure archive directory exists
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)

    retained = []
    archived = []

    # Separate old vs. recent
    try:
        with open(LOG_PATH, encoding="utf-8") as f:
            for line in f:
                try:
                    obj = json.loads(line.strip())
                    # Handle different timestamp formats
                    timestamp = obj.get("timestamp", "")
                    if timestamp.endswith("Z"):
                        timestamp = timestamp[:-1] + "+00:00"
                    ts = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))

                    if ts < cutoff:
                        archived.append(obj)
                    else:
                        retained.append(line)
                except (json.JSONDecodeError, ValueError, KeyError):
                    # Keep malformed entries in main log
                    retained.append(line)
    except Exception as e:
        print(f"[❌] Error reading log file: {e}")
        return

    # Write archive file if needed
    if archived:
        archive_file = ARCHIVE_DIR / f"command_log_{now.strftime('%Y%m%d')}.jsonl"
        try:
            with open(archive_file, "a", encoding="utf-8") as af:
                for obj in archived:
                    af.write(json.dumps(obj) + "\n")

            # Overwrite main log with recent entries
            with open(LOG_PATH, "w", encoding="utf-8") as f:
                for line in retained:
                    f.write(line)

            print(
                f"[🗄️] Archived {len(archived)} entries → {archive_file.name}, retained {len(retained)}"
            )
        except Exception as e:
            print(f"[❌] Error writing archive: {e}")
    else:
        print(f"[ℹ️] No entries older than {RETENTION_DAYS} days to archive")


def main():
    print(f"[🛁] AutoCleanerBot starting (retention: {RETENTION_DAYS} days)")
    print(f"[📍] Monitoring: {LOG_PATH}")
    print(f"[📁] Archive directory: {ARCHIVE_DIR}")
    print(f"[⏱️] Check interval: {POLL_INTERVAL // 3600}h")

    try:
        while True:
            archive_old_entries()
            print(f"[💤] Sleeping for {POLL_INTERVAL // 3600} hours...")
            time.sleep(POLL_INTERVAL)
    except KeyboardInterrupt:
        print("\n[🛁] AutoCleanerBot stopped by user.")
    except Exception as e:
        print(f"[❌] AutoCleanerBot error: {e}")


if __name__ == "__main__":
    main()
