import contextlib
import importlib
from types import SimpleNamespace


def test_help_cmd_else_path():
    mod = importlib.import_module("coterie_agents.commands.help_cmd")
    ctx = SimpleNamespace(router=SimpleNamespace(get_available_commands=lambda **_: []))
    mod.run(["not_a_command"], ctx)  # should print "Not found"


def test_logger_config_invalid_level():
    mod = importlib.import_module("coterie_agents.commands.logger_config")
    ctx = {"log_level": "INFO"}
    with contextlib.suppress(ValueError):
        mod.configure("NOTALEVEL", ctx)
