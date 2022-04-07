import json
import math
from collections.abc import MutableMapping
from typing import Callable
from typing import Iterator
from typing import Optional
from typing import Type
from typing import TypeVar
from typing import Union

from shapely.geometry import shape
from shapely.geometry.base import BaseGeometry
from shapely.wkb import dumps as shapely_wkb_dumps
from shapely.wkb import loads as shapely_wkb_loads

from paquo._utils import cached_property
from paquo.classes import QuPathPathClass
from paquo.java import ROI
from paquo.java import GeometryTools
from paquo.java import GsonTools
from paquo.java import PathAnnotationObject
from paquo.java import PathDetectionObject
from paquo.java import PathObjects
from paquo.java import PathROIObject
from paquo.java import PathTileObject
from paquo.java import String
from paquo.java import WKBReader
from paquo.java import WKBWriter

__all__ = [
    "fix_geojson_geometry",
    "BaseGeometry",
    "PathROIObjectType",
    "QuPathPathAnnotationObject",
    "QuPathPathDetectionObject",
    "QuPathPathTileObject",
]


def _shapely_geometry_to_qupath_roi(geometry: BaseGeometry, image_plane=None) -> ROI:
    """convert a shapely geometry into a qupath ROI

    uses well known binary WKB as intermediate representation

    todo: expose image plane settings and provide pythonic interface to it
    """
    wkb_bytes = shapely_wkb_dumps(geometry)
    jts_geometry = WKBReader().read(wkb_bytes)
    return GeometryTools.geometryToROI(jts_geometry, image_plane)


def _qupath_roi_to_shapely_geometry(roi) -> BaseGeometry:
    """convert a qupath ROI to a shapely geometry

    uses well known binary WKB as intermediate representation

    note: this loses the image plane information
    """
    jts_geometry = GeometryTools.roiToGeometry(roi)
    wkb_bytearray = WKBWriter(2).write(jts_geometry)
    return shapely_wkb_loads(bytes(wkb_bytearray))


def fix_geojson_geometry(geometry: dict) -> dict:
    """try to fix a provided geojson geometry via buffering"""
    s = shape(geometry)
    if not s.is_valid:
        # attempt to fix
        s = s.buffer(0, 1)
        if not s.is_valid:
            s = s.buffer(0, 1)
            if not s.is_valid:
                raise ValueError("invalid geometry")
    return s.__geo_interface__  # type: ignore


class _MeasurementList(MutableMapping):

    def __init__(self, measurement_list):
        self._measurement_list = measurement_list

    def __setitem__(self, k: str, v: float) -> None:
        self._measurement_list.putMeasurement(k, v)

    def __delitem__(self, v: str) -> None:
        if v not in self:
            raise KeyError(v)
        self._measurement_list.removeMeasurements(v)

    def __getitem__(self, k: Union[str, int]) -> float:
        if not isinstance(k, (int, str)):
            raise KeyError(f"unsupported key of type {type(k)}")
        return float(self._measurement_list.getMeasurementValue(k))

    def __contains__(self, item: object) -> bool:
        if not isinstance(item, str):
            return False
        return bool(self._measurement_list.containsNamedMeasurement(item))

    def __len__(self) -> int:
        return int(self._measurement_list.size())

    def __iter__(self) -> Iterator[str]:
        return iter(map(str, self._measurement_list.getMeasurementNames()))

    def clear(self) -> None:
        self._measurement_list.clear()

    def __repr__(self):
        return f"Measurements({repr(dict(self))})"

    def __str__(self):
        return str(dict(self))

    def to_records(self):
        return [{'name': name, 'value': value} for name, value in self.items()]


# noinspection PyTypeChecker
PathROIObjectType = TypeVar('PathROIObjectType', bound='_PathROIObject')


class _PathROIObject:
    """internal base class for PathObjects"""

    # must be provided in subclass
    java_class: Type[PathROIObject]
    java_class_factory: Callable[..., PathROIObject]

    def __init__(
        self,
        java_object: PathROIObject,
        *,
        update_callback: Optional[Callable[[PathROIObjectType], None]] = None
    ) -> None:
        """instantiate using classmethods: `from_shapely`, `from_geojson`"""
        self.java_object = java_object
        self._update_callback = update_callback

    @classmethod
    def from_shapely(cls: Type[PathROIObjectType],
                     roi: BaseGeometry,
                     path_class: Optional[QuPathPathClass] = None,
                     measurements: Optional[dict] = None,
                     *,
                     path_class_probability: float = math.nan) -> PathROIObjectType:
        """create a Path Object from a shapely shape

        Parameters
        ----------
        roi:
            a shapely shape as the region of interest of the annotation
        path_class:
            a paquo QuPathPathClass to mark the annotation type
        measurements:
            dict holding static measurements for annotation object
        path_class_probability:
            keyword only argument defining the probability of the class
            (default NaN)

        """
        if not isinstance(roi, BaseGeometry):
            raise TypeError("roi needs to be an instance of shapely.geometry.base.BaseGeometry")
        qupath_roi = _shapely_geometry_to_qupath_roi(roi)
        qupath_path_class = path_class.java_object if path_class is not None else None
        # fixme: should create measurements here and pass instead of None
        java_obj = cls.java_class_factory(qupath_roi, qupath_path_class, None)
        if not math.isnan(path_class_probability):
            java_obj.setPathClass(java_obj.getPathClass(), path_class_probability)
        obj = cls(java_obj)
        if measurements is not None:
            obj.measurements.update(measurements)
        return obj

    @classmethod
    def from_geojson(cls: Type[PathROIObjectType], geojson) -> PathROIObjectType:
        """create a new Path Object from geojson"""
        gson = GsonTools.getInstance()
        java_obj = gson.fromJson(String(json.dumps(geojson)), cls.java_class)
        return cls(java_obj)

    def to_geojson(self) -> dict:
        """convert the annotation object to geojson"""
        gson = GsonTools.getInstance()
        geojson = gson.toJson(self.java_object)
        return dict(json.loads(str(geojson)))

    @property
    def path_class(self) -> Optional[QuPathPathClass]:
        """the annotation path class"""
        pc = self.java_object.getPathClass()
        if not pc:
            return None
        return QuPathPathClass.from_java(pc)

    @property
    def path_class_probability(self) -> float:
        """the annotation path class probability"""
        return float(self.java_object.getClassProbability())

    def update_path_class(self: PathROIObjectType, pc: Optional[QuPathPathClass], probability: float = math.nan) -> None:
        """updating the class or probability has to be done via this method"""
        if not (pc is None or isinstance(pc, QuPathPathClass)):
            raise TypeError("requires QuPathPathClass")
        else:
            pc = pc if pc is None else pc.java_object
        self.java_object.setPathClass(pc, probability)
        if self._update_callback:
            self._update_callback(self)

    @property
    def locked(self) -> bool:
        """lock state of the annotation"""
        return bool(self.java_object.isLocked())

    @locked.setter
    def locked(self: PathROIObjectType, value: bool) -> None:
        self.java_object.setLocked(value)
        if self._update_callback:
            self._update_callback(self)

    @property
    def is_editable(self) -> bool:
        """can the annotation be edited in the qupath UI"""
        return bool(self.java_object.isEditable())

    @property
    def level(self) -> int:
        """the annotation's level"""
        return int(self.java_object.getLevel())

    @property
    def name(self) -> Optional[str]:
        """an optional name for the annotation"""
        name = self.java_object.getName()
        if name is None:
            return None
        return str(name)

    @name.setter
    def name(self: PathROIObjectType, name: Union[str, None]) -> None:
        if name is not None:
            name = String(name)
        self.java_object.setName(name)
        if self._update_callback:
            self._update_callback(self)

    @property
    def parent(self: PathROIObjectType) -> Optional[PathROIObjectType]:
        """the annotation object's parent annotation object"""
        parent = self.java_object.getParent()
        if not parent:
            return None
        # fixme: Is this true? Or do we need to dynamically cast to the right subclass
        return self.__class__(parent)

    @property
    def roi(self) -> BaseGeometry:
        """the roi as a shapely shape"""
        roi = self.java_object.getROI()
        return _qupath_roi_to_shapely_geometry(roi)

    def update_roi(self: PathROIObjectType, geometry: BaseGeometry) -> None:
        """update the roi of the annotation"""
        roi = _shapely_geometry_to_qupath_roi(geometry)
        self.java_object.setROI(roi)
        if self._update_callback:
            self._update_callback(self)

    @cached_property
    def measurements(self):
        return _MeasurementList(self.java_object.getMeasurementList())

    def __repr__(self):
        name = self.name
        path_class = self.path_class
        roi = self.roi
        out = []
        if name:
            out.append(f'name="{name}"')
        if path_class:
            out.append(f'class="{path_class.name}"')
        if roi:
            out.append(f'roi={roi.type}')
        return f"{type(self).__name__}({' '.join(out)})"

    def _repr_html_(self):
        from paquo._repr import br
        from paquo._repr import div
        from paquo._repr import h4
        from paquo._repr import p
        from paquo._repr import rawhtml
        from paquo._repr import repr_svg
        from paquo._repr import span

        obj_class_name = self.__class__.__name__
        if obj_class_name.startswith('QuPath'):
            obj_class_name = obj_class_name[6:]

        name = self.name or "N/A"
        path_class = self.path_class
        path_class_name = path_class.name if path_class else "N/A"
        roi = self.roi
        if hasattr(roi, '_repr_svg_'):
            roi_tag = span(rawhtml(repr_svg(roi)), style={"vertical-align": "text-top"})
        else:
            roi_tag = span(text=roi.wkt)  # pragma: no cover

        return div(
            h4(text=f"{obj_class_name}:", style={"margin-top": "0"}),
            p(
                span(text="name: ", style={"font-weight": "bold"}),
                span(text=name),
                br(),
                span(text="path_class: ", style={"font-weight": "bold"}),
                span(text=path_class_name),
                br(),
                span(text="roi_type: ", style={"font-weight": "bold"}),
                span(text=roi.type),
                br(),
                span(text="roi: ", style={"font-weight": "bold"}),
                roi_tag,
                style={"margin": "0.5em"},
            ),
        )


class QuPathPathAnnotationObject(_PathROIObject):

    java_class = PathAnnotationObject
    java_class_factory = PathObjects.createAnnotationObject

    @property
    def description(self) -> Optional[str]:
        """an optional description for the annotation"""
        desc = self.java_object.getDescription()
        return str(desc) if desc is not None else None

    @description.setter
    def description(self, value: str):
        if not isinstance(value, str):
            raise TypeError("requires a str")
        self.java_object.setDescription(String(value))


class QuPathPathDetectionObject(_PathROIObject):

    java_class = PathDetectionObject
    java_class_factory = PathObjects.createDetectionObject


class QuPathPathTileObject(QuPathPathDetectionObject):

    java_class = PathTileObject
    java_class_factory = PathObjects.createTileObject
