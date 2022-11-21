import collections.abc as collections_abc
import math
import pathlib
import re
import shutil
import sys
from contextlib import contextmanager
from contextlib import nullcontext
from typing import Any
from typing import Callable
from typing import ContextManager
from typing import Dict
from typing import Iterable
from typing import Iterator
from typing import List
from typing import Optional
from typing import Sequence
from typing import Tuple
from typing import Union
from typing import overload
from urllib.parse import urlsplit

if sys.version_info >= (3, 8):
    from typing import Literal
else:
    from typing_extensions import Literal

from paquo import settings
from paquo._logging import get_logger
from paquo._logging import redirect
from paquo._utils import make_backup_filename
from paquo.classes import QuPathPathClass
from paquo.images import ImageProvider
from paquo.images import QuPathImageType
from paquo.images import QuPathProjectImageEntry
from paquo.images import SimpleFileImageId
from paquo.java import URI
from paquo.java import BufferedImage
from paquo.java import DefaultProject
from paquo.java import ExceptionInInitializerError
from paquo.java import File
from paquo.java import Files
from paquo.java import GeneralTools
from paquo.java import ImageServerProvider
from paquo.java import IOException
from paquo.java import NegativeArraySizeException
from paquo.java import ProjectImportImagesCommand_getThumbnailRGB
from paquo.java import ProjectIO
from paquo.java import Projects
from paquo.java import ServerTools
from paquo.java import String
from paquo.java import compatibility

_log = get_logger(__name__)


class _ProjectImageEntriesProxy(collections_abc.Sequence):
    """iterable container holding image entries"""
    # todo: decide if this should be a mapping or not...
    #   maybe with key id? to simplify re-association

    def __init__(self, project: 'QuPathProject'):
        if not isinstance(project.java_object, DefaultProject):
            raise TypeError('requires DefaultProject instance')  # pragma: no cover
        self._project = project
        self._images = {
            self._key_func(entry): QuPathProjectImageEntry(entry, _project_ref=self._project)
            for entry in self._project.java_object.getImageList()
        }

    def _key_func(self, entry):
        """retrieve the fullProjectID from an ImageEntry

        note: this is only valid for the current project instance
        """
        # basically `DefaultProjectImageEntry.getFullProjectEntryID()`
        # but don't go via image_data
        return (
            str(self._project.java_object.getPath().toAbsolutePath().toString()),
            str(entry.getID()),
        )

    def refresh(self):
        removed = set(self._images.keys())
        for entry in self._project.java_object.getImageList():
            key = self._key_func(entry)
            if key not in self._images:
                self._images[key] = QuPathProjectImageEntry(entry, _project_ref=self._project)
            else:
                removed.discard(key)  # existing entry
        if removed:
            for key in removed:  # pragma: no cover
                _ = self._images.pop(key)

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
        return f"ImageEntries({repr([entry.image_name for entry in self])})"

    def _repr_html_(self, compact=False) -> str:
        from paquo._repr import div
        from paquo._repr import h4
        from paquo._repr import repr_html
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


DEFAULT_IMAGE_PROVIDER: Any = ImageProvider()


ProjectIOMode = Literal["r", "r+", "w", "w+", "a", "a+", "x", "x+"]


class QuPathProject:
    java_object: DefaultProject

    def __init__(self,
                 path: Union[str, pathlib.Path],
                 mode: ProjectIOMode = 'r',
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
        self._readonly = mode == "r"

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
            cm: Callable[..., ContextManager[Any]]
            if compatibility.requires_missing_classes_json_fix():
                @contextmanager
                def cm(is_readonly):
                    classes_json = p.parent.joinpath("classifiers", "classes.json")
                    is_missing = not classes_json.is_file()
                    if is_missing:
                        classes_json.write_text('{"pathClasses":[]}')
                    try:
                        yield
                    finally:
                        if is_missing and is_readonly:
                            classes_json.unlink(missing_ok=True)
            else:
                cm = nullcontext

            with redirect(stderr=True, stdout=True), cm(self._readonly):
                project = ProjectIO.loadProject(File(str(p)), BufferedImage)
        else:
            p_dir = p.parent
            p_dir.mkdir(parents=True, exist_ok=True)
            for f in p_dir.iterdir():
                if not f.match("*.backup"):
                    raise ValueError("will only create projects in empty directories")
            with redirect(stderr=True, stdout=True):
                project = Projects.createProject(File(str(p_dir)), BufferedImage)

        self.java_object = project
        self._image_entries_proxy = _ProjectImageEntriesProxy(self)
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

    @overload
    def add_image(
        self,
        image_id: SimpleFileImageId,
        image_type: Optional[QuPathImageType] = ...,
        *,
        allow_duplicates: bool = ...,
        return_list: Literal[True],
    ) -> List[QuPathProjectImageEntry]:
        ...

    @overload
    def add_image(
        self,
        image_id: SimpleFileImageId,
        image_type: Optional[QuPathImageType] = ...,
        *,
        allow_duplicates: bool = ...,
        return_list: Literal[False] = ...,
    ) -> Union[QuPathProjectImageEntry, List[QuPathProjectImageEntry]]:
        ...

    @redirect(stderr=True, stdout=True)
    def add_image(
        self,
        image_id: SimpleFileImageId,
        image_type: Optional[QuPathImageType] = None,
        *,
        allow_duplicates: bool = False,
        return_list: bool = False,
    ) -> Union[QuPathProjectImageEntry, List[QuPathProjectImageEntry]]:
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
        # readonly?
        if self._readonly:
            raise OSError("project in readonly mode")
        # test if we may add:
        img_uri = self._image_provider.uri(image_id)
        if img_uri is None:
            raise FileNotFoundError(f"image_provider can't provide URI for requested image_id: '{image_id}'")
        # img_id = self._image_provider.id(img_uri)
        # if img_id != image_id:  # pragma: no cover
        #     _log.warning(f"image_provider roundtrip error: '{image_id}' -> uri -> '{img_id}'")

        if not allow_duplicates:
            for entry in self.images:
                if img_uri == self._image_provider.uri(entry.uri):
                    raise FileExistsError(image_id)

        # first get a server builder
        try:
            support = ImageServerProvider.getPreferredUriImageSupport(
                BufferedImage,
                String(img_uri),
            )
        except IOException:  # pragma: no cover
            # it's possible that an image_provider returns an URI but that URI
            # is not actually reachable. In that case catch the java IOException
            # and raise a FileNotFoundError here
            raise FileNotFoundError(f"{image_id!r} as {img_uri!r}")
        except ExceptionInInitializerError:
            raise OSError("no preferred support found")
        if not support:
            raise OSError("no preferred support found")  # pragma: no cover
        server_builders = list(support.getBuilders())
        if not server_builders:
            raise OSError("no supported server builders found")  # pragma: no cover

        entries = []
        for server_builder in server_builders:
            with self._stage_image_entry(server_builder) as j_entry:
                # all of this happens in qupath.lib.gui.commands.ProjectImportImagesCommand
                try:
                    server = server_builder.build()
                except IOException:
                    _, _, _sb = server_builder.__class__.__name__.rpartition(".")
                    raise OSError(f"{_sb} can't open {str(image_id)}")
                j_entry.setImageName(ServerTools.getDisplayableImageName(server))

                # add some informative logging
                _md = server.getMetadata()
                width = int(_md.getWidth())
                height = int(_md.getHeight())
                downsamples = [float(x) for x in _md.getPreferredDownsamplesArray()]
                target_downsample = math.sqrt(width / 1024.0 * height / 1024.0)
                _log.info(f"Image[{width}x{height}] with downsamples {downsamples}")
                if not any(d >= target_downsample for d in downsamples):
                    _log.warning("No matching downsample for thumbnail! This might take a long time...")

                # set the project thumbnail
                try:
                    thumbnail = ProjectImportImagesCommand_getThumbnailRGB(server, None)
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
            py_entry.save()
            self.save(images=False)
            entries.append(py_entry)
        if return_list or len(entries) > 1:
            return entries
        else:
            return entries[0]

    def is_readable(self) -> Dict[str, bool]:
        """verify if images are reachable"""
        readability_map = {}
        for image in self.images:
            uri = image.uri
            if uri is None:
                raise RuntimeError(f"entry has None uri: {image!r}")
            if uri in readability_map:  # pragma: no cover
                raise RuntimeError("received the same image_id from image_provider for two different images")
            readability_map[str(uri)] = image.is_readable()
        return readability_map

    def update_image_paths(self, *, try_relative: bool = False, **rebase_kwargs) -> None:
        """update image path uris if image files moved

        Parameters
        ----------
        try_relative: bool
            if try_relative is True, update_image_paths tries to use relative paths
            to resolve missing image entries. This is useful in case you move the
            the project together with its images directory, or in case you remount
            at a different location.
        **rebase_kwargs:
            keyword arguments are handed over to the image provider instance.
            The default image provider is a paquo.images.ImageProvider
            which uses the uri2uri keyword argument. (A mapping from old URI to new
            URI: Mapping[str, str])

        """
        if not isinstance(try_relative, bool):
            raise TypeError(f"try_relative requires bool, got: {type(try_relative).__name__!r}")

        # get the current image URIs
        old_uris = [image.uri for image in self.images]

        # the uri to uri mapping
        uri2uri = {}

        if try_relative:
            assert not rebase_kwargs, "no other kwargs supported when try_relative=True"
            # test if project was moved (or mounted somewhere else...)
            prev_pth = GeneralTools.toPath(self.java_object.getPreviousURI()).getParent()
            proj_pth = GeneralTools.toPath(self.java_object.getURI()).getParent()
            if prev_pth and proj_pth and not prev_pth.equals(proj_pth):
                for old_uri in map(URI, old_uris):
                    img_pth = GeneralTools.toPath(old_uri)
                    new_pth = proj_pth.resolve(prev_pth.relativize(img_pth)).normalize()
                    if Files.exists(new_pth):
                        uri2uri[old_uri] = new_pth.normalize().toUri().normalize()

        else:
            # allow rebasing all image uris in a single call to rebase
            new_uris = self._image_provider.rebase(*old_uris, **rebase_kwargs)

            # build the java URI to URI mapping
            for old_uri, new_uri in zip(old_uris, new_uris):
                if new_uri is None:
                    continue
                elif ImageProvider.compare_uris(new_uri, old_uri):
                    continue
                uri2uri[URI(old_uri)] = URI(new_uri)

        # update uris if possible
        for image in self.images:
            image.java_object.updateServerURIs(uri2uri)

    @redirect(stderr=True, stdout=True)
    def remove_image(
        self,
        image_entry: Union[QuPathProjectImageEntry, int],
    ) -> None:
        """
        Delete an image from the QuPath project.

        Parameters
        ----------
        image_entry:
            the image entry to be removed
        """
        if isinstance(image_entry, int):
            image_entry = self.images[image_entry]
        if not isinstance(image_entry, QuPathProjectImageEntry):
            raise TypeError(
                f"expected QuPathProjectImageEntry, got: {type(image_entry).__name__!r}"
            )
        if self._readonly:
            raise OSError("project in readonly mode")
        try:
            self.java_object.removeImage(image_entry.java_object, False)
        finally:
            self._image_entries_proxy.refresh()
            self.save(images=False)

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
        if self._readonly:
            raise AttributeError("project in readonly mode")
        pcs = [pc.java_object for pc in path_classes]
        self.java_object.setPathClasses(pcs)

    @property
    def path(self) -> pathlib.Path:
        """the path to the project root"""
        return pathlib.Path(str(self.java_object.getPath()))

    @redirect(stderr=True, stdout=True)
    def save(self, images=True) -> None:
        """flush changes in the project to disk

        (writes path_classes and project data)
        """
        if self._readonly:
            raise OSError("project in readonly mode")
        if images:
            for entry in self.images:
                entry.save()
        try:
            self.java_object.syncChanges()
        # convert java land exception
        except IOException:  # pragma: no cover
            raise OSError("occurred when trying to save the project")

    @property
    def name(self) -> str:
        """project name"""
        name = str(self.java_object.getName())
        if name.endswith("/project.qpproj"):
            name = name[:-15]
        return name

    def __repr__(self) -> str:
        # name = self.java_object.getNameFromURI(self.java_object.getURI())
        return f'{type(self).__name__}(path="{self._path}" mode="{self._mode}")'

    def _repr_html_(self) -> str:
        from paquo._repr import br
        from paquo._repr import div
        from paquo._repr import h3
        from paquo._repr import p
        from paquo._repr import repr_html
        from paquo._repr import span
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
        if not self._readonly:
            self.save()
