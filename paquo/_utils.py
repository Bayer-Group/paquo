from datetime import datetime
from pathlib import Path

__all__ = ['cached_property', 'nullcontext', 'make_backup_filename']

try:
    from functools import cached_property  # type: ignore
except ImportError:
    # noinspection PyPep8Naming
    class cached_property:  # type: ignore  # https://github.com/python/mypy/issues/1153
        def __init__(self, getter):
            self.getter = getter
            self.name = getter.__name__

        def __get__(self, obj, objtype=None):
            if obj is None:
                return self  # pragma: no cover
            value = obj.__dict__[self.name] = self.getter(obj)
            return value

try:
    from contextlib import nullcontext  # type: ignore
except ImportError:
    from contextlib import suppress as nullcontext  # works with 3.4+


def make_backup_filename(path, name, suffix='backup'):
    path = Path(path)
    if not path.is_dir():
        raise ValueError("requires a directory")  # pragma: no cover
    now = datetime.now().strftime('%Y%m%d-%H%M%S')
    backup = path / f"{name}-{now}.{suffix}"
    if backup.is_file():
        raise RuntimeError(f"the file {backup} should not exist!")  # pragma: no cover
    return backup
