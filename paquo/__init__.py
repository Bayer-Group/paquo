from typing import TYPE_CHECKING

try:
    from ._version import version as __version__
except ImportError:  # pragma: no cover
    __version__ = "not-installed"

if TYPE_CHECKING:
    from dynaconf import Dynaconf
    settings: Dynaconf

__all__ = [
    "__version__",
    "settings",
]


def __getattr__(name):
    if name == "settings":
        from paquo._config import settings
        return settings
    else:
        raise AttributeError(name)
