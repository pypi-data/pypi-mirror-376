import warnings

from coterie_agents import *  # noqa: F403
from coterie_agents import __all__ as _ALL

__all__ = list(_ALL)

warnings.warn(
    "Importing 'agents' is deprecated; use 'coterie_agents' instead.",
    DeprecationWarning,
    stacklevel=2,
)
