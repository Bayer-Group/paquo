import collections
import json
import math
import reprlib
import struct
from contextlib import contextmanager
from contextlib import suppress
from typing import Any
from typing import Counter as CounterType
from typing import Iterable
from typing import Iterator
from typing import MutableSet
from typing import Optional
from typing import Sequence
from typing import Type
from typing import Union
from typing import overload

from paquo._logging import get_logger
from paquo._utils import cached_property
from paquo.classes import QuPathPathClass
from paquo.java import GsonTools
from paquo.java import IllegalArgumentException
from paquo.java import PathObjectHierarchy
from paquo.java import compatibility
from paquo.pathobjects import BaseGeometry
from paquo.pathobjects import PathROIObjectType
from paquo.pathobjects import QuPathPathAnnotationObject
from paquo.pathobjects import QuPathPathDetectionObject
from paquo.pathobjects import QuPathPathTileObject
from paquo.pathobjects import fix_geojson_geometry

__all__ = ["QuPathPathObjectHierarchy"]

_logger = get_logger(__name__)


class PathObjectProxy(Sequence[PathROIObjectType], MutableSet[PathROIObjectType]):
    """set interface for path objects with support for access by index and slicing

    *not meant to be instantiated by the user*

    Notes
    -----
    Access this proxy via the `QuPathPathObjectHierarchy.annotations` or
    `QuPathPathObjectHierarchy.detections` properties. It acts just like
    a python set, but also supports access by index and slicing.

    """

    def __init__(
        self,
        hierarchy: 'QuPathPathObjectHierarchy',
        paquo_cls: Type[PathROIObjectType],
        mask: Optional[Union[slice, Sequence[int]]] = None,
    ) -> None:
        """internal: not meant to be instantiated by the user"""
        self._hierarchy = hierarchy
        self._paquo_cls = paquo_cls
        if not (
            mask is None
            or isinstance(mask, slice)
            or (all(isinstance(x, int) for x in mask) and len(mask) > 0)
        ):
            raise TypeError(f"mask can be slice, or Sequence[int] or None. Got: {type(mask)!r}")
        self._mask: Optional[Union[slice, Sequence[int]]] = mask

    @property
    def _readonly(self) -> bool:
        # noinspection PyProtectedMember
        return self._hierarchy._readonly or self._mask is not None

    @property
    def _java_hierarchy(self):
        return self._hierarchy.java_object

    @cached_property
    def _list(self):
        _list = self._java_hierarchy.getObjects(None, self._paquo_cls.java_class)
        if self._mask:
            if isinstance(self._mask, slice):
                _list = _list[self._mask]
            else:
                _list = [_list[x] for x in self._mask]
        return _list

    def _list_invalidate_cache(self):
        with suppress(KeyError):
            del self.__dict__["_list"]

    def _disabled(self, other: Iterable[Any]) -> "PathObjectProxy":
        raise NotImplementedError(f"{type(self).__name__} only supports inplace operations: '|=', '-='")
    __or__ = __and__ = __sub__ = __xor__ = __iand__ = __ixor__ = _disabled
    del _disabled

    def __ior__(self, other: Iterable[Any]) -> "PathObjectProxy":  # type: ignore
        if self._mask:
            raise OSError("cannot modify view")
        if self._readonly:
            raise OSError("project in readonly mode")
        path_objects = [x.java_object for x in other]
        try:
            self._java_hierarchy.addPathObjects(path_objects)
        finally:
            self._list_invalidate_cache()
        return self
    update = __ior__

    def __isub__(self, other: Iterable[Any]) -> "PathObjectProxy":  # type: ignore
        if self._mask:
            raise OSError("cannot modify view")
        if self._readonly:
            raise OSError("project in readonly mode")
        path_objects = [x.java_object for x in other]
        try:
            self._java_hierarchy.removeObjects(path_objects, True)
        finally:
            self._list_invalidate_cache()
        return self

    def add(self, x: PathROIObjectType) -> None:
        """adds a new path object to the proxy"""
        if self._mask:
            raise OSError("cannot modify view")
        if self._readonly:
            raise OSError("project in readonly mode")
        if not isinstance(x, self._paquo_cls):
            raise TypeError(f"requires {self._paquo_cls.__name__} instance got {x.__class__.__name__}")
        try:
            if self._hierarchy.autoflush:
                self._java_hierarchy.addPathObject(x.java_object)
            else:
                self._java_hierarchy.addPathObjectWithoutUpdate(x.java_object)
        finally:
            self._list_invalidate_cache()

    def discard(self, x: PathROIObjectType) -> None:
        """discard a path object from the proxy"""
        if self._mask:
            raise OSError("cannot modify view")
        if self._readonly:
            raise OSError("project in readonly mode")
        if not isinstance(x, self._paquo_cls):
            raise TypeError(f"requires {self._paquo_cls.__name__} instance got {x.__class__.__name__}")
        try:
            if self._hierarchy.autoflush:
                self._java_hierarchy.removeObject(x.java_object, True)
            else:
                self._java_hierarchy.removeObjectWithoutUpdate(x.java_object, True)
        finally:
            self._list_invalidate_cache()

    def clear(self) -> None:
        """clear all path objects from the proxy"""
        if self._mask:
            raise OSError("cannot modify view")
        if self._readonly:
            raise OSError("project in readonly mode")
        try:
            self._java_hierarchy.removeObjects(self._list, True)
        finally:
            self._list_invalidate_cache()

    def __contains__(self, x: Any) -> bool:
        """test if path object is in proxy"""
        # ... inHierarchy is private
        # return bool(self._java_hierarchy.inHierarchy(x.java_object))
        if not isinstance(x, self._paquo_cls):
            return False
        while x.parent is not None:
            x = x.parent
        return bool(x.java_object == self._java_hierarchy.getRootObject())

    def __len__(self) -> int:
        return len(self._list)

    def __iter__(self: "PathObjectProxy") -> Iterator[PathROIObjectType]:
        for obj in self._list:
            yield self._paquo_cls(obj, update_callback=self.add)

    @overload
    def __getitem__(self, i: int) -> PathROIObjectType: ...
    @overload
    def __getitem__(self, i: slice) -> "PathObjectProxy": ...
    @overload
    def __getitem__(self, i: Sequence[int]) -> "PathObjectProxy": ...

    def __getitem__(self, i):
        if isinstance(i, int):
            return self._paquo_cls(self._list[i], update_callback=self.add)
        elif isinstance(i, slice):
            if self._mask is None:
                mask = i
            elif isinstance(self._mask, slice):
                _r = range(self._java_hierarchy.nObjects())
                _s = _r[self._mask][i]
                mask = slice(_s.start, _s.stop, _s.step)
            else:
                mask = self._mask[i]
            return PathObjectProxy(self._hierarchy, self._paquo_cls, mask)
        else:
            if self._mask is None:
                mask = i
            elif isinstance(self._mask, slice):
                _r = range(self._java_hierarchy.nObjects())
                _s = _r[self._mask]
                mask = [_s[idx] for idx in i]
            else:
                mask = [self._mask[idx] for idx in i]
            return PathObjectProxy(self._hierarchy, self._paquo_cls, mask)

    def count(self, value: PathROIObjectType) -> int:
        return int(value in self)  # PathObjectProxy is a set

    def __repr__(self):
        c = type(self).__name__
        h = repr(self._hierarchy)
        p = self._paquo_cls.__name__
        m = reprlib.repr(self._mask)
        i = f"0x{hex(id(self))}"
        if m is None:
            return f"<{c} hierarchy={h} paquo_cls={p} at {i}>"
        return f"<{c} hierarchy={h} paquo_cls={p} mask={m} at {i}>"


class QuPathPathObjectHierarchy:
    java_object: PathObjectHierarchy

    def __init__(
        self,
        hierarchy: Optional[PathObjectHierarchy] = None,
        *,
        readonly: bool = False,
        image_name: str = "N/A",
        autoflush: bool = True,
    ) -> None:
        """qupath hierarchy stores all annotation objects

        Parameters
        ----------
        hierarchy:
            a PathObjectHierarchy instance (optional)
            Usually accessed directly via the Image Container.
        """
        if hierarchy is None:
            hierarchy = PathObjectHierarchy()
        self.java_object = hierarchy
        # internals
        self._image_name = str(image_name)
        self._readonly = bool(readonly)
        self._annotations = PathObjectProxy(self, paquo_cls=QuPathPathAnnotationObject)
        self._detections = PathObjectProxy(self, paquo_cls=QuPathPathDetectionObject)
        # attrs
        self.autoflush = bool(autoflush)

    def __len__(self) -> int:
        """Number of objects in hierarchy (all types)"""
        return int(self.java_object.nObjects())

    @property
    def is_empty(self) -> bool:
        """a hierarchy is empty if it only contains the root object"""
        return bool(self.java_object.isEmpty())

    @contextmanager
    def no_autoflush(self):
        """prevent updates to the hierarchy to trigger an internal update event"""
        _autoflush, self.autoflush = self.autoflush, False
        try:
            yield self
        finally:
            self.flush(invalidate_proxy_cache=True)
            self.autoflush = _autoflush

    # noinspection PyProtectedMember
    def flush(self, invalidate_proxy_cache: bool = False):
        """flush changes to the hierarchy"""
        root = self.java_object.getRootObject()
        self.java_object.fireHierarchyChangedEvent(root)
        if invalidate_proxy_cache:
            self._annotations._list_invalidate_cache()
            self._detections._list_invalidate_cache()

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
    def annotations(self) -> PathObjectProxy[QuPathPathAnnotationObject]:
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
            raise OSError("project in readonly mode")
        obj = QuPathPathAnnotationObject.from_shapely(
            roi, path_class, measurements,
            path_class_probability=path_class_probability
        )
        self._annotations.add(obj)
        return obj

    @property
    def detections(self) -> PathObjectProxy[QuPathPathDetectionObject]:
        """all detections provided as a flattened set-like proxy"""
        return self._detections

    def add_detection(self,
                      roi: BaseGeometry,
                      path_class: Optional[QuPathPathClass] = None,
                      measurements: Optional[dict] = None,
                      *,
                      path_class_probability: float = math.nan) -> QuPathPathDetectionObject:
        if self._readonly:
            raise OSError("project in readonly mode")
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
            raise OSError("project in readonly mode")
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
            raise OSError("project in readonly mode")
        if not isinstance(geojson, list):
            raise TypeError("requires a geojson list")

        aos = []
        skipped: "CounterType[str]" = collections.Counter()
        for annotation in geojson:
            try:
                if fix_invalid:
                    annotation["geometry"] = fix_geojson_geometry(annotation["geometry"])

                # compatibility layer
                # todo: should maybe test at the beginning of this method
                #   if the version supports id or not, instead of checking
                #   the version number...
                if (
                    compatibility.requires_annotation_json_fix()
                    and 'id' not in annotation
                ):
                    object_type = annotation['properties'].get("object_type", "unknown")
                    object_id = {
                        'annotation': "PathAnnotationObject",
                        'detection': "PathDetectionObject",
                        'tile': "PathTileObject",
                        'cell': "PathCellObject",
                        'tma_core': "TMACoreObject",
                        'root': "PathRootObject",
                        'unknown': "PathAnnotationObject",
                    }.get(object_type, None)
                    if object_id is None:
                        _logger.warn(f"annotation has incompatible object_type: '{object_type}'")
                        object_id = "PathAnnotationObject"
                    annotation['id'] = object_id

                ao = QuPathPathAnnotationObject.from_geojson(annotation)

            except (IllegalArgumentException, ValueError) as err:
                _logger.warn(f"Annotation skipped: {err}")
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

        updated = bool(self.java_object.insertPathObjects(aos))
        if updated:
            self.flush(invalidate_proxy_cache=True)
        return updated

    def to_ome_xml(self, prefix="paquo", fill_alpha=0.0) -> str:
        """return all annotations in ome xml format"""
        # this
        try:
            from ome_types import to_xml
            from ome_types.model import OME
            from ome_types.model import ROI
            from ome_types.model import AnnotationRef
            from ome_types.model import Ellipse as OmeEllipse
            from ome_types.model import Line as OmeLine
            from ome_types.model import Map
            from ome_types.model import MapAnnotation
            from ome_types.model import Point as OmePoint
            from ome_types.model import Polygon as OmePolygon
            from ome_types.model import Polyline as OmePolyline
            from ome_types.model import Rectangle as OmeRectangle
            from ome_types.model.map import M
            from ome_types.model.shape import FillRule
        except ImportError:
            raise RuntimeError(f"{type(self).__name__}.to_ome_xml requires 'ome-types' python module and python>=3.7")

        from paquo.java import EllipseROI
        from paquo.java import GeometryROI
        from paquo.java import LineROI
        from paquo.java import PointsROI
        from paquo.java import PolygonROI
        from paquo.java import PolylineROI
        from paquo.java import RectangleROI

        ome = OME()

        for ao in self.annotations:

            class_name: Optional[str]
            if ao.path_class:
                class_name = ao.path_class.name
            else:
                class_name = None

            # --- create the map_annotation

            _m = {
                f"{prefix}:object_type": {
                    "PathAnnotationObject": 'annotation',
                    "PathDetectionObject": 'detection',
                    "PathTileObject": 'tile',
                    "PathCellObject": 'cell',
                    "TMACoreObject": 'tma_core',
                    "PathRootObject": 'root',
                }.get(type(ao.java_object).__name__.rpartition(".")[2], "unknown")
            }
            if class_name:
                _m[f"{prefix}:path_class"] = class_name
            if ao.name:
                _m[f"{prefix}:name"] = ao.name
            for k, v in ao.measurements.items():
                _m[f"{prefix}:measurement:{k}"] = v
            map_annotation = MapAnnotation(value=Map(m=[
                M(k=_key, value=str(_value))
                for _key, _value in _m.items()
            ]))

            # --- prepare common kwargs for ome Shape

            if ao.path_class and ao.path_class.color:
                # https://www.openmicroscopy.org/Schemas/Documentation/Generated/OME-2016-06/ome_xsd.html#Color
                r, g, b, a = ao.path_class.color.to_rgba()
                stroke_color, = struct.unpack(">i", bytes([r, g, b, a]))
                if fill_alpha <= 0:
                    fill_color = None
                else:
                    fill_alpha = min(max(0.0, fill_alpha), 1.0)
                    fill_color, = struct.unpack(">i", bytes([r, g, b, int(fill_alpha*a)]))
            else:
                stroke_color = None
                fill_color = None
            # https://www.openmicroscopy.org/Schemas/Documentation/Generated/OME-2016-06/ome_xsd.html#Shape_FillRule
            fill_rule = FillRule.NON_ZERO

            qp_roi = ao.java_object.getROI()
            the_c = int(qp_roi.getC())
            the_t = int(qp_roi.getT())
            the_z = int(qp_roi.getZ())

            shape_kwargs = dict(
                # id=...,
                # annotation_ref=...,
                fill_color=fill_color,
                fill_rule=fill_rule,
                # font_family=None,
                # font_size=None,
                # font_size_unit=UnitsLength("pt"),
                # font_style=None,
                locked=ao.locked,
                stroke_color=stroke_color,
                stroke_dash_array=None,
                stroke_width=2,  # 2px is the QuPath default gui setting
                # stroke_width_unit=UnitsLength("pixel"),
                text=class_name,  # again class instead of ao.description for a nicer UX in omero.iviewer...
                the_c=the_c if the_c >= 0 else None,
                the_t=the_t,
                the_z=the_z,
                transform=None,
            )

            # --- create the roi

            roi = ROI(name=class_name)
            roi.annotation_ref.append(AnnotationRef(id=map_annotation.id))

            # --- add the correct shape dependent on roi types

            ome_shape: Any
            if isinstance(qp_roi, (PolygonROI, GeometryROI)):
                ome_shape = OmePolygon(
                    points=" ".join(f"{p.getX():f},{p.getY():f}" for p in qp_roi.getAllPoints()),
                    **shape_kwargs,
                )
            elif isinstance(qp_roi, EllipseROI):
                # https://github.com/qupath/qupath/blob/e84467e86751e5aa542ab68a4915b70ecbf2f6fc/qupath-core/src/main/java/qupath/lib/roi/EllipseROI.java#L60-L63
                ome_shape = OmeEllipse(
                    radius_x=float(qp_roi.getBoundsWidth() * 0.5),
                    radius_y=float(qp_roi.getBoundsHeight() * 0.5),
                    x=float(qp_roi.getCentroidX()),
                    y=float(qp_roi.getCentroidY()),
                    **shape_kwargs,
                )
            elif isinstance(qp_roi, RectangleROI):
                ome_shape = OmeRectangle(
                    height=float(qp_roi.getBoundsHeight()),
                    width=float(qp_roi.getBoundsWidth()),
                    x=float(qp_roi.getBoundsX()),
                    y=float(qp_roi.getBoundsY()),
                    **shape_kwargs,
                )
            elif isinstance(qp_roi, LineROI):
                ome_shape = OmeLine(
                    x1=float(qp_roi.getX1()),
                    x2=float(qp_roi.getX2()),
                    y1=float(qp_roi.getY1()),
                    y2=float(qp_roi.getY2()),
                    marker_end=None,
                    marker_start=None,
                    **shape_kwargs,
                )
            elif isinstance(qp_roi, PolylineROI):
                ome_shape = OmePolyline(
                    points=" ".join(f"{p.getX():f},{p.getY():f}" for p in qp_roi.getAllPoints()),
                    marker_end=None,
                    marker_start=None,
                    **shape_kwargs,
                )
            elif isinstance(qp_roi, PointsROI):
                # we have to create individual points in ome
                ome_shape = [
                    OmePoint(x=float(p.getX()), y=float(p.getY()), **shape_kwargs)
                    for p in qp_roi.getAllPoints()
                ]
            else:
                raise NotImplementedError(f"todo {type(qp_roi).__name__}")

            if isinstance(ome_shape, list):
                roi.union.extend(ome_shape)
            else:
                roi.union.append(ome_shape)

            # --- add the annotation to the ome structure
            ome.rois.append(roi)
            ome.structured_annotations.append(map_annotation)

        return to_xml(ome)

    def __repr__(self):
        return f"Hierarchy(image={self._image_name}, annotations={len(self._annotations)}, detections={len(self._detections)})"

    def _repr_html_(self):
        from paquo._repr import br
        from paquo._repr import div
        from paquo._repr import h4
        from paquo._repr import p
        from paquo._repr import span

        return div(
            h4(text=f"Hierarchy: {self._image_name}", style={"margin-top": "0"}),
            p(
                span(text="annotations: ", style={"font-weight": "bold"}),
                span(text=f"{len(self._annotations)}"),
                br(),
                span(text="detections: ", style={"font-weight": "bold"}),
                span(text=f"{len(self._detections)}"),
                style={"margin": "0.5em"},
            ),
        )
