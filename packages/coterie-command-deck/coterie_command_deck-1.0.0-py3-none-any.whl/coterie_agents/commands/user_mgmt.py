from __future__ import annotations

import getpass
import json
import os
from collections.abc import Callable
from typing import Any

from coterie_agents.utils import helper_funcs as _log

from ._cli import has_unknown_flags, wants_help


def _noop_debug_log(*args: Any, **kwargs: Any) -> None:
    return None


debug_log: Callable[..., None] = getattr(_log, "debug_log", _noop_debug_log)

COMMAND = "user_mgmt"
DESCRIPTION = "User management command for crew system."
USAGE = f"{COMMAND} [subcommand] [--help]"
USERS_FILE = "users.json"

# Default roles and their allowed commands
COMMAND_PERMISSIONS = {
    "admin": ["*"],  # all commands
    "manager": [
        "book",
        "list_bookings",
        "optimize_schedule",
        "dashboard",
        "notify",
        "weather_check",
        "cluster_bookings",
        "user_list",
        "user_roles",
        "user_whoami",
        "inv_add",
        "inv_remove",
        "inv_list",
        "inv_update",
        "inv_usage",
        "inv_check",
    ],
    "scheduler": [
        "book",
        "list_bookings",
        "optimize_schedule",
        "dashboard",
        "notify",
        "user_roles",
        "user_whoami",
        "inv_list",
        "inv_check",
    ],
    "viewer": [
        "status",
        "board",
        "list_bookings",
        "dashboard",
        "user_roles",
        "user_whoami",
        "inv_list",
    ],
}


def load_users() -> dict[str, str]:
    """Load users from file"""
    if not os.path.exists(USERS_FILE):
        # Create default users if file doesn't exist
        default_users = {"admin": "admin", "coterie": "manager"}
        save_users(default_users)
        return default_users

    try:
        with open(USERS_FILE) as f:
            return json.load(f)
    except Exception as e:
        debug_log(f"[❌] user_mgmt - load_users failed: {e}")
        return {}


def save_users(users: dict[str, str]) -> None:
    """Save users to file"""
    try:
        with open(USERS_FILE, "w") as f:
            json.dump(users, f, indent=2)
        debug_log(f"[✅] user_mgmt - saved {len(users)} users")
    except Exception as e:
        debug_log(f"[❌] user_mgmt - save_users failed: {e}")


def check_permission(command: str, context: Any | None = None) -> bool:
    """Check if current user has permission for command"""
    current = getpass.getuser()
    users = load_users()
    role = users.get(current, "viewer")  # Default to viewer if user not found

    allowed = COMMAND_PERMISSIONS.get(role, [])

    # Admin has access to everything
    if "*" in allowed:
        return True

    # Check if command is allowed for this role
    if command in allowed:
        return True

    # Always allow basic commands
    if command in ["help", "exit", "user_roles", "user_whoami"]:
        return True

    print(f"[🚫] Access denied. User '{current}' (role: {role}) cannot execute '{command}'")
    print(f"[ℹ️] Allowed commands: {', '.join(allowed)}")
    return False


def get_current_user_info() -> dict[str, str]:
    """Get current user's information"""
    current = getpass.getuser()
    users = load_users()
    role = users.get(current, "viewer")
    return {"username": current, "role": role}


def run(argv: list[str] | None = None, ctx: object | None = None) -> int:
    """Main CLI entry point for user management."""
    argv = argv or []
    known_flags = {"--help", "-h"}

    def print_help():
        print(
            """[ℹ️] User Management Commands:
  user_add <username> <role>      - Add/update user role (admin/manager only)
  user_remove <username>          - Remove user (admin only)
  user_list                       - List all users and roles
  user_roles                      - Show available roles and permissions
  user_whoami                     - Show current user and role

Available roles: admin, manager, scheduler, viewer"""
        )

    if wants_help(argv):
        print_help()
        return 0
    if has_unknown_flags(argv, known_flags):
        print("Not found")
        print_help()
        return 0
    args = argv if argv else []

    def handle_user_whoami(current: str, current_role: str):
        allowed = COMMAND_PERMISSIONS.get(current_role, [])
        print(f"🔑 Current User: {current}")
        print(f"👑 Role: {current_role}")
        if "*" in allowed:
            print("🚀 Permissions: All commands (admin access)")
        else:
            print(f"📋 Allowed Commands: {', '.join(allowed)}")

    def handle_user_roles(current_role: str):
        print("\n👑 Available Roles and Permissions:")
        print("-" * 60)
        for role, cmds in COMMAND_PERMISSIONS.items():
            if "*" in cmds:
                perms = "All commands (full admin access)"
            else:
                perms = ", ".join(cmds[:5])
                if len(cmds) > 5:
                    perms += f", ... ({len(cmds)} total)"
            print(f"  {role:<12} | {perms}")
        print(f"\n[ℹ️] Your current role: {current_role}")

    def handle_user_list(users: dict[str, str], current: str, current_role: str):
        print("\n👥 Coterie Platform Users:")
        print("-" * 40)
        for u, r in users.items():
            current_indicator = " (YOU)" if u == current else ""
            print(f"  • {u:<15} | {r:<10}{current_indicator}")
        print(f"\n🔑 You are logged in as: {current} (role: {current_role})")

    def handle_user_add(args: list[str], users: dict[str, str], current_role: str):
        if current_role not in ["admin", "manager"]:
            print(f"[🚫] Only admin/manager users can add users. Your role: {current_role}")
            return
        if len(args) != 3:
            print("[❌] Usage: user_add <username> <role>")
            return
        uname, role = args[1], args[2]
        if role not in COMMAND_PERMISSIONS:
            print(f"[❌] Invalid role. Choose from: {', '.join(COMMAND_PERMISSIONS.keys())}")
            return
        if current_role == "manager" and role == "admin":
            print("[🚫] Managers cannot create admin users")
            return
        action = "Updated" if uname in users else "Added"
        users[uname] = role
        save_users(users)
        print(f"[✅] {action} user '{uname}' with role '{role}'")

    def handle_user_remove(args: list[str], users: dict[str, str], current: str, current_role: str):
        if current_role != "admin":
            print_help()
            return
        if len(args) != 2:
            print("[❌] Usage: user_remove <username>")
            return
        uname = args[1]
        if uname == current:
            print("[❌] Cannot remove yourself")
            return
        if uname in users:
            del users[uname]
            save_users(users)
            print(f"[✅] Removed user '{uname}'")
        else:
            print(f"[⚠️] User '{uname}' not found")

    if not args:
        print_help()
        return 0
    cmd = args[0]
    users = load_users()
    current = getpass.getuser()
    current_role = users.get(current, "viewer")
    if cmd == "user_whoami":
        handle_user_whoami(current, current_role)
        return 0
    if cmd == "user_roles":
        handle_user_roles(current_role)
        return 0
    if cmd == "user_list":
        handle_user_list(users, current, current_role)
        return 0
    if cmd == "user_add":
        handle_user_add(args, users, current_role)
        return 0
    if cmd == "user_remove":
        handle_user_remove(args, users, current, current_role)
        return 0
    print(f"[❌] Unknown command: {cmd}")
    print("[ℹ️] Use 'user_mgmt' without arguments to see available commands")
    return 1
