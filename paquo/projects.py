import collections.abc as collections_abc
import math
import pathlib
import re
import shutil
from contextlib import contextmanager
from typing import Union, Iterable, Tuple, Optional, Iterator, \
    Dict, overload, Sequence, Hashable, Any

try:
    from typing import Literal  # type: ignore
except ImportError:
    from typing_extensions import Literal

from paquo import settings
from paquo._base import QuPathBase
from paquo._logging import redirect, get_logger
from paquo._utils import make_backup_filename
from paquo.classes import QuPathPathClass
from paquo.images import QuPathProjectImageEntry, ImageProvider, SimpleURIImageProvider, QuPathImageType
from paquo.java import ImageServerProvider, BufferedImage, ProjectImportImagesCommand, \
    ProjectIO, File, Projects, String, ServerTools, DefaultProject, URI, GeneralTools, IOException, \
    NegativeArraySizeException

_log = get_logger(__name__)


class _ProjectImageEntriesProxy(collections_abc.Sequence):
    """iterable container holding image entries"""
    # todo: decide if this should be a mapping or not...
    #   maybe with key id? to simplify re-association

    def __init__(self, project: DefaultProject):
        if not isinstance(project, DefaultProject):
            raise TypeError('requires DefaultProject instance')  # pragma: no cover
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
            for key in removed:  # pragma: no cover
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

    def _repr_html_(self, compact=False) -> str:
        from paquo._repr import div, h4, repr_html
        images = [
            repr_html(img, compact=True, index=idx) for idx, img in enumerate(self)
        ]
        header_css = {"margin-top": "0"} if not compact else {}
        return div(
            h4(text="Images:", style=header_css),
            div(*images, style={"display": "flex"}),
        )

    @overload
    def __getitem__(self, i: int) -> QuPathProjectImageEntry: ...

    @overload
    def __getitem__(self, i: slice) -> Sequence[QuPathProjectImageEntry]: ...

    def __getitem__(self, i):
        if not isinstance(i, (int, slice)):
            raise IndexError(i)
        return list(self._images.values())[i]


def _stash_project_files(project_dir: pathlib.Path):
    """move rename projects files in a project to .backup"""
    if not project_dir.is_dir():
        return
    if not any(project_dir.iterdir()):
        return

    if settings.safe_truncate:
        # create a backup archive of the project
        _log.warning(f"backing up {project_dir.name} before truncating!"
                     " (this can be disabled via PAQUO_SAFE_TRUNCATE)")
        str_name = shutil.make_archive(
            f".{project_dir.name}",
            format="zip",
            root_dir=project_dir.parent,
            base_dir=project_dir,
            logger=_log
        )
        # and rename it
        src_name = pathlib.Path(str_name)
        dst_name = make_backup_filename(project_dir.parent, src_name.stem)
        shutil.move(str(src_name), str(dst_name))
        _log.info(f"backup to {dst_name.name} successful")

    # empty the project directory
    for p in project_dir.iterdir():
        if p.is_file():
            p.unlink()
        elif p.is_dir():
            shutil.rmtree(p)
    # done


DEFAULT_IMAGE_PROVIDER: Any = SimpleURIImageProvider()


ProjectIOMode = Union[
    Literal["r"],
    Literal["r+"],
    Literal["w"],
    Literal["w+"],
    Literal["a"],
    Literal["a+"],
    Literal["x"],
    Literal["x+"],
]


class QuPathProject(QuPathBase[DefaultProject]):

    def __init__(self,
                 path: Union[str, pathlib.Path],
                 mode: ProjectIOMode = 'x',
                 *,
                 image_provider: ImageProvider = DEFAULT_IMAGE_PROVIDER):
        """load or create a new qupath project

        Parameters
        ----------
        path:
            path to `project.qpproj` file, or its parent directory
        mode:
            'r' --> readonly, error if not there
            'r+' --> read/write, error if not there
            'a' = 'a+' --> read/write, create if not there, append if there
            'w' = 'w+' --> read/write, create if not there, truncate if there
            'x' = 'x+' --> read/write, create if not there, error if there

        """
        if not isinstance(image_provider, ImageProvider):
            raise TypeError("image_provider must quack like a paquo.images.ImageProvider")

        self._path = pathlib.Path(path)
        self._mode = str(mode)

        # guarantee p points to qpproj file (allow directory)
        if not self._path.suffix:
            self._path /= 'project.qpproj'
        elif self._path.suffix != ".qpproj":
            raise ValueError("project file requires '.qpproj' suffix")

        if not re.match(r"^[rawx][+]?$", mode):
            raise ValueError(f"unsupported mode '{mode}'")

        p = self._path.expanduser().absolute()
        _exists = p.is_file()
        self._READONLY = mode == "r"
        if self._READONLY:
            raise NotImplementedError("readonly mode not implemented yet, use 'r+'")

        if mode in {"r", "r+"} and not _exists:
            raise FileNotFoundError(p)
        elif mode in {"x", "x+"} and _exists:
            raise FileExistsError(p)
        elif mode in {"w", "w+"}:
            # truncate gracefully
            p_dir = p.parent
            if p_dir.is_dir():
                _stash_project_files(p_dir)
            _exists = False

        if _exists:
            project = ProjectIO.loadProject(File(str(p)), BufferedImage)
        else:
            p_dir = p.parent
            p_dir.mkdir(parents=True, exist_ok=True)
            for f in p_dir.iterdir():
                if not f.match("*.backup"):
                    raise ValueError("will only create projects in empty directories")
            project = Projects.createProject(File(str(p_dir)), BufferedImage)

        super().__init__(project)
        self._image_entries_proxy = _ProjectImageEntriesProxy(project)
        self._image_provider = image_provider

    @property
    def images(self) -> Sequence[QuPathProjectImageEntry]:
        """project images"""
        return self._image_entries_proxy

    @contextmanager
    def _stage_image_entry(self, server_builder):
        """internal contextmanager for staging new entries"""
        entry = self.java_object.addImage(server_builder)
        try:
            yield entry
        except Exception:
            # todo: check if we could set removeAllData to True here
            self.java_object.removeImage(entry, False)
            raise
        finally:
            # update the proxy
            self._image_entries_proxy.refresh()

    @redirect(stderr=True, stdout=True)  # type: ignore
    def add_image(self,
                  image_id: Any,  # this should actually be ID type of the image provider
                  image_type: Optional[QuPathImageType] = None,
                  *,
                  allow_duplicates: bool = False) -> QuPathProjectImageEntry:
        """add an image to the project

        Parameters
        ----------
        image_id:
            image_id pointing to the image file (with default image_provider: filename)
        image_type:
            provide an image type for the image. If not provided the user will
            be prompted before opening the image in QuPath.
        allow_duplicates:
            check if file has already been added to the project.

        """
        # test if we may add:
        img_uri = self._image_provider.uri(image_id)
        if img_uri is None:
            raise FileNotFoundError(f"image_provider can't provide URI for requested image_id: '{image_id}'")
        img_id = self._image_provider.id(img_uri)
        if not img_id == image_id:  # pragma: no cover
            _log.warning(f"image_provider roundtrip error: '{image_id}' -> uri -> '{img_id}'")
            raise RuntimeError("the image provider failed to roundtrip the image id correctly")

        if not allow_duplicates:
            for entry in self.images:
                uri = self._image_provider.id(entry.uri)
                if img_id == uri:
                    raise FileExistsError(img_id)

        # first get a server builder
        try:
            support = ImageServerProvider.getPreferredUriImageSupport(
                BufferedImage,
                String(str(img_uri))
            )
        except IOException:  # pragma: no cover
            # it's possible that an image_provider returns an URI but that URI
            # is not actually reachable. In that case catch the java IOException
            # and raise a FileNotFoundError here
            raise FileNotFoundError(image_id)
        if not support:
            raise IOError("no preferred support found")  # pragma: no cover
        server_builders = list(support.getBuilders())
        if not server_builders:
            raise IOError("no supported server builders found")  # pragma: no cover
        server_builder = server_builders[0]

        with self._stage_image_entry(server_builder) as j_entry:
            # all of this happens in qupath.lib.gui.commands.ProjectImportImagesCommand
            try:
                server = server_builder.build()
            except IOException:
                _, _, _sb = server_builder.__class__.__name__.rpartition(".")
                raise IOError(f"{_sb} can't open {str(image_id)}")
            j_entry.setImageName(ServerTools.getDisplayableImageName(server))

            # add some informative logging
            _md = server.getMetadata()
            width = int(_md.getWidth())
            height = int(_md.getHeight())
            downsamples = [float(x) for x in _md.getPreferredDownsamplesArray()]
            target_downsample = math.sqrt(width / 1024.0 * height / 1024.0)
            _log.info(f"Image[{width}x{height}] with downsamples {downsamples}")
            if not any(d >= target_downsample for d in downsamples):
                _log.warning(f"No matching downsample for thumbnail! This might take a long time...")

            # set the project thumbnail
            try:
                thumbnail = ProjectImportImagesCommand.getThumbnailRGB(server, None)
            except NegativeArraySizeException:  # pragma: no cover
                raise RuntimeError(
                    "Thumbnailing FAILED. Image might be too large and has no embedded thumbnail."
                )
            else:
                j_entry.setThumbnail(thumbnail)

        py_entry = self._image_entries_proxy[-1]
        if image_type is not None:
            py_entry.image_type = image_type
        # save project after adding image
        self.save()
        return py_entry

    def is_readable(self) -> Dict[Hashable, bool]:
        """verify if images are reachable"""
        readability_map = {}
        for image in self.images:
            image_id = self._image_provider.id(image.uri)
            if image_id in readability_map:  # pragma: no cover
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

    # @property
    # def uri_previous(self) -> Optional[str]:
    #     """previous uri. potentially useful for re-associating"""
    #     uri = self.java_object.getPreviousURI()
    #     if uri is None:
    #         return None
    #     return str(uri.toString())

    @property
    def path_classes(self) -> Tuple[QuPathPathClass, ...]:
        """return path_classes stored in the project"""
        return tuple(map(QuPathPathClass.from_java, self.java_object.getPathClasses()))

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
        try:
            self.java_object.syncChanges()
        except IOException:
            raise IOError("occurred when trying to save the project")

    @property
    def name(self) -> str:
        """project name"""
        name = str(self.java_object.getName())
        if name.endswith("/project.qpproj"):
            name = name[:-15]
        return name

    def __repr__(self) -> str:
        # name = self.java_object.getNameFromURI(self.java_object.getURI())
        return f"<QuPathProject path='{self._path}' mode='{self._mode}'>"

    def _repr_html_(self) -> str:
        from paquo._repr import br, h3, div, p, span, repr_html
        return div(
            h3(style={"margin-top": "0"}, text=f"Project: {self.name}"),
            p(
                span(text="path: ", style={"font-weight": "bold"}),
                span(text=str(self._path)),
                br(),
                span(text="mode: ", style={"font-weight": "bold"}),
                span(text=self._mode),
                style={"margin": "0.5em"},
            ),
            repr_html(self.images),
        )

    @property
    def timestamp_creation(self) -> int:
        """system time at creation in milliseconds"""
        return int(self.java_object.getCreationTimestamp())

    @property
    def timestamp_modification(self) -> int:
        """system time at modification in milliseconds"""
        return int(self.java_object.getModificationTimestamp())

    @property
    def version(self) -> Optional[str]:
        """the project version. should be identical to the qupath version"""
        # for older projects this returns null.
        # for newer projects this will be set to DefaultProject.LATEST_VERSION
        # which is just GeneralTools.getVersion()...
        version = self.java_object.getVersion()
        try:
            # note: this still implicitly requires a QuPath version that has GeneralTools
            #   which is probably fine...
            latest_version = GeneralTools.getVersion()
        except AttributeError:  # pragma: no cover
            latest_version = None
        # version is None, until we save a project to disk AND reload it!
        if version:
            return str(version)
        if latest_version:
            return str(latest_version)
        return None  # pragma: no cover

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.save()
