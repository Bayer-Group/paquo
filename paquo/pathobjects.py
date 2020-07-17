from __future__ import annotations

import json
import math
from typing import Optional, Union

from shapely.geometry.base import BaseGeometry
from shapely.wkb import loads as shapely_wkb_loads, dumps as shapely_wkb_dumps

from paquo._base import QuPathBase
from paquo.classes import QuPathPathClass
from paquo.colors import QuPathColor, ColorType
from paquo.java import String, PathObjects, ROI, WKBWriter, WKBReader, GeometryTools, PathAnnotationObject, GsonTools


def _shapely_geometry_to_qupath_roi(geometry: BaseGeometry, image_plane=None) -> ROI:
    """convert a shapely geometry into a qupath ROI

    uses well known binary WKB as intermediate representation

    todo: expose image plane settings and provide pythonic interface to it
    """
    wkb_bytes = shapely_wkb_dumps(geometry)
    jts_geomerty = WKBReader().read(wkb_bytes)
    return GeometryTools.geometryToROI(jts_geomerty, image_plane)


def _qupath_roi_to_shapely_geometry(roi) -> BaseGeometry:
    """convert a qupath ROI to a shapely geometry

    uses well known binary WKB as intermediate representation

    note: this loses the image plane information
    """
    jts_geometry = GeometryTools.roiToGeometry(roi)
    wkb_bytearray = WKBWriter(2).write(jts_geometry)
    return shapely_wkb_loads(bytes(wkb_bytearray))


class QuPathPathAnnotationObject(QuPathBase[PathAnnotationObject]):

    @classmethod
    def from_shapely(cls,
                     roi: BaseGeometry,
                     path_class: Optional[QuPathPathClass] = None,
                     measurements: Optional[dict] = None,
                     *,
                     path_class_probability: float = math.nan) -> QuPathPathAnnotationObject:
        """create a QuPathPathAnnotationObject from a shapely shape

        Parameters
        ----------
        roi:
            a shapely shape as the region of interest of the annotation
        path_class:
            a paquo QuPathPathClass to mark the annotation type
        measurements:
            todo --- not yet implemented (holds static measurements)
        path_class_probability:
            keyword only argument defining the probability of the class
            (default NaN)

        """
        qupath_roi = _shapely_geometry_to_qupath_roi(roi)
        qupath_path_class = path_class.java_object if path_class is not None else None
        ao = PathObjects.createAnnotationObject(
            qupath_roi, qupath_path_class, measurements
        )
        if measurements is not None:
            raise NotImplementedError("wrap and cast to paquo Measurements")
        if not math.isnan(path_class_probability):
            ao.setPathClass(ao.getPathClass(), path_class_probability)
        return cls(ao)

    @classmethod
    def from_geojson(cls, geojson) -> QuPathPathAnnotationObject:
        """create a new QuPathPathAnnotationObject from geojson"""
        gson = GsonTools.getInstance()
        ao = gson.fromJson(String(json.dumps(geojson)), PathAnnotationObject)
        return cls(ao)

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
        """the annotation path class probablity"""
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
    def description(self) -> str:
        """an optional description for the annotation"""
        return str(self.java_object.getDescription())

    @description.setter
    def description(self, value: Union[str, None]):
        self.java_object.setDescription(value)

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

        todo: ? is this seperate from the class color ?
        """
        argb = self.java_object.getColor()
        return QuPathColor.from_java_rgba(argb)

    @color.setter
    def color(self, rgb: ColorType) -> None:
        argb = QuPathColor.from_any(rgb).to_java_rgba()
        self.java_object.setColor(argb)

    @property
    def parent(self) -> Optional[QuPathPathAnnotationObject]:
        """the annotation object's parent annotation object"""
        parent = self.java_object.getParent()
        if not parent:
            return None
        return QuPathPathAnnotationObject(parent)

    @property
    def roi(self) -> BaseGeometry:
        """the roi as a shapely shape"""
        roi = self.java_object.getROI()
        return _qupath_roi_to_shapely_geometry(roi)

    def update_roi(self, geometry: BaseGeometry) -> None:
        """update the roi of the annotation"""
        roi = _shapely_geometry_to_qupath_roi(geometry)
        self.java_object.setROI(roi)

    @property
    def measurements(self):
        raise NotImplementedError("todo: provide via a dict proxy")
