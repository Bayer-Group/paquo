import collections.abc as collections_abc
import json
import math
import weakref
from typing import Optional, Iterator, MutableSet, TypeVar, Type, Any, TYPE_CHECKING

from shapely.geometry.base import BaseGeometry

from paquo._base import QuPathBase
from paquo.classes import QuPathPathClass
from paquo.java import GsonTools, PathObjectHierarchy
from paquo.pathobjects import QuPathPathAnnotationObject, _PathROIObject, QuPathPathDetectionObject, \
    QuPathPathTileObject
if TYPE_CHECKING:
    from paquo.images import QuPathProjectImageEntry

PathROIObjectType = TypeVar("PathROIObjectType", bound=_PathROIObject)


class _PathObjectSetProxy(MutableSet[PathROIObjectType]):
    """provides a python set interface for path objects"""

    def __init__(self, hierarchy: PathObjectHierarchy, paquo_cls: Type[_PathROIObject[Any]]):
        self._hierarchy = hierarchy
        self._paquo_cls = paquo_cls

    def add(self, x: PathROIObjectType) -> None:
        if not isinstance(x, self._paquo_cls):
            raise TypeError(f"requires {self._paquo_cls.__name__} instance got {x.__class__.__name__}")
        self._hierarchy.addPathObject(x.java_object)

    def discard(self, x: PathROIObjectType) -> None:
        if not isinstance(x, self._paquo_cls):
            raise TypeError(f"requires {self._paquo_cls.__name__} instance got {x.__class__.__name__}")
        self._hierarchy.removeObject(x.java_object, True)

    def __contains__(self, x: object) -> bool:
        # ... inHierarchy is private
        # return bool(self._hierarchy.inHierarchy(x.java_object))
        if not isinstance(x, self._paquo_cls):
            return False
        while x.parent is not None:
            x = x.parent
        return bool(x.java_object == self._hierarchy.getRootObject())

    def __len__(self) -> int:
        return int(self._hierarchy.getObjects(None, self._paquo_cls.java_class).size())

    def __iter__(self) -> Iterator[PathROIObjectType]:
        return map(self._paquo_cls, self._hierarchy.getObjects(None, self._paquo_cls.java_class))  # type: ignore

    def __repr__(self):
        return f"<{self._paquo_cls.__name__}Set n={len(self)}>"

    # provide update
    update = collections_abc.MutableSet.__ior__


class QuPathPathObjectHierarchy(QuPathBase[PathObjectHierarchy]):

    def __init__(self, hierarchy: Optional[PathObjectHierarchy] = None,
                 *, _image_ref: Optional['QuPathProjectImageEntry'] = None) -> None:
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
        self._annotations = _PathObjectSetProxy(hierarchy, paquo_cls=QuPathPathAnnotationObject)  # type: ignore
        self._detections = _PathObjectSetProxy(hierarchy, paquo_cls=QuPathPathDetectionObject)  # type: ignore
        self._image_ref = weakref.ref(_image_ref) if _image_ref else lambda: None

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
    def annotations(self) -> _PathObjectSetProxy[QuPathPathAnnotationObject]:
        """all annotations provided as a flattened set-like proxy"""
        return self._annotations

    def add_annotation(self,
                       roi: BaseGeometry,
                       path_class: Optional[QuPathPathClass] = None,
                       measurements: Optional[dict] = None,
                       *,
                       path_class_probability: float = math.nan) -> QuPathPathAnnotationObject:
        """convenience method for adding annotations"""
        obj = QuPathPathAnnotationObject.from_shapely(
            roi, path_class, measurements,
            path_class_probability=path_class_probability
        )
        self._annotations.add(obj)
        return obj

    @property
    def detections(self) -> _PathObjectSetProxy[QuPathPathDetectionObject]:
        """all detections provided as a flattened set-like proxy"""
        return self._detections

    def add_detection(self,
                      roi: BaseGeometry,
                      path_class: Optional[QuPathPathClass] = None,
                      measurements: Optional[dict] = None,
                      *,
                      path_class_probability: float = math.nan) -> QuPathPathDetectionObject:
        """convenience method for adding detections"""
        obj = QuPathPathDetectionObject.from_shapely(
            roi, path_class, measurements,
            path_class_probability=path_class_probability
        )
        self._detections.add(obj)
        return obj

    def add_tile(self,
                 roi: BaseGeometry,
                 path_class: Optional[QuPathPathClass] = None,
                 measurements: Optional[dict] = None,
                 *,
                 path_class_probability: float = math.nan) -> QuPathPathTileObject:
        """convenience method for adding tile detections

        Notes
        -----
        these will be added to self.detections
        """
        obj = QuPathPathTileObject.from_shapely(
            roi, path_class, measurements,
            path_class_probability=path_class_probability
        )
        self._detections.add(obj)
        return obj

    def to_geojson(self) -> list:
        """return all annotations as a list of geojson features"""
        gson = GsonTools.getInstance()
        geojson = gson.toJson(self.java_object.getAnnotationObjects())
        return list(json.loads(str(geojson)))

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
        img: Optional['QuPathProjectImageEntry'] = self._image_ref()
        if img:
            img_name = img.image_name
        else:
            img_name = 'N/A'
        return f"<Hierarchy image={img_name} annotations={len(self._annotations)} detections={len(self._detections)}>"

    def _repr_html_(self):
        from paquo._repr import br, div, h4, p, span

        img: Optional['QuPathProjectImageEntry'] = self._image_ref()
        if img:
            img_name = img.image_name
        else:
            img_name = 'N/A'
        return div(
            h4(text=f"Hierarchy: {img_name}", style={"margin-top": "0"}),
            p(
                span(text="annotations: ", style={"font-weight": "bold"}),
                span(text=f"{len(self._annotations)}"),
                br(),
                span(text="detections: ", style={"font-weight": "bold"}),
                span(text=f"{len(self._detections)}"),
                style={"margin": "0.5em"},
            ),
        )
