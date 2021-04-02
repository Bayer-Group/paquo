import collections
import collections.abc as collections_abc
import json
import math
import weakref
from typing import Optional, Iterator, MutableSet, TypeVar, Type, Any, TYPE_CHECKING

from shapely.geometry import shape
from shapely.geometry.base import BaseGeometry

from paquo._base import QuPathBase
from paquo._logging import get_logger
from paquo.classes import QuPathPathClass
from paquo.java import GsonTools, PathObjectHierarchy, IllegalArgumentException
from paquo.pathobjects import QuPathPathAnnotationObject, _PathROIObject, QuPathPathDetectionObject, \
    QuPathPathTileObject

if TYPE_CHECKING:  # pragma: no cover
    import paquo.images

PathROIObjectType = TypeVar("PathROIObjectType", bound=_PathROIObject)
_logger = get_logger(__name__)


class _PathObjectSetProxy(MutableSet[PathROIObjectType]):
    """provides a python set interface for path objects"""

    def __init__(self, hierarchy: 'QuPathPathObjectHierarchy', paquo_cls: Type[PathROIObjectType]):
        self._hierarchy = hierarchy
        self._java_hierarchy = hierarchy.java_object
        self._paquo_cls = paquo_cls

    def add(self, x: PathROIObjectType) -> None:
        # noinspection PyProtectedMember
        if self._hierarchy._readonly:
            raise IOError("project in readonly mode")
        if not isinstance(x, self._paquo_cls):
            raise TypeError(f"requires {self._paquo_cls.__name__} instance got {x.__class__.__name__}")
        self._java_hierarchy.addPathObject(x.java_object)

    def discard(self, x: PathROIObjectType) -> None:
        # noinspection PyProtectedMember
        if self._hierarchy._readonly:
            raise IOError("project in readonly mode")
        if not isinstance(x, self._paquo_cls):
            raise TypeError(f"requires {self._paquo_cls.__name__} instance got {x.__class__.__name__}")
        self._java_hierarchy.removeObject(x.java_object, True)

    def __contains__(self, x: Any) -> bool:
        # ... inHierarchy is private
        # return bool(self._java_hierarchy.inHierarchy(x.java_object))
        if not isinstance(x, self._paquo_cls):
            return False
        while x.parent is not None:
            x = x.parent
        return bool(x.java_object == self._java_hierarchy.getRootObject())

    def __len__(self) -> int:
        return int(self._java_hierarchy.getObjects(None, self._paquo_cls.java_class).size())

    def __iter__(self) -> Iterator[PathROIObjectType]:
        for obj in self._java_hierarchy.getObjects(None, self._paquo_cls.java_class):
            yield self._paquo_cls(obj, _proxy_ref=self)

    def __repr__(self):
        return f"{self._paquo_cls.__name__}Set(n={len(self)})"

    # provide update
    update = collections_abc.MutableSet.__ior__


class QuPathPathObjectHierarchy(QuPathBase[PathObjectHierarchy]):

    def __init__(self, hierarchy: Optional[PathObjectHierarchy] = None,
                 *, _image_ref: Optional['paquo.images.QuPathProjectImageEntry'] = None) -> None:
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
        self._image_ref = weakref.ref(_image_ref) if _image_ref else lambda: None
        self._annotations = _PathObjectSetProxy(self, paquo_cls=QuPathPathAnnotationObject)  # type: ignore
        self._detections = _PathObjectSetProxy(self, paquo_cls=QuPathPathDetectionObject)  # type: ignore

    @property
    def _readonly(self):
        i = self._image_ref()
        if i is None:
            return False  # empty hierarchies can be modified!
        return getattr(i, "_readonly", False)

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
        if self._readonly:
            raise IOError("project in readonly mode")
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
        if self._readonly:
            raise IOError("project in readonly mode")
        """convenience method for adding detections

        Notes
        -----
        these will be added to self.detections
        """
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
        if self._readonly:
            raise IOError("project in readonly mode")
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

    def load_geojson(
            self, geojson: list,
            *, raise_on_skip: bool = False, fix_invalid: bool = False,
    ) -> bool:
        """load annotations into this hierarchy from a geojson list

        returns True if new objects were added, False otherwise.
        """
        # todo: use geojson module for type checking?
        if self._readonly:
            raise IOError("project in readonly mode")
        if not isinstance(geojson, list):
            raise TypeError("requires a geojson list")

        aos = []
        skipped = collections.Counter()  # type: ignore
        for annotation in geojson:
            try:
                if fix_invalid:
                    s = shape(annotation['geometry'])
                    if not s.is_valid:
                        # attempt to fix
                        s = s.buffer(0, 1)
                        if not s.is_valid:
                            s = s.buffer(0, 1)
                            if not s.is_valid:
                                raise ValueError("invalid geometry")
                    annotation['geometry'] = s.__geo_interface__
                ao = QuPathPathAnnotationObject.from_geojson(annotation)

            except (IllegalArgumentException, ValueError) as err:
                _logger.debug(f"Annotation skipped: {err}")
                class_ = annotation["properties"].get("classification", {}).get("name", "UNDEFINED")
                skipped[class_] += 1
                continue

            else:
                aos.append(ao.java_object)

        if skipped:
            n_skipped = sum(skipped.values())
            if raise_on_skip:
                raise ValueError(f"could not convert {n_skipped} annotations")
            _logger.error(
                f"skipped {n_skipped} annotation objects: {skipped.most_common()}"
            )

        return bool(self.java_object.insertPathObjects(aos))

    def __repr__(self):
        img: Optional['paquo.images.QuPathProjectImageEntry'] = self._image_ref()
        if img:
            img_name = img.image_name
        else:  # pragma: no cover
            img_name = 'N/A'
        return f"Hierarchy(image={img_name}, annotations={len(self._annotations)}, detections={len(self._detections)})"

    def _repr_html_(self):
        from paquo._repr import br, div, h4, p, span

        img: Optional['paquo.images.QuPathProjectImageEntry'] = self._image_ref()
        if img:
            img_name = img.image_name
        else:  # pragma: no cover
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
