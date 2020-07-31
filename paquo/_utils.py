
try:
    from functools import cached_property
except ImportError:
    # noinspection PyPep8Naming
    class cached_property(object):
        def __init__(self, getter):
            self.getter = getter
            self.name = getter.__name__

        def __get__(self, obj, objtype=None):
            if obj is None:
                return self
            value = obj.__dict__[self.name] = self.getter(obj)
            return value
