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
    wkb_bytes = shapely_wkb_dumps(geometry)
    jts_geomerty = WKBReader().read(wkb_bytes)
    return GeometryTools.geometryToROI(jts_geomerty, image_plane)


def _qupath_roi_to_shapely_geometry(roi) -> BaseGeometry:
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
        raise NotImplementedError("todo")

    def to_geojson(self):
        gson = GsonTools.getInstance()
        geojson = gson.toJson(self.java_object)
        return json.loads(str(geojson))

    @property
    def path_class(self):
        return QuPathPathClass(self.java_object.getPathClass())

    @property
    def path_class_probability(self):
        return float(self.java_object.getClassProbability())

    def update_path_class(self, pc: QuPathPathClass, probability: float = math.nan):
        self.java_object.setPathClass(pc.java_object, probability)

    @property
    def locked(self):
        return bool(self.java_object.isLocked())

    @locked.setter
    def locked(self, value):
        self.java_object.setLocked(value)

    @property
    def is_editable(self):
        return bool(self.java_object.isEditable())

    @property
    def level(self):
        return int(self.java_object.getLevel())

    @property
    def description(self):
        return str(self.java_object.getDescription())

    @description.setter
    def description(self, value: Union[str, None]):
        self.java_object.setDescription(value)

    @property
    def name(self):
        return str(self.java_object.getName())

    @name.setter
    def name(self, name):
        self.java_object.setName(String(name))

    @property
    def color(self):
        argb = self.java_object.getColor()
        return QuPathColor.from_java_rgba(argb)

    @color.setter
    def color(self, rgb: ColorType):
        argb = QuPathColor.from_any(rgb).to_java_rgba()
        self.java_object.setColor(argb)

    @property
    def parent(self):
        parent = self.java_object.getParent()
        if not parent:
            return None
        return QuPathPathAnnotationObject(parent)

    @property
    def roi(self):
        roi = self.java_object.getROI()
        return _qupath_roi_to_shapely_geometry(roi)

    def update_roi(self, geometry: BaseGeometry):
        roi = _shapely_geometry_to_qupath_roi(geometry)
        self.java_object.setROI(roi)

    @property
    def measurements(self):
        raise NotImplementedError("todo: provide via a dict proxy")
