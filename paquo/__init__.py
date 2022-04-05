try:
    from ._version import version as __version__
except ImportError:  # pragma: no cover
    __version__ = "not-installed"

# noinspection PyUnresolvedReferences
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
