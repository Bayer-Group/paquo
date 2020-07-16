import pathlib
import collections.abc as collections_abc
from typing import Union, Iterable, Tuple, Optional, Iterator, Collection

from paquo.classes import QuPathPathClass
from paquo.images import QuPathProjectImageEntry
from paquo.java import ImageServerProvider, BufferedImage, DefaultProjectImageEntry, \
    ProjectIO, File, Projects, String, ServerTools, DefaultProject


class _ProjectImageEntriesProxy(collections_abc.Collection):
    """iterable container holding image entries"""
    # todo: decide if this should be a mapping or not...
    #   maybe with key id? to simplify re-association

    def __init__(self, project: DefaultProject):
        if not isinstance(project, DefaultProject):
            raise TypeError('requires DefaultProject instance')
        self._project = project

    def __len__(self) -> int:
        return int(self._project.size())

    def __iter__(self) -> Iterator[QuPathProjectImageEntry]:
        return iter(map(QuPathProjectImageEntry, self._project.getImageList()))

    def __contains__(self, __x: object) -> bool:
        if not isinstance(__x, DefaultProjectImageEntry):
            return False
        # this would need to compare via unique image ids as in
        # Project.getEntry
        raise NotImplementedError("todo")


class QuPathProject:

    def __init__(self, path: Union[str, pathlib.Path]):
        """load or create a new qupath project"""
        path = pathlib.Path(path)
        if path.is_file():
            self._project = ProjectIO.loadProject(File(str(path)), BufferedImage)
        else:
            self._project = Projects.createProject(File(str(path)), BufferedImage)

        self._image_entries_proxy = _ProjectImageEntriesProxy(self._project)

    @property
    def images(self) -> Collection[QuPathProjectImageEntry]:
        """project images"""
        return self._image_entries_proxy

    def add_image(self, filename: str) -> QuPathProjectImageEntry:
        """add an image to the project

        Parameters
        ----------
        filename:
            filename pointing to the image file

        todo: expose copying/moving/re-association etc...
        """
        # first get a server builder
        img_path = pathlib.Path(filename).absolute()
        support = ImageServerProvider.getPreferredUriImageSupport(
            BufferedImage,
            String(str(img_path))
        )
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

    @property
    def uri(self) -> str:
        """the uri identifying the project location"""
        return str(self._project.getURI().toString())

    @property
    def uri_previous(self) -> Optional[str]:
        """previous uri. potentially useful for re-associating"""
        uri = self._project.getPreviousURI()
        if uri is None:
            return None
        return str(uri.toString())

    @property
    def path_classes(self) -> Tuple[QuPathPathClass]:
        """return path_classes stored in the project"""
        return tuple(map(QuPathPathClass, self._project.getPathClasses()))

    @path_classes.setter
    def path_classes(self, path_classes: Iterable[QuPathPathClass]):
        """to add path_classes reassign all path_classes here"""
        pcs = [pc.java_object for pc in path_classes]
        self._project.setPathClasses(pcs)

    @property
    def path(self) -> pathlib.Path:
        """the path to the project root"""
        return pathlib.Path(str(self._project.getPath()))

    def save(self) -> None:
        """flush changes in the project to disk

        (writes path_classes and project data)
        """
        self._project.syncChanges()

    @property
    def name(self) -> str:
        """project name"""
        return self._project.getName()

    def __repr__(self) -> str:
        name = self._project.getNameFromURI(self._project.getURI())
        return f'<QuPathProject "{name}">'

    @property
    def timestamp_creation(self) -> int:
        """system time at creation in milliseconds"""
        return int(self._project.getCreationTimestamp())

    @property
    def timestamp_modification(self) -> int:
        """system time at modification in milliseconds"""
        return int(self._project.getModificationTimestamp())

    @property
    def version(self) -> str:
        """the project version. should be identical to the qupath version"""
        # note: only available when building project while the gui
        #   is active? ...
        return str(self._project.getVersion())
