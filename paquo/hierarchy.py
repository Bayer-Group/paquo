import collections.abc as collections_abc
import json
import math
from typing import Optional, Iterator, MutableSet

from shapely.geometry.base import BaseGeometry

from paquo._base import QuPathBase
from paquo.classes import QuPathPathClass
from paquo.java import GsonTools, PathObjectHierarchy
from paquo.pathobjects import QuPathPathAnnotationObject


class _AnnotationsListProxy(MutableSet[QuPathPathAnnotationObject]):
    """provides a python set interface for annotations"""

    def __init__(self, hierarchy: PathObjectHierarchy):
        self._hierarchy = hierarchy

    def add(self, x: QuPathPathAnnotationObject) -> None:
        self._hierarchy.addPathObject(x.java_object)

    def discard(self, x: QuPathPathAnnotationObject) -> None:
        self._hierarchy.removeObject(x.java_object, True)

    def __contains__(self, x: QuPathPathAnnotationObject) -> bool:
        # ... inHierarchy is private
        # return bool(self._hierarchy.inHierarchy(x.java_object))
        while x.parent is not None:
            x = x.parent
        return x.java_object == self._hierarchy.getRootObject()

    def __len__(self) -> int:
        return int(self._hierarchy.getAnnotationObjects().size())

    def __iter__(self) -> Iterator[QuPathPathAnnotationObject]:
        return map(QuPathPathAnnotationObject, self._hierarchy.getAnnotationObjects())

    def __repr__(self):
        return f"<AnnotationSet(n={len(self)})>"

    # provide update
    update = collections_abc.MutableSet.__ior__


class QuPathPathObjectHierarchy(QuPathBase[PathObjectHierarchy]):

    def __init__(self, hierarchy: Optional[PathObjectHierarchy] = None) -> None:
        """qupath hierarchy stores all annotation objects

        Parameters
        ----------
        hierarchy:
            a PathObjectHierarchy instance (optional)
            Usually accessed directly via the Image Container.
        """
        if hierarchy is None:
            hierarchy = PathObjectHierarchy()
        super().__init__(hierarchy)
        self._annotations = _AnnotationsListProxy(hierarchy)

    def __len__(self) -> int:
        """Number of objects in hierarchy (all types)"""
        return int(self.java_object.nObjects())

    @property
    def is_empty(self) -> bool:
        """a hierarchy is empty if it only contains the root object"""
        return bool(self.java_object.isEmpty())

    @property
    def root(self) -> QuPathPathAnnotationObject:
        """the hierarchy root node

        This object has no roi and cannot be assigned another class.
        All other objects are descendants of this object if they are
        attached to this hierarchy.
        """
        root = self.java_object.getRootObject()
        return QuPathPathAnnotationObject(root)  # todo: specialize...

    @property
    def annotations(self) -> _AnnotationsListProxy:
        """all annotations provided as a flattened set-like proxy"""
        return self._annotations

    def add_annotation(self,
                       roi: BaseGeometry,
                       path_class: Optional[QuPathPathClass] = None,
                       measurements: Optional[dict] = None,
                       *,
                       path_class_probability: float = math.nan):
        """convenience method for adding annotations"""
        ao = QuPathPathAnnotationObject.from_shapely(
            roi, path_class, measurements,
            path_class_probability=path_class_probability
        )
        self._annotations.add(ao)
        return ao

    def to_geojson(self) -> list:
        """return all annotations as a list of geojson features"""
        gson = GsonTools.getInstance()
        geojson = gson.toJson(self.java_object.getAnnotationObjects())
        return json.loads(str(geojson))

    def load_geojson(self, geojson: list) -> bool:
        """load annotations into this hierarchy from a geojson list

        returns True if new objects were added, False otherwise.
        """
        # todo: use geojson module for type checking?
        if not isinstance(geojson, list):
            raise TypeError("requires a geojson list")
        changed = False
        for annotation in geojson:
            ao = QuPathPathAnnotationObject.from_geojson(annotation)
            changed |= self.java_object.insertPathObject(ao.java_object, True)
        return changed

    def __repr__(self):
        return f"<Hierarchy(n_annotations={len(self._annotations)})>"