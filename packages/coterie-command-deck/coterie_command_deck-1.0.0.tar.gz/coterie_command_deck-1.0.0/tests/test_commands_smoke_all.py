import contextlib
import importlib
import pkgutil
from types import SimpleNamespace

import coterie_agents.commands as commands_pkg


def iter_command_modules():
    for m in pkgutil.iter_modules(commands_pkg.__path__, commands_pkg.__name__ + "."):
        yield importlib.import_module(m.name)


def safe_ctx():
    return SimpleNamespace(
        router=SimpleNamespace(get_available_commands=lambda **_: []),
        log_level="INFO",
        store={},
    )


def test_import_all_command_modules():
    for mod in iter_command_modules():
        assert mod.__name__.startswith("coterie_agents.commands")


def _try_run(mod, argv=None, ctx_obj=None, ctx_dict=None):
    argv = argv or []
    if hasattr(mod, "run"):
        with contextlib.suppress(TypeError):
            mod.run(argv, ctx_obj)
        with contextlib.suppress(TypeError):
            mod.run(argv, {"store": {}, "log_level": "INFO"})


def test_run_zero_arg_safe():
    ctx_obj = safe_ctx()
    for mod in iter_command_modules():
        _try_run(mod, [], ctx_obj)


def test_run_help_arg_safe():
    ctx_obj = safe_ctx()
    for mod in iter_command_modules():
        _try_run(mod, ["--help"], ctx_obj)
