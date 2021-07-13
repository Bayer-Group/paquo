from typing import Optional

from paquo.colors import ColorType
from paquo.colors import QuPathColor
from paquo.java import PathClass
from paquo.java import PathClassFactory
from paquo.java import String

__all__ = ['QuPathPathClass']


class QuPathPathClass:
    java_object: PathClass

    @classmethod
    def from_java(cls, path_class: PathClass) -> 'QuPathPathClass':
        """initialize a QuPathPathClass from its corresponding java PathClass"""
        if not isinstance(path_class, PathClass):
            raise TypeError("use PathClass(name='myclass') to instantiate")
        # keep type annotation requirements intact by providing
        # empty string, which is ignored when providing _java_path_class
        return cls('', _java_path_class=path_class)

    def __init__(self,
                 name: str,
                 color: Optional[ColorType] = None,
                 parent: Optional['QuPathPathClass'] = None,
                 **_kwargs) -> None:
        """create a QuPathPathClass

        The QuPathPathClasses are wrappers around singletons defined by their
        name and their ancestors. Internally there's only one java PathClass
        instance per ancestor chain + name. (The internal unique id is chaining
        names via ':', which is why ':' is an unsupported name character)

        Parameters
        ----------
        name:
            the name of your path class
        color:
            a color (r,g,b) or (r,g,b,a) with 0 < x < 255 or a QuPathColor
            if color is None, a color calculated from the name is used
        parent:
            the parent of the class

        Returns
        -------
        path_class:
            the QuPathPathClass
        """
        # internal: check if a java path class was already provided
        _java_path_class = _kwargs.pop('_java_path_class', None)
        if _java_path_class is not None:
            self.java_object = _java_path_class
            return

        # called by user
        if name is None:
            if parent is None:
                # note:
                #   parent=None for name=None creates the root node on the qupath java side
                #   will have to consider if we expose this here.
                raise NotImplementedError("creating Root PathClass is currently not supported")
            else:
                raise ValueError("cannot create derived QuPathPathClass with name=None")
        elif isinstance(name, str):
            if ":" in name or "\n" in name:
                raise ValueError("PathClass names cannot contain ':' or '\n'")
            name = String(name)
        else:
            raise TypeError(f"name requires type 'str' got '{type(name)}'")

        # get the parent class if requested
        java_parent = None
        if parent is not None:
            if not isinstance(parent, QuPathPathClass):
                raise TypeError("parent must be a QuPathPathClass")
            java_parent = parent.java_object

        # set the color if requested
        java_color = None
        if color is not None:
            java_color = QuPathColor.from_any(color).to_java_rgba()  # use rgba?

        path_class = PathClassFactory.getDerivedPathClass(java_parent, name, java_color)
        self.java_object = path_class

    @property
    def name(self) -> str:
        """the name of the class"""
        return str(self.java_object.getName())

    @property
    def id(self) -> str:
        """the unique identifier string of the class"""
        return str(self.java_object.toString())

    def __eq__(self, other) -> bool:
        # check if path classes are identical
        if not isinstance(other, QuPathPathClass):
            return False
        return int(self.java_object.compareTo(other.java_object)) == 0

    @property
    def parent(self) -> Optional['QuPathPathClass']:
        """the parent path class of this path class"""
        path_class = self.java_object.getParentClass()
        if path_class is None:
            return None
        return QuPathPathClass.from_java(path_class)

    @property
    def origin(self) -> 'QuPathPathClass':
        """the toplevel parent of this path class"""
        origin_class = self
        while origin_class.parent is not None:
            origin_class = origin_class.parent
        return origin_class

    def is_derived_from(self, parent_class: 'QuPathPathClass'):
        """is this class derived from the parent_class"""
        return self.java_object.isDerivedFrom(parent_class.java_object)

    def is_ancestor_of(self, child_class: 'QuPathPathClass'):
        """is this class an ancestor of the child_class"""
        return self.java_object.isAncestorOf(child_class.java_object)

    @property
    def color(self) -> Optional[QuPathColor]:
        """return the path color"""
        rgb = self.java_object.getColor()
        if rgb is None:
            return None
        return QuPathColor.from_java_rgb(rgb)

    @color.setter
    def color(self, rgb: Optional[ColorType]) -> None:
        """set the path color"""
        if rgb is not None:
            rgb = QuPathColor.from_any(rgb).to_java_rgb()  # maybe use argb?
        self.java_object.setColor(rgb)

    @property
    def is_valid(self) -> bool:
        """check if the path class is valid"""
        return bool(self.java_object.isValid())

    @property
    def is_derived_class(self) -> bool:
        """check if the class is a derived path class"""
        return bool(self.java_object.isDerivedClass())

    def __repr__(self) -> str:
        return f"QuPathPathClass('{self.id}')"
