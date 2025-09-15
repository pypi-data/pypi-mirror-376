# attach.py - Command module for 'attach'
from __future__ import annotations

from ._cli import has_unknown_flags, print_help, safe_ctx_store, wants_help

COMMAND = "attach"
DESCRIPTION = "Attach a file or note to a crew member."
USAGE = f"{COMMAND} <member> <attachment> [--help]"


def run(argv: list[str] | None = None, ctx: object = None) -> int:
    argv = argv or []
    known_flags = {"--help", "-h"}

    if wants_help(argv):
        print_help(COMMAND, DESCRIPTION, USAGE)
        return 0

    if has_unknown_flags(argv, known_flags):
        print("Not found")
        print_help(COMMAND, DESCRIPTION, USAGE)
        return 0

    if len(argv) < 2:
        print_help(COMMAND, DESCRIPTION, USAGE)
        return 0

    name, attachment = argv[0], argv[1]
    store = safe_ctx_store(ctx)
    member = store.get(name, {"name": name, "attachments": []})
    attachments = member.get("attachments", [])
    attachments.append(str(attachment))
    member["attachments"] = attachments
    store[name] = member
    print(f"[✅] Attached to {name}: {attachment}")
    return 0
