from __future__ import annotations

import shlex
import sys
from collections.abc import Callable
from typing import Any

from coterie_agents.authz import Role, has_at_least, resolve_actor, role_of
from coterie_agents.commands.assign import run as assign_run
from coterie_agents.commands.board import run as board_run
from coterie_agents.commands.book import run as book_run
from coterie_agents.commands.calendar_auth import run as calendar_auth_run
from coterie_agents.commands.cluster_bookings import run as cluster_run
from coterie_agents.commands.config import run as config_run
from coterie_agents.commands.dashboard import run as dashboard_run
from coterie_agents.commands.due import run as due_run
from coterie_agents.commands.email_summary import run as email_summary_run
from coterie_agents.commands.end_job import run as end_job_run
from coterie_agents.commands.history import run as history_run
from coterie_agents.commands.inventory import run as inventory_run
from coterie_agents.commands.list_bookings import run as list_bookings_run
from coterie_agents.commands.logger_config import run as logger_run
from coterie_agents.commands.notify import run as notify_run
from coterie_agents.commands.optimize_schedule import run as optimize_run
from coterie_agents.commands.receipt_mgmt import handle_msds_commands
from coterie_agents.commands.roles import run as roles_run
from coterie_agents.commands.sms import run as sms_run
from coterie_agents.commands.start_job import run as start_job_run
from coterie_agents.commands.status import run as status_run
from coterie_agents.commands.sync_calendar import run as sync_calendar_run
from coterie_agents.commands.user_mgmt import run as user_mgmt_run
from coterie_agents.commands.users import run as users_run
from coterie_agents.commands.view import run as view_run
from coterie_agents.commands.weather_check import run as weather_run
from coterie_agents.commands.whoami import run as whoami_run
from coterie_agents.utils import helper_funcs as _log


def _noop_debug_log(*args: Any, **kwargs: Any) -> None:
    return None


def _placeholder_receipt_run(args: list[str], ctx: Any = None) -> int:
    """Placeholder for receipt command - not implemented yet."""
    print("[ℹ️] Receipt management not implemented yet")
    return 0


debug_log: Callable[..., None] = getattr(_log, "debug_log", _noop_debug_log)

# Command role requirements - maps commands to minimum required roles
COMMAND_ROLES: dict[str, Role] = {
    # Viewer level - basic read-only access
    "status": "viewer",
    "view": "viewer",
    "board": "viewer",
    "history": "viewer",
    "list_bookings": "viewer",
    "dashboard": "viewer",
    "deck": "viewer",  # alias
    "weather": "viewer",  # alias
    "weather_check": "viewer",
    "inv_list": "viewer",
    "inv_value": "viewer",
    "help": "viewer",
    # Tech level - operational commands
    "start_job": "tech",
    "end_job": "tech",
    "due": "tech",
    "notify": "tech",
    "sms": "tech",
    "book": "tech",
    "calendar_auth": "tech",
    "sync_calendar": "tech",
    "inv_add": "tech",
    "inv_add_mix": "tech",
    "inv_remove": "tech",
    "inv_update": "tech",
    "inv_usage": "tech",
    "inv_check": "tech",
    "receipt": "tech",
    "receipts": "tech",
    "msds": "tech",
    "safety": "tech",
    # Lead level - advanced operations
    "assign": "lead",  # Leads can assign tasks to crew
    "cluster_bookings": "lead",
    "optimize_schedule": "lead",
    "optimize": "lead",  # alias
    "email_summary": "lead",
    "logger_config": "lead",
    "config": "lead",
    # Owner level - system administration
    "user_mgmt": "owner",
    "process_payment": "owner",
    "invoice": "owner",  # Invoice processing requires owner role
    "generate_invoice": "owner",  # Invoice generation requires owner role
    # Always allowed
    "exit": "viewer",
}

COMMANDS: dict[str, Callable] = {
    # Core crew management
    "assign": assign_run,
    "start_job": start_job_run,
    "end_job": end_job_run,
    "status": status_run,
    "history": history_run,
    "view": view_run,
    "board": board_run,
    "due": due_run,
    "notify": notify_run,
    "sms": sms_run,
    # Business operations
    "book": book_run,
    "list_bookings": list_bookings_run,
    "calendar_auth": calendar_auth_run,
    "sync_calendar": sync_calendar_run,
    "cluster_bookings": cluster_run,
    "weather_check": weather_run,
    "optimize_schedule": optimize_run,
    "email_summary": email_summary_run,
    "dashboard": dashboard_run,
    # Inventory management
    "inv_add": lambda args, ctx=None: inventory_run(["inv_add", *args]),
    "inv_add_mix": lambda args, ctx=None: inventory_run(["inv_add_mix", *args]),
    "inv_remove": lambda args, ctx=None: inventory_run(["inv_remove", *args]),
    "inv_list": lambda args, ctx=None: inventory_run(["inv_list", *args]),
    "inv_update": lambda args, ctx=None: inventory_run(["inv_update", *args]),
    "inv_usage": lambda args, ctx=None: inventory_run(["inv_usage", *args]),
    "inv_check": lambda args, ctx=None: inventory_run(["inv_check", *args]),
    "inv_value": lambda args, ctx=None: inventory_run(["inv_value", *args]),
    # User management
    "user_mgmt": user_mgmt_run,
    # Aliases for convenience
    "deck": dashboard_run,  # alias for dashboard
    "weather": weather_run,  # alias for weather_check
    "optimize": optimize_run,  # alias for optimize_schedule
    "receipt": _placeholder_receipt_run,
    "msds": handle_msds_commands,
    "receipts": _placeholder_receipt_run,
    "safety": handle_msds_commands,
    # System commands
    "logger_config": lambda args, ctx=None: logger_run(list(args)),
    "help": lambda args, ctx=None: print_help(),
    "config": lambda args, ctx=None: config_run(list(args)),
    "exit": lambda args, ctx=None: sys.exit(0),
    # Whoami and roles commands
    "whoami": whoami_run,
    "roles": roles_run,
    "users": users_run,
}


def _check_permission(cmd_name: str) -> bool:
    """Check if current user has permission to run the command."""
    actor = resolve_actor()
    required_role = COMMAND_ROLES.get(cmd_name, "owner")  # Default to owner if not specified

    if has_at_least(actor, required_role):
        return True

    user_role = role_of(actor)
    print(f"[🚫] Access denied. User '{actor}' (role: {user_role}) cannot run '{cmd_name}'.")
    print(f"[ℹ️] Required role: {required_role} or higher")
    return False


def _check_as_escalation(argv: list[str]) -> None:
    import getpass

    if "--as" in argv:
        idx = argv.index("--as")
        if idx + 1 < len(argv):
            requested = argv[idx + 1]
            os_user = getpass.getuser()
            if requested != os_user and "--force" not in argv:
                print(
                    f"[⚠️] Escalation: --as '{requested}' is above your OS user '{os_user}'. Use --force to proceed."
                )


def print_help() -> None:
    """Show available commands based on user role."""
    actor = resolve_actor()
    user_role = role_of(actor)

    print("\n🏢 COTERIE COMMAND DECK")
    print(f"🔑 User: {actor} (Role: {user_role})")
    print("=" * 50)

    # Get commands available to current user
    available_commands = [
        cmd for cmd, required in COMMAND_ROLES.items() if has_at_least(actor, required)
    ]

    # Group commands by category
    categories = {
        "Crew Operations": [
            cmd
            for cmd in available_commands
            if cmd
            in [
                "assign",
                "start_job",
                "end_job",
                "status",
                "board",
                "history",
                "view",
                "due",
            ]
        ],
        "Business Management": [
            cmd
            for cmd in available_commands
            if cmd in ["book", "list_bookings", "optimize", "optimize_schedule"]
        ],
        "Inventory Management": [cmd for cmd in available_commands if cmd.startswith("inv_")],
        "Intelligence & Weather": [
            cmd
            for cmd in available_commands
            if cmd in ["weather", "weather_check", "cluster_bookings"]
        ],
        "Communications": [
            cmd for cmd in available_commands if cmd in ["notify", "sms", "email_summary"]
        ],
        "Dashboard & Monitoring": [
            cmd for cmd in available_commands if cmd in ["dashboard", "deck"]
        ],
        "System Administration": [
            cmd for cmd in available_commands if cmd in ["user_mgmt", "logger_config", "config"]
        ],
        "System": [cmd for cmd in available_commands if cmd in ["help", "exit"]],
    }

    for category, commands in categories.items():
        if commands:
            print(f"\n  {category}:")
            for cmd in sorted(commands):
                print(f"    {cmd}")

    print("\n[ℹ️] Type '<command>' to execute")

    if user_role == "viewer":
        print("[🔒] Limited access - contact owner for role upgrade")


def main() -> None:
    """Main command deck loop."""
    context = {}

    # Show welcome message
    actor = resolve_actor()
    user_role = role_of(actor)

    print("\n🚀 Welcome to Coterie Command Deck!")
    print(f"🔑 Logged in as: {actor} (Role: {user_role})")
    print("📋 Type 'help' to see available commands")
    print("🚪 Type 'exit' to quit")
    print("-" * 50)

    while True:
        try:
            line = input("coterie>> ").strip()
            if not line:
                continue

            parts = shlex.split(line)
            cmd, args = parts[0], parts[1:]

            if cmd not in COMMANDS:
                print(f"[❌] Unknown command: '{cmd}'")
                print("[ℹ️] Type 'help' to see available commands")
                continue

            # Check permissions before executing
            if not _check_permission(cmd):
                continue

            # Execute command handler
            try:
                handler = COMMANDS[cmd]
                handler(args, context)
            except Exception as e:
                debug_log(f"[❌] Command '{cmd}' error: {e}")
                print(f"[❌] Error in '{cmd}': {e}")

        except (EOFError, KeyboardInterrupt):
            print("\n\n[👋] Exiting Coterie Command Deck. Have a great day!")
            break


def dispatch_command(argv: list[str]) -> int:
    if not argv:
        print_help()
        return 0
    _check_as_escalation(argv)
    cmd = argv[0]
    args = argv[1:]
    if cmd in COMMANDS:
        if _check_permission(cmd):
            return COMMANDS[cmd](args)
        else:
            return 2
    print(f"[❌] Unknown command: '{cmd}'")
    print("[ℹ️] Type 'help' to see available commands")
    return 1


if __name__ == "__main__":
    main()


# Create router object for compatibility with command_deck.py
class Router:
    def __init__(self) -> None:
        self.commands = COMMANDS

    def route(self, cmd: str, args: list[str], context: dict[str, Any]) -> None:
        """Route command to appropriate handler."""
        if cmd in self.commands:
            self.commands[cmd](args, context)
        else:
            print(f"[❌] Unknown command: '{cmd}'")


# Export router instance for command_deck.py compatibility
router = Router()
