from typing import Generic, TypeVar

T = TypeVar('T')


class QuPathBase(Generic[T]):
    """QuPathBase class for composite classes in paquo"""

    def __init__(self, java_object: T) -> None:
        # todo: add typechecking?
        self._java_object = java_object

    @property
    def java_object(self) -> T:
        """access to the underlying java class"""
        return self._java_object
