from __future__ import annotations

import os
import sys
import warnings
from collections.abc import Iterable

_DEPRECATED_ENVS: dict[str, str] = {
    "AGENTS_DEBUG": "Use AGENTS_LOG_LEVEL=DEBUG instead.",
    "USE_OLD_TASK_KEY": "The 'task' key is deprecated. Use 'tasks' (list[str]).",
}

_MIN_PY = (3, 11)


def configure_deprecation_handling(extra_envs: Iterable[str] | None = None) -> None:
    """
    Convert DeprecationWarning to errors and fail fast on deprecated env flags.
    Call this as early as possible in your entrypoint.
    """
    if sys.version_info < _MIN_PY:
        raise RuntimeError(f"Python {_MIN_PY[0]}.{_MIN_PY[1]}+ required.")

    # Strict mode: any DeprecationWarning becomes an error
    if os.getenv("AGENTS_DEPRECATION_STRICT") == "1":
        warnings.filterwarnings("error", category=DeprecationWarning)
    else:
        warnings.filterwarnings("default", category=DeprecationWarning)

    # Check known-deprecated env flags
    for key, remedy in _DEPRECATED_ENVS.items():
        if os.getenv(key) not in (None, ""):
            raise RuntimeError(f"Deprecated env var {key} set. {remedy}")

    # Optional: consumer-specified envs to forbid
    if extra_envs:
        for key in extra_envs:
            if os.getenv(key) not in (None, ""):
                raise RuntimeError(f"Unsupported env var {key} set.")
