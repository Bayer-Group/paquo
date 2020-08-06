from functools import wraps
from io import UnsupportedOperation
from pathlib import Path
from typing import Optional

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


def stash_project_files(project_dir: Path):
    """move rename projects files in a project to .backup"""
    if not project_dir.is_dir():
        return
    for old_file in project_dir.iterdir():
        if old_file.suffix == ".backup":
            continue
        new_file = old_file.with_suffix(f"{old_file.suffix}.backup")
        i = 0
        while new_file.is_file():
            new_file = old_file.with_suffix(f"{old_file.suffix}.{i}.backup")
        old_file.rename(new_file)


__all__ = ['cached_property', 'nullcontext', 'stash_project_files']
