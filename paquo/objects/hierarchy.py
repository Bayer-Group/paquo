import json
from typing import List

from paquo.java import JString, JGsonTools, JColorTools, JArrayList, JPoint2, JROIs, JPathObjects
from paquo.objects.classes import PathClass


class PathObjectHierarchy:

    def __init__(self, hierarchy):
        self._hierarchy = hierarchy

    def __len__(self):
        return int(self._hierarchy.nObjects())

    @property
    def is_empty(self):
        return bool(self._hierarchy.isEmpty())

    @property
    def root(self):
        root = self._hierarchy.getRootObject()
        if root is None:
            return None
        return PathObject(root)

    def to_geojson(self):
        gson = JGsonTools.getInstance()
        geojson = gson.toJson(self._hierarchy.getAnnotationObjects())
        return json.loads(str(geojson))

    def from_geojson(self, geojson):
        # fixme: implement nicely...
        """
        def annotations = []
        for (annotation in tumorAnnotations) {
            def name = annotation['name']
            def vertices = annotation['vertices']
            def points = vertices.collect {new Point2(it[0], it[1])}
            def polygon = new PolygonROI(points)
            def pathAnnotation = new PathAnnotationObject(polygon)
            pathAnnotation.setName(name)
            annotations << pathAnnotation
        }

        // Add to current hierarchy
        QPEx.addObjects(annotations)

        [{
            'type': 'Feature',
            'id': 'PathAnnotationObject',
            'geometry': {
                'type': 'Polygon',
                'coordinates': [[
                    [1058, 1379],
                    [1054, 1380],
                    [1058, 1379]
                ]]
            },
            'properties': {
                'classification': {
                    'name': 'Tumor',
                    'colorRGB': -3670016
                },
                'isLocked': False,
                'measurements': []
            }
        }]
        """
        assert isinstance(geojson, list)
        changed = False
        for annotation in geojson:
            ao = PathAnnotationObject.from_geojson(annotation)
            changed |= self._hierarchy.insertPathObject(ao._path_object, True)
        return changed


class PathObject:

    def __init__(self, path_object):
        self._path_object = path_object

    @property
    def parent(self):
        po = self._path_object.getParent()
        if not po:
            return None
        return PathObject(self._path_object.getParent())

    @property
    def locked(self):
        return bool(self._path_object.isLocked())

    @locked.setter
    def locked(self, value):
        self._path_object.setLocked(value)

    @property
    def level(self):
        return int(self._path_object.getLevel())

    @property
    def is_root(self):
        return bool(self._path_object.isRootObject())

    @property
    def name(self):
        return str(self._path_object.getName())

    @name.setter
    def name(self, name):
        self._path_object.setName(JString(name))

    @property
    def color(self):
        argb = self._path_object.getColor()
        r = int(JColorTools.red(argb))
        g = int(JColorTools.green(argb))
        b = int(JColorTools.blue(argb))
        return r, g, b

    @color.setter
    def color(self, rgb):
        r, g, b = map(int, rgb)
        a = int(255 * self.alpha)
        argb = JColorTools.makeRGB(r, g, b, a)
        self._path_object.setColor(argb)

    @property
    def alpha(self):
        argb = self._path_object.getColor()
        a = int(JColorTools.alpha(argb))
        return a / 255.0

    @alpha.setter
    def alpha(self, alpha):
        r, g, b = self.color
        a = int(255 * alpha)
        argb = JColorTools.makeRGBA(r, g, b, a)
        self._path_object.setColor(argb)

    @property
    def path_class(self):
        return PathClass(self._path_object.getPathClass())

    @path_class.setter
    def path_class(self, pc: PathClass):
        self._path_object.setPathClass(pc._path_class)

    @property
    def path_class_probability(self):
        return float(self._path_object.getClassProbability())

    # ... todo: needs more pythonic interface
    # def set_path_class(self, pc: PathClass, probability: float = float("nan")):
    #     self._path_object.setPathClass(pc._path_class, probability)


class PathAnnotationObject(PathObject):

    @classmethod
    def from_vertices(cls, vertices: List[List[List[float]]], path_class: PathClass = None):
        # fixme: quick and dirty poc
        assert len(vertices) == 1
        points = JArrayList()
        for x, y in vertices[0]:
            points.add(JPoint2(x, y))
        roi = JROIs.createPolygonROI(points, None)
        ao = JPathObjects.createAnnotationObject(roi, path_class._path_class, None)
        return cls(ao)

    @classmethod
    def from_geojson(cls, geojson):
        assert geojson['geometry']['type'] == 'Polygon'
        path_class = PathClass.create(
            name=geojson['properties']['classification']['name'],
            color=(0, 255, 0)
        )
        polygon = geojson['geometry']['coordinates']
        return cls.from_vertices(polygon, path_class)
