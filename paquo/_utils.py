import json
import lzma
from datetime import datetime
from pathlib import Path

__all__ = ['cached_property', 'nullcontext', 'make_backup_filename', 'load_json_from_path']

try:
    from functools import cached_property as _cached_property # type: ignore

    # noinspection PyPep8Naming
    class cached_property(_cached_property):
        def __set__(self, obj, value):
            raise AttributeError(f"readonly attribute {self.attrname}")
except ImportError:
    # noinspection PyPep8Naming
    class cached_property:  # type: ignore  # https://github.com/python/mypy/issues/1153
        _NOCACHE = object()

        def __init__(self, fget):
            self.fget = fget
            self.attrname = None
            self.__doc__ = fget.__doc__

        def __set_name__(self, owner, name):
            self.attrname = name

        def __get__(self, obj, objtype=None):
            if obj is None:
                return self  # pragma: no cover
            cache = obj.__dict__
            val = cache.get(self.attrname, self._NOCACHE)
            if val is self._NOCACHE:
                val = cache[self.attrname] = self.fget(obj)
            return val

        def __set__(self, obj, value):
            raise AttributeError(f"readonly attribute {self.fget.__name__}")

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


def load_json_from_path(path):
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(str(path))  # pragma: no cover

    if path.name.endswith(".geojson.xz"):
        ctx = lambda: lzma.open(path, 'rt')
    elif path.name.endswith(('.geojson', '.json')):
        ctx = lambda: path.open('r')
    else:
        raise NotImplementedError(f"unsupported file format '{path}'")

    with ctx() as fobj:
        data = json.load(fobj)

    if isinstance(data, dict):
        return data
    elif isinstance(data, list):
        return {'annotations': data}
    else:
        raise ValueError("expected dict or list of annotations")
