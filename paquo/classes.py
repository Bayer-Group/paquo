from paquo.java import PathClass, PathClassFactory, ColorTools


class QuPathPathClass:

    def __init__(self, path_class=None):
        if not isinstance(path_class, PathClass):
            raise ValueError("use PathClass.create() to instantiate")
        self._path_class = path_class

    @classmethod
    def create(cls, name, color=None, parent=None, exist_ok=True):
        if name is None and parent is not None:
            raise ValueError("cannot create derived PathClass with name=None")

        _parent_class = None
        if parent is not None:
            if not isinstance(parent, PathClass):
                raise TypeError("parent must be a PathClass")
            _parent_class = parent._path_class

        if not exist_ok:
            # FIXME: derivedClassToString is not public...
            path_class_str = PathClass.derivedClassToString(_parent_class, name)
            if bool(PathClassFactory.classExists(path_class_str)):
                raise Exception("path_class already created")

        _color = ColorTools.makeRGB(int(color[0]), int(color[1]), int(color[2]))
        path_class = PathClassFactory.getDerivedPathClass(_parent_class, name, _color)
        return cls(path_class)

    @property
    def name(self):
        return str(self._path_class.getName())

    @property
    def id(self):
        return str(self._path_class.toString())

    def __eq__(self, other):
        return self._path_class.compareTo(other._path_class)

    @property
    def parent(self):
        path_class = self._path_class.getParentClass()
        if path_class is None:
            return None
        return PathClass(path_class)

    @property
    def origin(self):
        origin_class = self
        while origin_class.parent is not None:
            origin_class = origin_class.parent
        return origin_class

    def is_derived_from(self, parent_class):
        return self._path_class.isDerivedFrom(parent_class._path_class)

    def is_ancestor_of(self, child_class):
        return self._path_class.isAncestorOf(child_class._path_class)

    @property
    def color(self):
        argb = self._path_class.getColor()
        r = int(ColorTools.red(argb))
        g = int(ColorTools.green(argb))
        b = int(ColorTools.blue(argb))
        return r, g, b

    @color.setter
    def color(self, rgb):
        r, g, b = map(int, rgb)
        a = int(255 * self.alpha)
        argb = ColorTools.makeRGBA(r, g, b, a)
        self._path_class.setColor(argb)

    @property
    def alpha(self):
        argb = self._path_class.getColor()
        a = int(ColorTools.alpha(argb))
        return a / 255.0

    @alpha.setter
    def alpha(self, alpha):
        r, g, b = self.color
        a = int(255 * alpha)
        argb = ColorTools.makeRGBA(r, g, b, a)
        self._path_class.setColor(argb)

    @property
    def is_valid(self):
        return bool(self._path_class.isValid())

    @property
    def is_derived_class(self):
        return bool(self._path_class.isDerivedClass())

    def __repr__(self):
        return f"<PathClass '{self.id}'>"
