import json

from paquo.qupath.jpype_backend import jvm_running, java_import

from paquo.objects.classes import PathClass

with jvm_running():
    _String = java_import('java.lang.String')
    _ColorTools = java_import('qupath.lib.common.ColorTools')
    _GsonTools = java_import('qupath.lib.io.GsonTools')


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
        return PathObject(self._hierarchy.getRootObject())

    def to_geojson(self):
        gson = _GsonTools.getInstance()
        geojson = gson.toJson(self._hierarchy.getAnnotationObjects())
        return json.loads(str(geojson))


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
        self._path_object.setName(_String(name))

    @property
    def color(self):
        argb = self._path_object.getColor()
        r = int(_ColorTools.red(argb))
        g = int(_ColorTools.green(argb))
        b = int(_ColorTools.blue(argb))
        return r, g, b

    @color.setter
    def color(self, rgb):
        r, g, b = map(int, rgb)
        a = int(255 * self.alpha)
        argb = _ColorTools.makeRGB(r, g, b, a)
        self._path_object.setColor(argb)

    @property
    def alpha(self):
        argb = self._path_object.getColor()
        a = int(_ColorTools.alpha(argb))
        return a / 255.0

    @alpha.setter
    def alpha(self, alpha):
        r, g, b = self.color
        a = int(255 * alpha)
        argb = _ColorTools.makeRGBA(r, g, b, a)
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
