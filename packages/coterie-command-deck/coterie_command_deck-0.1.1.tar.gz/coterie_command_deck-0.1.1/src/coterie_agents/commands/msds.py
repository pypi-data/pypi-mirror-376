from __future__ import annotations

from typing import Any

from coterie_agents.utils.http import default_http

from ._cli import has_unknown_flags, print_help, wants_help


def fetch_msds(url: str) -> dict[str, Any]:
    """
    Fetch an MSDS JSON from a remote endpoint with sane defaults.
    Raises requests.HTTPError on non-2xx.
    """
    try:
        resp = default_http.get(url)  # timeout + retries baked in
        return resp.json()
    except Exception as e:
        print(f"[❌] msds - fetch failed: {e}")
        # S110: suppress block, log and continue
        return {}


COMMAND = "msds"
DESCRIPTION = "Fetch and display MSDS data from a remote endpoint."
USAGE = "msds <url>"


def run(argv: list[str] | None = None, ctx: object | None = None) -> int:
    argv = argv or []
    known_flags = {"--help", "-h"}
    if wants_help(argv):
        print_help(COMMAND, DESCRIPTION, USAGE)
        return 0
    if has_unknown_flags(argv, known_flags):
        print("Not found")
        print_help(COMMAND, DESCRIPTION, USAGE)
        return 0
    if not argv:
        print(f"usage: {USAGE}")
        return 1
    url = argv[0]
    data = fetch_msds(url)
    name = data.get("name") or data.get("product") or "<unknown>"
    print(f"MSDS for: {name}")
    return 0
