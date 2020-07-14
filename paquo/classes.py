from __future__ import annotations
from typing import Optional

from paquo._base import QuPathBase
from paquo.colors import QuPathColor, ColorType
from paquo.java import PathClass, PathClassFactory, ColorTools, String


class QuPathPathClass(QuPathBase[PathClass]):

    def __init__(self, path_class: PathClass) -> None:
        """initialize a QuPathPathClass from its corresponding java PathClass"""
        if not isinstance(path_class, PathClass):
            raise ValueError("use PathClass.create() to instantiate")
        super().__init__(path_class)

    @classmethod
    def create(cls,
               name: str,
               color: Optional[ColorType] = None,
               parent: Optional[QuPathPathClass] = None) -> QuPathPathClass:
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
        if name is None:
            # note:
            #   parent=None for name=None creates the root node on the qupath java side
            #   will have to consider if we expose this here.
            if parent is not None:
                raise ValueError("cannot create derived QuPathPathClass with name=None")
        name = String(name)

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
        return cls(path_class)

    @property
    def name(self) -> str:
        """the name of the class"""
        return str(self.java_object.getName())

    @property
    def id(self) -> str:
        """the unique identifier string of the class"""
        return str(self.java_object.toString())

    def __eq__(self, other: QuPathPathClass) -> bool:
        # check if path classes are identical
        if not isinstance(other, QuPathPathClass):
            return False
        return self.java_object.compareTo(other.java_object)

    @property
    def parent(self) -> Optional[QuPathPathClass]:
        """the parent path class of this path class"""
        path_class = self.java_object.getParentClass()
        if path_class is None:
            return None
        return QuPathPathClass(path_class)

    @property
    def origin(self) -> QuPathPathClass:
        """the toplevel parent of this path class"""
        origin_class = self
        while origin_class.parent is not None:
            origin_class = origin_class.parent
        return origin_class

    def is_derived_from(self, parent_class: QuPathPathClass):
        """is this class derived from the parent_class"""
        return self.java_object.isDerivedFrom(parent_class.java_object)

    def is_ancestor_of(self, child_class: QuPathPathClass):
        """is this class an ancestor of the child_class"""
        return self.java_object.isAncestorOf(child_class.java_object)

    @property
    def color(self) -> QuPathColor:
        """return the path color"""
        argb = self.java_object.getColor()
        return QuPathColor.from_java_rgba(argb)

    @color.setter
    def color(self, rgb: ColorType) -> None:
        """set the path color"""
        argb = ColorTools.from_any(rgb).to_java_argb()  # maybe use argb?
        self.java_object.setColor(argb)

    @property
    def is_valid(self) -> bool:
        """check if the path class is valid"""
        return bool(self.java_object.isValid())

    @property
    def is_derived_class(self) -> bool:
        """check if the class is a derived path class"""
        return bool(self.java_object.isDerivedClass())

    def __repr__(self) -> str:
        return f"<QuPathPathClass '{self.id}'>"
