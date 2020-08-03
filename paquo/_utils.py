
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
    from contextlib import nullcontext
except ImportError:
    from contextlib import suppress as nullcontext  # works with 3.4+

__all__ = ['cached_property', 'nullcontext']
