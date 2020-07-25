import pathlib
import collections.abc as collections_abc
from typing import Union, Iterable, Tuple, Optional, Iterator, \
    List, Dict, overload, Sequence, Literal

from paquo._base import QuPathBase
from paquo.classes import QuPathPathClass
from paquo.images import QuPathProjectImageEntry
from paquo.java import ImageServerProvider, BufferedImage, \
    ProjectIO, File, Projects, String, ServerTools, DefaultProject, URI


class _ProjectImageEntriesProxy(collections_abc.Sequence):
    """iterable container holding image entries"""
    # todo: decide if this should be a mapping or not...
    #   maybe with key id? to simplify re-association

    def __init__(self, project: DefaultProject):
        if not isinstance(project, DefaultProject):
            raise TypeError('requires DefaultProject instance')
        self._project = project
        self._images = {
            self._key_func(entry): QuPathProjectImageEntry(entry)
            for entry in self._project.getImageList()
        }

    def _key_func(self, entry):
        """retrieve the fullProjectID from an ImageEntry

        note: this is only valid for the current project instance
        """
        # basically `DefaultProjectImageEntry.getFullProjectEntryID()`
        # but don't go via image_data
        return (
            str(self._project.getPath().toAbsolutePath().toString()),
            str(entry.getID()),
        )

    def refresh(self):
        removed = set(self._images.keys())
        for entry in self._project.getImageList():
            key = self._key_func(entry)
            if key not in self._images:
                self._images[key] = QuPathProjectImageEntry(entry)
            else:
                removed.discard(key)  # existing entry
        if removed:
            for key in removed:
                _ = self._images.pop(key)
                raise NotImplementedError("removal not yet implemented")

    def __iter__(self) -> Iterator[QuPathProjectImageEntry]:
        return iter(self._images.values())

    def __contains__(self, entry: object) -> bool:
        if not isinstance(entry, QuPathProjectImageEntry):
            return False
        return entry.java_object.getFullProjectEntryID() in self._images

    def __len__(self) -> int:
        return len(self._images)

    def __repr__(self):
        return f"<ImageEntries({repr([entry.image_name for entry in self])})>"

    @overload
    def __getitem__(self, i: slice) -> Sequence[QuPathProjectImageEntry]:
        ...

    def __getitem__(self, i: int) -> QuPathProjectImageEntry:
        # n images is very likely to be small
        return list(self._images.values())[i]


class QuPathProject(QuPathBase):

    def __init__(self, path: Union[str, pathlib.Path]):
        """load or create a new qupath project"""
        path = pathlib.Path(path)
        if path.is_file():
            project = ProjectIO.loadProject(File(str(path)), BufferedImage)
        else:
            project = Projects.createProject(File(str(path)), BufferedImage)

        super().__init__(project)
        self._image_entries_proxy = _ProjectImageEntriesProxy(project)

    @property
    def images(self) -> Sequence[QuPathProjectImageEntry]:
        """project images"""
        return self._image_entries_proxy

    def add_image(self, filename: Union[str, pathlib.Path]) -> QuPathProjectImageEntry:
        """add an image to the project

        todo: expose copying/moving/re-association etc...

        Parameters
        ----------
        filename:
            filename pointing to the image file

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
        entry = self.java_object.addImage(server_builder)

        # all of this happens in qupath.lib.gui.commands.ProjectImportImagesCommand
        server = server_builder.build()
        entry.setImageName(ServerTools.getDisplayableImageName(server))
        # basically getThumbnailRGB(server, None) without the resize...
        thumbnail = server.getDefaultThumbnail(server.nZSlices() // 2, 0)
        entry.setThumbnail(thumbnail)

        # update the proxy
        self._image_entries_proxy.refresh()

        return self._image_entries_proxy[-1]

    def is_readable(self, ) -> Dict[str, bool]:
        """verify if images are reachable"""
        # todo: image_name is definitely not a good unique key...
        return {
            img.image_name: img.is_readable() for img in self.images
        }

    def update_image_paths(self, name_path_map: Dict[str, str]):
        """update image path uris if image files moved"""
        for image in self.images:
            if image.image_name not in name_path_map:
                continue
            # update uri
            new_path = pathlib.Path(name_path_map[image.image_name])
            new_path = new_path.absolute()
            uri2uri = {
                URI(image.uri): File(str(new_path)).toURI()
            }
            image.java_object.updateServerURIs(uri2uri)

    @property
    def uri(self) -> str:
        """the uri identifying the project location"""
        return str(self.java_object.getURI().toString())

    @property
    def uri_previous(self) -> Optional[str]:
        """previous uri. potentially useful for re-associating"""
        uri = self.java_object.getPreviousURI()
        if uri is None:
            return None
        return str(uri.toString())

    @property
    def path_classes(self) -> Tuple[QuPathPathClass]:
        """return path_classes stored in the project"""
        return tuple(map(QuPathPathClass, self.java_object.getPathClasses()))

    @path_classes.setter
    def path_classes(self, path_classes: Iterable[QuPathPathClass]):
        """to add path_classes reassign all path_classes here"""
        pcs = [pc.java_object for pc in path_classes]
        self.java_object.setPathClasses(pcs)

    @property
    def path(self) -> pathlib.Path:
        """the path to the project root"""
        return pathlib.Path(str(self.java_object.getPath()))

    def save(self) -> None:
        """flush changes in the project to disk

        (writes path_classes and project data)
        """
        for entry in self.images:
            entry.save()
        self.java_object.syncChanges()

    @property
    def name(self) -> str:
        """project name"""
        return self.java_object.getName()

    def __repr__(self) -> str:
        name = self.java_object.getNameFromURI(self.java_object.getURI())
        return f'<QuPathProject "{name}">'

    @property
    def timestamp_creation(self) -> int:
        """system time at creation in milliseconds"""
        return int(self.java_object.getCreationTimestamp())

    @property
    def timestamp_modification(self) -> int:
        """system time at modification in milliseconds"""
        return int(self.java_object.getModificationTimestamp())

    @property
    def version(self) -> str:
        """the project version. should be identical to the qupath version"""
        # note: only available when building project while the gui
        #   is active? ...
        return str(self.java_object.getVersion())

    @classmethod
    def from_settings(
            cls,
            project_path: pathlib.Path,
            image_paths: List[pathlib.Path],
            path_classes: Optional[List[Dict]] = None,
            image_metadata: Optional[Dict] = None,
            *,
            save: bool = True
    ):
        """create a project from settings"""
        if project_path.exists():
            raise ValueError("project_path exists already")
        project_path.mkdir(parents=True)

        # create empty project
        project = QuPathProject(project_path)

        # set required path classes
        if path_classes:
            project.path_classes = [
                QuPathPathClass.create(**class_dict) for class_dict in path_classes
            ]

        # append images from paths
        for image in image_paths:
            entry = project.add_image(image)
            if image_metadata:
                entry.metadata.update(image_metadata)

        if save:
            # store the project
            project.save()

        return project
