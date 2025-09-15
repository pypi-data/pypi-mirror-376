import os
from datetime import datetime

from coterie_agents.utils.crew_store import ensure_crew, load_crew, save_crew

CREW_FILE = "crew_status.json"
LOG_FILE = "command_log.jsonl"

# Check the environment variable for autovivification
AUTOCREATE = os.getenv("CREW_AUTOCREATE", "1") == "1"


def _fmt_duration(delta):
    """Pretty print duration as a string."""
    return str(delta)


def run(args, context):
    """
    End a job for a crew member.
    Usage: end_job <crew_member>
    """
    if len(args) < 1:
        print("[!!] Usage: end_job <name>")
        return

    name = args[0]
    now_dt = datetime.now()
    now = now_dt.isoformat()

    # Load current crew status
    crew = load_crew()

    # Ensure crew member exists in the data based on AUTOCREATE setting
    if AUTOCREATE:
        crew = ensure_crew(crew, [name], autovivify=True)
    elif name not in crew:
        print(f"[!!] Unknown crew member: {name}")
        return

    from coterie_agents.utils.helper_funcs import primary_task, set_primary_task

    current_task = primary_task(crew[name])
    start_iso = crew[name].get("start_time")
    duration_str = "0:00:00"

    if start_iso:
        try:
            start_dt = datetime.fromisoformat(start_iso)
            duration_str = _fmt_duration(now_dt - start_dt)
        except Exception as e:
            print(f"[❌] end_job - failed to parse start_time: {start_iso} error: {e}")

    # Update state
    if current_task and current_task != "—":
        crew[name]["last_completed"] = current_task
        crew[name]["last_completed_time"] = now

    crew[name]["status"] = "READY"
    set_primary_task(crew[name], "—")
    crew[name].pop("start_time", None)  # Clear start time

    # Save updated crew status
    save_crew(crew)
    print(f"[✅] Job ended for {name} at {now}. Duration: {duration_str}.")

    # Log the command if a logging function is provided
    log_func = context.get("log_func")
    if callable(log_func):
        log_func(
            "end_job",
            [name],
            {"task": current_task, "duration": duration_str, "when": now},
        )
