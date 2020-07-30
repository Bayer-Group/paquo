import pathlib
import collections.abc as collections_abc
from typing import Union, Iterable, Tuple, Optional, Iterator, \
    List, Dict, overload, Sequence, Hashable

from paquo._base import QuPathBase
from paquo._logging import redirect
from paquo.classes import QuPathPathClass
from paquo.images import QuPathProjectImageEntry, ImageProvider, SimpleURIImageProvider, QuPathImageType
from paquo.java import ImageServerProvider, BufferedImage, \
    ProjectIO, File, Projects, String, ServerTools, DefaultProject, URI, GeneralTools, IOException


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
        full_id = self._key_func(entry.java_object)
        return full_id in self._images

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


DEFAULT_IMAGE_PROVIDER = SimpleURIImageProvider()


class QuPathProject(QuPathBase):

    def __init__(self,
                 path: Union[str, pathlib.Path],
                 create: bool = True,
                 *,
                 image_provider: ImageProvider = DEFAULT_IMAGE_PROVIDER):
        """load or create a new qupath project

        Parameters
        ----------
        path:
            path to `project.qpproj` file, or its parent directory
        create:
            if create is False raise FileNotFoundError if project doesn't exist

        """
        if not isinstance(image_provider, ImageProvider):
            raise TypeError("image_provider must quack like a paquo.images.ImageProvider")

        p = pathlib.Path(path).expanduser().absolute()
        # guarantee p points to qpproj file (allow directory)
        if not p.suffix:
            p /= 'project.qpproj'
        elif p.suffix != ".qpproj":
            raise ValueError("project file requires '.qpproj' suffix")

        if p.is_file():  # existing project
            project = ProjectIO.loadProject(File(str(p)), BufferedImage)

        elif not create:
            raise FileNotFoundError(path)

        else:  # create new
            p_dir = p.parent
            p_dir.mkdir(parents=True, exist_ok=True)
            if any(p_dir.iterdir()):
                raise ValueError("will only create projects in empty directories")
            project = Projects.createProject(File(str(p_dir)), BufferedImage)

        super().__init__(project)
        self._image_entries_proxy = _ProjectImageEntriesProxy(project)
        self._image_provider = image_provider

    @property
    def images(self) -> Sequence[QuPathProjectImageEntry]:
        """project images"""
        return self._image_entries_proxy

    @redirect(stderr=True, stdout=True)
    def add_image(self,
                  filename: Union[str, pathlib.Path],
                  image_type: Optional[QuPathImageType] = None) -> QuPathProjectImageEntry:
        """add an image to the project

        todo: expose copying/moving/re-association etc...

        Parameters
        ----------
        filename:
            filename pointing to the image file
        image_type:
            provide an image type for the image. If not provided the user will
            be prompted before opening the image in QuPath.

        """
        # first get a server builder
        img_path = pathlib.Path(filename).absolute()
        try:
            support = ImageServerProvider.getPreferredUriImageSupport(
                BufferedImage,
                String(str(img_path))
            )
        except IOException:
            raise FileNotFoundError(filename)
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

        py_entry = self._image_entries_proxy[-1]
        if image_type is not None:
            py_entry.image_type = image_type
        return py_entry

    def is_readable(self) -> Dict[Hashable, bool]:
        """verify if images are reachable"""
        readability_map = {}
        for image in self.images:
            image_id = self._image_provider.id(image.uri)
            if image_id in readability_map:
                raise RuntimeError("received the same image_id from image_provider for two different images")
            readability_map[image_id] = image.is_readable()
        return readability_map

    def update_image_paths(self, **rebase_kwargs):
        """update image path uris if image files moved"""
        # allow rebasing all image uris in a single call to rebase
        old_uris = [image.uri for image in self.images]
        new_uris = self._image_provider.rebase(*old_uris, **rebase_kwargs)

        # build the java URI to URI mapping
        uri2uri = {}
        for old_uri, new_uri in zip(old_uris, new_uris):
            if new_uri is None:
                continue
            elif ImageProvider.compare_uris(new_uri, old_uri):
                continue
            uri2uri[URI(old_uri)] = URI(new_uri)

        # update uris if possible
        for image in self.images:
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

    @redirect(stderr=True, stdout=True)
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
        # for older projects this returns null.
        # for newer projects this will be set to DefaultProject.LATEST_VERSION
        # which is just GeneralTools.getVersion()...
        version = self.java_object.getVersion()
        # fixme: this implictly requires qupath versions >= 0.2.0-m3
        latest_version = GeneralTools.getVersion()
        if version is None:
            return str(latest_version)
        return str(version)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.save()
