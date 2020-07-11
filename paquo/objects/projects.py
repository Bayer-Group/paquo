import pathlib
from collections.abc import MutableSet, MutableMapping
from typing import Union, Iterator

from paquo.qupath.jpype_backend import java_import, jvm_running

# import java classes
with jvm_running():
    _BufferedImage = java_import('java.awt.image.BufferedImage')
    _DefaultProject = java_import('qupath.lib.projects.DefaultProject')
    # _Project = java_import('qupath.lib.projects.Project')
    _Projects = java_import('qupath.lib.projects.Projects')
    _ProjectIO = java_import('qupath.lib.projects.ProjectIO')
    _File = java_import('java.io.File')
    _String = java_import('java.lang.String')
    _DefaultProjectImageEntry = java_import('qupath.lib.projects.DefaultProject.DefaultProjectImageEntry')
    _ImageServerProvider = java_import('qupath.lib.images.servers.ImageServerProvider')
    _ServerTools = java_import('qupath.lib.images.servers.ServerTools')
    _ColorTools = java_import('qupath.lib.common.ColorTools')
    _PathClass = java_import('qupath.lib.objects.classes.PathClass')
    _PathClassFactory = java_import('qupath.lib.objects.classes.PathClassFactory')


class _QuPathImageEntryMetadata(MutableMapping):

    def __init__(self, entry):
        self._entry = entry

    def __setitem__(self, k: str, v: str) -> None:
        self._entry.putMetadataValue(_String(k), _String(v))

    def __delitem__(self, k: str) -> None:
        self._entry.removeMetadataValue(_String(k))

    def __getitem__(self, k: str) -> str:
        v = self._entry.getMetadataValue(_String(k))
        return str(v)

    def __len__(self) -> int:
        # ... not really nice
        return sum(1 for _ in self._entry.getMetadataKeys())

    def __iter__(self) -> Iterator[str]:
        return iter(map(str, self._entry.getMetadataKeys()))

    def __contains__(self, item):
        return bool(self._entry.containsMetadata(_String(item)))

    def clear(self) -> None:
        self._entry.clearMetadata()


class QuPathProjectImageEntry:

    def __init__(self, entry):
        if not isinstance(entry, _DefaultProjectImageEntry):
            raise TypeError("don't instantiate QuPathProjectImageEntry yourself")
        self._entry = entry
        self._metadata = _QuPathImageEntryMetadata(entry)

    @property
    def id(self):
        return str(self._entry.getID())

    @property
    def image_name(self):
        return str(self._entry.getImageName())

    @image_name.setter
    def image_name(self, name):
        self._entry.setImageName(_String(name))

    @property
    def image_name_original(self):
        org_name = self._entry.getOriginalImageName()
        return str(org_name) if org_name else None

    @property
    def entry_path(self):
        return pathlib.Path(self._entry.getEntryPath().toString())

    @property
    def thumbnail(self):
        return self._entry.getThumbnail()

    @thumbnail.setter
    def thumbnail(self, value):
        if isinstance(value, _BufferedImage):
            pass
        else:
            raise TypeError('fixme: support pil')
        return self._entry.setThumbnail(value)

    @property
    def metadata(self):
        return self._metadata

    @metadata.setter
    def metadata(self, value):
        self._metadata.clear()
        self._metadata.update(value)


class _QuPathProjectImageEntriesProxy(MutableSet):

    def discard(self, x: QuPathProjectImageEntry) -> None:
        pass

    # TODO:
    #   set.add returns None normally.
    #   need to think about the interface because the conversion from
    #   file to entry happens in qupath in a project.
    def add(self, filename) -> QuPathProjectImageEntry:
        # first get a server builder
        img_path = pathlib.Path(filename).absolute()
        support = _ImageServerProvider.getPreferredUriImageSupport(_BufferedImage, _String(str(img_path)))
        if not support:
            raise Exception("unsupported file")
        server_builders = list(support.getBuilders())
        if not server_builders:
            raise Exception("unsupported file")
        server_builder = server_builders[0]
        entry = self._project.addImage(server_builder)

        # all of this happens in qupath.lib.gui.commands.ProjectImportImagesCommand
        server = server_builder.build()
        entry.setImageName(_ServerTools.getDisplayableImageName(server))
        # basically getThumbnailRGB(server, None) without the resize...
        thumbnail = server.getDefaultThumbnail(server.nZSlices() // 2, 0)
        entry.setThumbnail(thumbnail)

        return QuPathProjectImageEntry(entry)

    def __init__(self, project):
        if not isinstance(project, _DefaultProject):
            raise TypeError('requires _DefaultProject instance')
        self._project = project
        self._it = iter(())

    def __len__(self):
        return self._project.size()

    def __contains__(self, __x: object) -> bool:
        if not isinstance(__x, _DefaultProjectImageEntry):
            return False
        return False  # FIXME

    def __iter__(self):
        self._it = iter(self._project.getImageList())
        return self

    def __next__(self):
        image_entry = next(self._it)
        return QuPathProjectImageEntry(image_entry)


class QuPathPathClass:

    def __init__(self, path_class=None):
        if not isinstance(path_class, _PathClass):
            raise ValueError("use QuPathPathClass.create() to instantiate")
        self._path_class = path_class

    @classmethod
    def create(cls, name, color=None, parent=None, exist_ok=True):
        if name is None and parent is not None:
            raise ValueError("cannot create derived PathClass with name=None")

        _parent_class = None
        if parent is not None:
            if not isinstance(parent, QuPathPathClass):
                raise TypeError("parent must be a QuPathPathClass")
            _parent_class = parent._path_class

        path_class_str = _PathClass.derivedClassToString(_parent_class, name)
        if not exist_ok:
            if bool(_PathClassFactory.classExists(path_class_str)):
                raise Exception("path_class already created")

        _color = _ColorTools.makeRGB(int(color[0]), int(color[1]), int(color[2]))
        path_class = _PathClassFactory.getDerivedPathClass(parent._path_class, name, _color)
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
        return QuPathPathClass(path_class)

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
        r = int(_ColorTools.red(argb))
        g = int(_ColorTools.green(argb))
        b = int(_ColorTools.blue(argb))
        return r, g, b

    @color.setter
    def color(self, rgb):
        r, g, b = map(int, rgb)
        a = int(255 * self.alpha)
        argb = _ColorTools.makeRGBA(r, g, b, a)
        self._path_class.setColor(argb)

    @property
    def alpha(self):
        argb = self._path_class.getColor()
        a = int(_ColorTools.alpha(argb))
        return a / 255.0

    @alpha.setter
    def alpha(self, alpha):
        r, g, b = self.color
        a = int(255 * alpha)
        argb = _ColorTools.makeRGBA(r, g, b, a)
        self._path_class.setColor(argb)

    @property
    def is_valid(self):
        return bool(self._path_class.isValid())

    @property
    def is_derived_class(self):
        return bool(self._path_class.isDerivedClass())

    def __repr__(self):
        return f"<PathClass '{self.id}'>"


class QuPathProject:

    def __init__(self, path: Union[str, pathlib.Path]):
        path = pathlib.Path(path)
        if path.is_file():
            self._project = _ProjectIO.loadProject(_File(str(path)), _BufferedImage)
        else:
            self._project = _Projects.createProject(_File(str(path)), _BufferedImage)

        self._image_entries_proxy = _QuPathProjectImageEntriesProxy(self._project)

    @property
    def images(self):
        return self._image_entries_proxy

    @images.setter
    def images(self, images):
        _images = []
        for image in images:
            if not isinstance(image, QuPathProjectImageEntry):
                raise TypeError("images needs to be iterable of instances of QuPathProjectImageEntry")
        self.images.clear()
        for image in _images:
            self.images.add(image)

    def __len__(self):
        return len(self.images)

    @property
    def image_id(self):
        return self._project.IMAGE_ID

    @property
    def uri(self):
        return str(self._project.getURI().toString())

    @property
    def uri_previous(self):
        uri = self._project.getPreviousURI()
        if uri is None:
            return None
        return str(uri.toString())

    @property
    def path_classes(self):
        return tuple(map(QuPathPathClass, self._project.getPathClasses()))

    @path_classes.setter
    def path_classes(self, path_classes):
        pcs = [pc._path_class for pc in path_classes]
        self._project.setPathClasses(pcs)

    @property
    def path(self):
        return self._project.getPath()

    def save(self):
        self._project.syncChanges()

    @property
    def mask_image_names(self):
        return bool(self._project.getMaskImageNames())

    @mask_image_names.setter
    def mask_image_names(self, value: bool):
        self._project.setMaskImageNames(value)

    @property
    def name(self):
        return self._project.getName()

    def __repr__(self):
        name = self._project.getNameFromURI(self._project.getURI())
        return f'<QuPathProject {name}>'

    @property
    def timestamp_creation(self):
        return self._project.getCreationTimestamp()

    @property
    def timestamp_modification(self):
        return self._project.getModificationTimestamp()

    @property
    def version(self):
        return str(self._project.getVersion())
