import importlib
import pkgutil

import pytest

import coterie_agents.bots as bots_pkg

# These run long loops/schedulers; import-only in smoke.
SKIP = {"auto_cleaner_bot", "reminder_bot", "watchdog_bot", "logger_bot"}

# These run long loops/schedulers; import-only in smoke.
SKIP = {"auto_cleaner_bot", "reminder_bot", "watchdog_bot", "logger_bot"}


def _iter_bot_modules() -> list[str]:
    return [
        m.name
        for m in pkgutil.iter_modules(bots_pkg.__path__, bots_pkg.__name__ + ".")
        if m.name.rsplit(".", 1)[-1] not in SKIP
    ]


@pytest.mark.parametrize("modname", _iter_bot_modules())
def test_bot_modules_import_only(modname: str) -> None:
    # Import-only smoke (no entrypoint calls) to avoid side effects.
    importlib.import_module(modname)
