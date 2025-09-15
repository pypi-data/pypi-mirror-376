# agents/bots/logger_bot.py

import json
import time
from pathlib import Path

# Paths to the main command log and the filtered event log
LOG_PATH = Path(__file__).parents[2] / "command_log.jsonl"
EVENT_LOG_PATH = Path(__file__).parents[2] / "event_log.jsonl"


def tail(file):
    """
    Generator that yields new lines as they are written to the file (like `tail -f`).
    """
    file.seek(0, 2)  # Move to end of file
    while True:
        line = file.readline()
        if not line:
            time.sleep(0.5)
            continue
        yield line


def process_entry(entry):
    """
    If the command in entry is one of our key events, append to event log and notify.
    """
    key_commands = {
        "assign",
        "log",
        "status",
        "add_crew",
        "promote",
        "demote",
        "edit_task",
    }
    cmd = entry.get("command")
    if cmd in key_commands:
        with open(EVENT_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
        print(f"[📓] LoggerBot recorded '{cmd}' at {entry['timestamp']}")


def run():
    """
    Start LoggerBot: watch the main log file and filter key events.
    """
    print("[🤖] LoggerBot starting, watching command_log.jsonl...")

    # Ensure the main log file exists
    if not LOG_PATH.exists():
        print(f"[⚠️] Main log file not found: {LOG_PATH}")
        print("[ℹ️] LoggerBot will wait for the file to be created...")

        # Wait for the file to be created
        while not LOG_PATH.exists():
            time.sleep(1)
        print("[✅] Log file detected! Starting monitoring...")

    try:
        with open(LOG_PATH, encoding="utf-8") as f:
            for line in tail(f):
                try:
                    entry = json.loads(line.strip())
                    process_entry(entry)
                except json.JSONDecodeError as e:
                    print(f"[⚠️] LoggerBot: Skipped malformed JSON: {e}")
                except Exception as e:
                    print(f"[❌] LoggerBot: Error processing entry: {e}")
    except KeyboardInterrupt:
        print("\n[🤖] LoggerBot stopped by user.")
    except FileNotFoundError:
        print(f"[❌] LoggerBot: Cannot find log file: {LOG_PATH}")
    except Exception as e:
        print(f"[❌] LoggerBot: Unexpected error: {e}")


if __name__ == "__main__":
    run()
