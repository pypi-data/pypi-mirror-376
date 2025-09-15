from ._cli import has_unknown_flags, print_help, wants_help

# agents/commands/help.py


COMMAND_HELP = {
    "assign": (
        "assign <crew> <task> [--priority high|low]\nAssign a task to one or more crew members."
    ),
    "status": ("status\nDisplays the current task status of all crew members."),
    "log": ("log <task>\nLogs a completed task and updates crew status."),
    "view": ("view\nView the current crew_status.json in terminal format."),
    "history": ("history [--limit N] [--filter <crew/task>]\nShow past command history from logs."),
    "sms": ("sms <number> <message>\nSend an SMS using your gateway setup."),
    "help": ("help [<command>]\nShow this help message or usage for a specific command."),
    "start_job": ("start_job <crew_member> <job_name>\nStart a timed job for a crew member."),
    "end_job": ("end_job <crew_member>\nEnd the current job for a crew member and log duration."),
    "board": ("board [--history N]\nDisplay crew dashboard with status and recent history."),
    "due": (
        "due <crew_member> <due_time>\n"
        "Set due time. Examples: 'in 30m', '14:30', '2025-08-03T17:00'"
    ),
    "notify": (
        "notify [--soon MINUTES] [--member NAME] [--sms NUMBER]\n"
        "Show overdue, soon-due tasks with optional SMS alert."
    ),
    "book": (
        "book [<customer> <tier> <size> <vehicles> <datetime> <location>]\n"
        "Create client booking with capacity management. Interactive mode if no args. "
        "Tiers: Everyday ($165-230), Payday ($205-320), Mayday ($205-320), Subscription"
    ),
    "list_bookings": (
        "list_bookings [--limit N] [--all]\n"
        "List upcoming client bookings (default: 10). Use --all to show past bookings too."
    ),
    "calendar_auth": ("calendar_auth\nAuthenticate with Google Calendar (one-time setup)"),
    "sync_calendar": ("sync_calendar [--clear]\nSync local bookings to Google Calendar"),
    "cluster_bookings": (
        "cluster_bookings [--threshold MILES] [--date YYYY-MM-DD] [--optimize]\n"
        "Cluster bookings by geographic proximity for route optimization. "
        "Requires Google Maps API key."
    ),
    "weather_check": (
        "weather_check [--threshold F] [--days N] [--rain]\n"
        "Check weather forecast for upcoming bookings. Warns about extreme heat and rain. "
        "Requires OpenWeatherMap API key."
    ),
    "optimize_schedule": (
        "optimize_schedule <vehicles> <tier> <size> <start_date> <days_ahead> "
        "[--weather] [--priority]\n"
        "Suggest optimal booking slots considering capacity, weather, and route clustering."
    ),
    "email_summary": (
        "email_summary <recipient> [--subject SUBJ] [--format html|text] [--days N]\n"
        "Send comprehensive email summary with crew status, bookings, and weather alerts."
    ),
    "dashboard": (
        "dashboard [--simple]\n"
        "Live terminal dashboard with crew status, bookings, and alerts. "
        "Auto-refreshes every 60 seconds."
    ),
    "whoami": ("whoami\nPrint current actor, role, and config path used."),
    "roles": ("roles\nPrint permissions table for all commands."),
    "users": ("users\nList configured users by role."),
    # Add more as needed...
}


def run(argv: list[str] | None = None, ctx: object | None = None):
    argv = argv or []
    known_flags = {"--help", "-h"}
    COMMAND = "help"
    DESCRIPTION = "Show help for available commands."
    USAGE = "help [<command>] [--help]"
    args = argv
    if wants_help(argv):
        print_help(COMMAND, DESCRIPTION, USAGE)
        return 0
    if has_unknown_flags(argv, known_flags):
        print("Not found")
        print_help(COMMAND, DESCRIPTION, USAGE)
        return 0
    if args:
        command = args[0]
        help_text = COMMAND_HELP.get(command)
        if help_text:
            print(f"\n[ℹ️] Help for '{command}':\n  {help_text}")
        else:
            print(f"[ERROR] No help entry for '{command}'")
    else:
        print("\n[🆘] Available Commands:")
        for cmd in sorted(COMMAND_HELP):
            print(f"  • {cmd}")
        print("\n[ℹ️] Type 'help <command>' for detailed usage.")
