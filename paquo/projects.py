import pathlib
from collections.abc import MutableSet
from typing import Union

from paquo.classes import QuPathPathClass
from paquo.images import QuPathProjectImageEntry
from paquo.java import ImageServerProvider, BufferedImage, DefaultProjectImageEntry, \
    ProjectIO, File, Projects, String, ServerTools, DefaultProject


class _ProjectImageEntriesProxy(MutableSet):

    def discard(self, x: QuPathProjectImageEntry) -> None:
        pass

    # TODO:
    #   set.add returns None normally.
    #   need to think about the interface because the conversion from
    #   file to entry happens in qupath in a project.
    def add(self, filename) -> QuPathProjectImageEntry:
        # first get a server builder
        img_path = pathlib.Path(filename).absolute()
        support = ImageServerProvider.getPreferredUriImageSupport(BufferedImage, String(str(img_path)))
        if not support:
            raise Exception("unsupported file")
        server_builders = list(support.getBuilders())
        if not server_builders:
            raise Exception("unsupported file")
        server_builder = server_builders[0]
        entry = self._project.addImage(server_builder)

        # all of this happens in qupath.lib.gui.commands.ProjectImportImagesCommand
        server = server_builder.build()
        entry.setImageName(ServerTools.getDisplayableImageName(server))
        # basically getThumbnailRGB(server, None) without the resize...
        thumbnail = server.getDefaultThumbnail(server.nZSlices() // 2, 0)
        entry.setThumbnail(thumbnail)

        return QuPathProjectImageEntry(entry)

    def __init__(self, project):
        if not isinstance(project, DefaultProject):
            raise TypeError('requires _DefaultProject instance')
        self._project = project
        self._it = iter(())

    def __len__(self):
        return self._project.size()

    def __contains__(self, __x: object) -> bool:
        if not isinstance(__x, DefaultProjectImageEntry):
            return False
        return False  # FIXME

    def __iter__(self):
        self._it = iter(self._project.getImageList())
        return self

    def __next__(self):
        image_entry = next(self._it)
        return QuPathProjectImageEntry(image_entry)


class QuPathProject:

    def __init__(self, path: Union[str, pathlib.Path]):
        path = pathlib.Path(path)
        if path.is_file():
            self._project = ProjectIO.loadProject(File(str(path)), BufferedImage)
        else:
            self._project = Projects.createProject(File(str(path)), BufferedImage)

        self._image_entries_proxy = _ProjectImageEntriesProxy(self._project)

    @property
    def images(self):
        return self._image_entries_proxy

    @images.setter
    def images(self, images):
        _images = []
        for image in images:
            if not isinstance(image, QuPathProjectImageEntry):
                raise TypeError("images needs to be iterable of instances of ProjectImageEntry")
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