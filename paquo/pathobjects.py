from __future__ import annotations

from collections.abc import MutableMapping
import json
import math
from functools import cached_property
from typing import Optional, Union, Iterator, TypeVar

from shapely.geometry.base import BaseGeometry
from shapely.wkb import loads as shapely_wkb_loads, dumps as shapely_wkb_dumps

from paquo._base import QuPathBase
from paquo.classes import QuPathPathClass
from paquo.colors import QuPathColor, ColorType
from paquo.java import String, PathObjects, ROI, WKBWriter, WKBReader, GeometryTools, PathAnnotationObject, GsonTools, \
    PathROIObject, PathDetectionObject


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

    def __contains__(self, item: str):
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
        return f"<Measurements({repr(dict(self))})>"


PathObjectType = TypeVar('PathObjectType', bound=PathROIObject)


class _PathROIObject(QuPathBase[PathObjectType]):
    """internal base class for PathObjects"""

    java_class = None
    java_class_factory = None

    @classmethod
    def from_shapely(cls,
                     roi: BaseGeometry,
                     path_class: Optional[QuPathPathClass] = None,
                     measurements: Optional[dict] = None,
                     *,
                     path_class_probability: float = math.nan) -> _PathROIObject:
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
        qupath_roi = _shapely_geometry_to_qupath_roi(roi)
        qupath_path_class = path_class.java_object if path_class is not None else None
        # fixme: should create measurements here and pass instead of None
        java_obj = cls.java_class_factory(
            qupath_roi, qupath_path_class, None
        )
        if not math.isnan(path_class_probability):
            java_obj.setPathClass(java_obj.getPathClass(), path_class_probability)
        obj = cls(java_obj)
        if measurements is not None:
            obj.measurements.update(measurements)
        return obj

    @classmethod
    def from_geojson(cls, geojson) -> PathObjectType:
        """create a new Path Object from geojson"""
        gson = GsonTools.getInstance()
        java_obj = gson.fromJson(String(json.dumps(geojson)), cls.java_class)
        return cls(java_obj)

    def to_geojson(self) -> dict:
        """convert the annotation object to geojson"""
        gson = GsonTools.getInstance()
        geojson = gson.toJson(self.java_object)
        return json.loads(str(geojson))

    @property
    def path_class(self) -> Optional[QuPathPathClass]:
        """the annotation path class"""
        pc = self.java_object.getPathClass()
        if not pc:
            return None
        return QuPathPathClass(pc)

    @property
    def path_class_probability(self) -> float:
        """the annotation path class probability"""
        return float(self.java_object.getClassProbability())

    def update_path_class(self, pc: QuPathPathClass, probability: float = math.nan) -> None:
        """updating the class or probability has to be done via this method"""
        self.java_object.setPathClass(pc.java_object, probability)

    @property
    def locked(self) -> bool:
        """lock state of the annotation"""
        return bool(self.java_object.isLocked())

    @locked.setter
    def locked(self, value: bool) -> None:
        self.java_object.setLocked(value)

    @property
    def is_editable(self) -> bool:
        """can the annotation be edited in the qupath UI"""
        return bool(self.java_object.isEditable())

    @property
    def level(self) -> int:
        """the annotation's level"""
        return int(self.java_object.getLevel())

    @property
    def name(self) -> str:
        """an optional name for the annotation"""
        return str(self.java_object.getName())

    @name.setter
    def name(self, name: str):
        self.java_object.setName(String(name))

    @property
    def color(self) -> QuPathColor:
        """the path annotation object color

        todo: ? is this separate from the class color ?
        """
        argb = self.java_object.getColor()
        return QuPathColor.from_java_rgba(argb)

    @color.setter
    def color(self, rgb: ColorType) -> None:
        argb = QuPathColor.from_any(rgb).to_java_rgba()
        self.java_object.setColor(argb)

    @property
    def parent(self) -> Optional[_PathROIObject]:
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

    def update_roi(self, geometry: BaseGeometry) -> None:
        """update the roi of the annotation"""
        roi = _shapely_geometry_to_qupath_roi(geometry)
        self.java_object.setROI(roi)

    @cached_property
    def measurements(self):
        return _MeasurementList(self.java_object.getMeasurementList())


class QuPathPathAnnotationObject(_PathROIObject[PathAnnotationObject]):

    java_class = PathAnnotationObject
    java_class_factory = PathObjects.createAnnotationObject

    @property
    def description(self) -> str:
        """an optional description for the annotation"""
        return str(self.java_object.getDescription())

    @description.setter
    def description(self, value: Union[str, None]):
        self.java_object.setDescription(value)


class QuPathPathDetectionObject(_PathROIObject[PathDetectionObject]):

    java_class = PathDetectionObject
    java_class_factory = PathObjects.createDetectionObject
