import json
import pathlib
import re
import weakref
from abc import ABC
from abc import abstractmethod
from collections.abc import Hashable
from collections.abc import MutableMapping
from copy import deepcopy
from enum import Enum
from pathlib import Path
from pathlib import PurePath
from pathlib import PurePosixPath
from pathlib import PureWindowsPath
from typing import Any
from typing import Dict
from typing import Iterator
from typing import List
from typing import Optional
from typing import TYPE_CHECKING
from typing import Union

from paquo._logging import get_logger
from paquo._logging import redirect
from paquo._utils import cached_property
from paquo.hierarchy import QuPathPathObjectHierarchy
from paquo.java import BufferedImage
from paquo.java import DefaultProjectImageEntry
from paquo.java import File
from paquo.java import FileNotFoundException
from paquo.java import IOException
from paquo.java import ImageType
from paquo.java import NoSuchFileException
from paquo.java import PathIO
from paquo.java import String
from paquo.java import URI
from paquo.java import URISyntaxException

if TYPE_CHECKING:
    import paquo.projects

_log = get_logger(__name__)


# [URI:java-python]
# NOTE: pathlib handles URIs a little different to QuPath's java URIs
#   having looked into it a little bit it seems neither are entirely
#   rfc3986 compliant because they both try to be permissive with
#   broken URIs...
#   For the sake of moving forward we go with the workarounds below.
#   This should all be replaced with rfc3986 compliant URI handling.
def _normalize_pathlib_uris(uri):
    """this will correctly unescape and normalize uri's received from pathlib.Path.as_uri()"""
    # https://docs.oracle.com/javase/7/docs/api/java/net/URI.html section Identities
    u = URI(uri)
    return URI(
        u.getScheme(),
        u.getUserInfo(),
        u.getHost(),
        u.getPort(),
        u.getPath(),
        u.getQuery(),
        u.getFragment()
    )


class ImageProvider(ABC):
    """Maps image ids to paths and paths to image ids."""

    @abstractmethod
    def uri(self, image_id: Hashable) -> Optional[str]:
        """Returns an URI for an image given an image id tuple."""
        # default implementation:
        # -> null uri
        return None

    @abstractmethod
    def id(self, uri: str) -> Hashable:
        """Returns an image id given an URI."""
        # default implementation:
        # -> return filename as image id
        return ImageProvider.path_from_uri(uri).name

    @abstractmethod
    def rebase(self, *uris: str, **kwargs) -> List[Optional[str]]:
        """Allows rebasing"""
        return [self.uri(self.id(uri)) for uri in uris]

    @staticmethod
    def path_from_uri(uri: str) -> PurePath:
        """
        Parses an URI representing a file system path into a Path.
        """
        # TODO: needs way more tests... See note [URI:java-python]
        try:
            java_uri = URI(uri)
        except URISyntaxException:
            raise ValueError(f"not a valid uri '{uri}'")
        # test current scheme support
        if str(java_uri.getScheme()) != "file":
            raise NotImplementedError("paquo only supports file:/ URIs as of now")
        else:
            path_str = str(java_uri.getPath())
        # fixme: this should be replaced with something more reliable...
        # check if we encode a windows path
        if re.match(r"/[A-Z]:/[^/]", path_str):
            return PureWindowsPath(path_str[1:])
        elif re.match(r"//(?P<share>[^/]+)/(?P<directory>[^/]+)/", path_str):
            return PureWindowsPath(path_str)
        else:
            return PurePosixPath(path_str)

    @staticmethod
    def uri_from_path(path: PurePath) -> str:
        """
        Convert a python path object to an URI
        """
        # TODO: needs way more tests... See note [URI:java-python]
        if not path.is_absolute():
            raise ValueError("uri_from_path requires an absolute path")
        java_uri = str(_normalize_pathlib_uris(path.as_uri()).toString())
        # fixme: this should be replaced with a rfc3896 compliant solution...
        if re.match("file://([^/]|$)", java_uri):
            uri = f"file:////{java_uri[7:]}"  # network shares have redundant authority on the java side
        # vvv this would only be required if we wouldn't normalize the uri like above
        # elif re.match("file:///([^/]|$)", java_uri):
        #     uri = f"file:/{java_uri[8:]}"  # the local windows absolute paths don't
        else:
            uri = java_uri
        return uri

    @staticmethod
    def compare_uris(a: str, b: str) -> bool:
        """
        Test if two URIs point two the same resource
        """
        # TODO: needs way more tests... See note [URI:java-python]
        uri_a = _normalize_pathlib_uris(a)
        uri_b = _normalize_pathlib_uris(b)
        return bool(uri_a.equals(uri_b))

    @classmethod
    def __subclasshook__(cls, C):
        """ImageProviders don't need to derive but only duck-type"""
        required_methods = ('uri', 'id', 'rebase')
        if cls is ImageProvider:
            methods_available = [False] * len(required_methods)
            for B in C.__mro__:
                for idx, method in enumerate(required_methods):
                    methods_available[idx] |= method in B.__dict__
                if all(methods_available):
                    return True
        return NotImplemented


SimpleFileImageId = Union[str, pathlib.Path]


# noinspection PyMethodMayBeStatic
class SimpleURIImageProvider:
    """simple image provider that uses the files uri as it's identifier"""

    class FilenamePathId(str):
        """an id that uses the filename as it's identifier"""
        def __eq__(self, other):
            return Path(self).name == Path(other).name

        def __hash__(self):
            return hash(Path(self).name)

        def __repr__(self):  # pragma: no cover
            p = Path(self)
            return f'FilenamePathId("{p.name}", parent="{p.parent}")'

    class URIString(str):
        """string uri's can differ in their string representation and still be identical"""
        # we need some way to normalize uris
        def __eq__(self, other):  # pragma: no cover
            return ImageProvider.compare_uris(self, other)
        __hash__ = str.__hash__  # fixme: this is not correct!

    def uri(self, image_id: SimpleFileImageId) -> Optional['URIString']:
        """accepts a path and returns a URIString"""
        if not isinstance(image_id, (Path, str, SimpleURIImageProvider.FilenamePathId)):
            raise TypeError("image_id not of correct format")  # pragma: no cover
        img_path = pathlib.Path(image_id).absolute().resolve()
        if not img_path.is_file():
            return None
        return SimpleURIImageProvider.URIString(img_path.as_uri())

    def id(self, uri: URIString) -> str:
        """accepts a uri string and returns a FilenamePathId"""
        if not isinstance(uri, (str, SimpleURIImageProvider.URIString)):
            raise TypeError("uri not of correct format")  # pragma: no cover
        return SimpleURIImageProvider.FilenamePathId(ImageProvider.path_from_uri(uri))

    def rebase(self, *uris: str, **kwargs) -> List[Optional[str]]:
        uri2uri = kwargs.pop('uri2uri', {})
        return [uri2uri.get(uri, None) for uri in uris]


# noinspection PyPep8Naming
class _RecoveredReadOnlyImageServer:
    """internal. used to allow access to image server metadata recovered from project.qpproj"""

    # noinspection PyMethodParameters,PyPep8Naming
    class _FakeResolutionLevel:
        def __init__(self_, _lvl):
            self_._lvl = _lvl

        def getDownsample(self_):
            return self_._lvl['downsample']

        def getHeight(self_):
            return self_._lvl['height']

        def getWidth(self_):
            return self_._lvl['width']

    # noinspection PyMethodParameters,PyPep8Naming
    class _FakeMetadata:
        def __init__(self_, _metadata):
            self_._md = _metadata

        def nLevels(self_):
            return len(self_._md.get('levels', []))

        def getLevel(self_, idx):
            _rl = self_._md.get('levels')[idx]
            # noinspection PyProtectedMember
            return _RecoveredReadOnlyImageServer._FakeResolutionLevel(_rl)

    def __init__(self, entry_path: Path):
        server_json_f = Path(entry_path) / "server.json"
        with server_json_f.open('r') as f:
            self._metadata = json.load(f).get('metadata', {})

    def getWidth(self):
        return self._metadata['width']

    def getHeight(self):
        return self._metadata['height']

    def nChannels(self):
        return len(self._metadata['channels'])

    def nZSlices(self):
        return self._metadata['sizeZ']

    def nTimepoints(self):
        return self._metadata['sizeT']

    def getMetadata(self) -> Any:
        # fake the java metadata interface
        _md = deepcopy(self._metadata)
        # noinspection PyProtectedMember
        return _RecoveredReadOnlyImageServer._FakeMetadata(_md)


class _ProjectImageEntryMetadata(MutableMapping):
    """provides a python dict interface for image entry metadata"""

    def __init__(self, image: 'QuPathProjectImageEntry') -> None:
        self._image = image
        self._entry = image.java_object

    def __setitem__(self, k: str, v: str) -> None:
        # noinspection PyProtectedMember
        if self._image._readonly:
            raise AttributeError("project in readonly mode")
        if not isinstance(k, str):
            raise TypeError(f"key must be of type `str` got `{type(k)}`")
        if not isinstance(v, str):
            raise TypeError(f"value must be of type `str` got `{type(v)}`")
        self._entry.putMetadataValue(String(str(k)), String(str(v)))

    def __delitem__(self, k: str) -> None:
        # noinspection PyProtectedMember
        if self._image._readonly:
            raise AttributeError("project in readonly mode")
        if not isinstance(k, str):
            raise TypeError(f"key must be of type `str` got `{type(k)}`")
        self._entry.removeMetadataValue(String(str(k)))

    def __getitem__(self, k: str) -> str:
        if not isinstance(k, str):
            raise TypeError(f"key must be of type `str` got `{type(k)}`")
        v = self._entry.getMetadataValue(String(str(k)))
        if v is None:
            raise KeyError(f"'{k}' not in metadata")
        return str(v)

    def __len__(self) -> int:
        return int(self._entry.getMetadataKeys().size())

    def __iter__(self) -> Iterator[str]:
        return iter(map(str, self._entry.getMetadataKeys()))

    def __contains__(self, item):
        return bool(self._entry.containsMetadata(String(str(item))))

    def clear(self) -> None:
        # noinspection PyProtectedMember
        if self._image._readonly:
            raise AttributeError("project in readonly mode")
        self._entry.clearMetadata()

    def __repr__(self):
        return f"Metadata({repr(dict(self))})"


class _ImageDataProperties(MutableMapping):
    """provides a python dict interface for image data properties"""

    def __init__(self, image: 'QuPathProjectImageEntry') -> None:
        self._image = image
        # noinspection PyProtectedMember
        self._image_data = image._image_data

    def __setitem__(self, k: str, v: Any) -> None:
        # noinspection PyProtectedMember
        if self._image._readonly:
            raise AttributeError("project in readonly mode")
        if not isinstance(k, str):
            raise TypeError(f"key must be of type `str` got `{type(k)}`")
        self._image_data.setProperty(String(k), v)

    def __delitem__(self, k: str) -> None:
        # noinspection PyProtectedMember
        if self._image._readonly:
            raise AttributeError("project in readonly mode")
        if not isinstance(k, str):
            raise TypeError(f"key must be of type `str` got `{type(k)}`")
        self._image_data.removeProperty(String(k))

    def __getitem__(self, k: str) -> Any:
        if not isinstance(k, str):
            raise TypeError(f"key must be of type `str` got `{type(k)}`")
        if k not in self:
            raise KeyError(f"'{k}' not in metadata")
        v = self._image_data.getProperty(String(k))
        return v

    def __contains__(self, item: Any) -> bool:
        if not isinstance(item, str):
            return False
        return bool(
            self._image_data.getProperties().containsKey(String(item))
        )

    def __len__(self) -> int:
        return int(self._image_data.getProperties().size())

    def __iter__(self) -> Iterator[str]:
        return iter(map(str, dict(self._image_data.getProperties())))

    def __repr__(self):
        return f"Properties({repr(dict(self))})"


# note: this could just be autogenerated by inspecting the ImageType
#   but it's better to be explicit so that all values are defined here
class QuPathImageType(str, Enum):
    """Enum representing image types"""
    java_enum: ImageType

    def __new__(cls, value: str, java_enum: ImageType):
        # noinspection PyArgumentList
        obj = super().__new__(cls, value)
        obj._value_ = value
        obj.java_enum = java_enum
        return obj

    @classmethod
    def from_java(cls, java_enum) -> 'QuPathImageType':
        """internal for converting from java to python"""
        for value in cls.__members__.values():
            if value.java_enum == java_enum:
                return value
        raise ValueError("unsupported java_enum")  # pragma: no cover

    # Brightfield image with hematoxylin and DAB stains.
    BRIGHTFIELD_H_DAB = ("Brightfield (H-DAB)", ImageType.BRIGHTFIELD_H_DAB)
    # Brightfield image with hematoxylin and eosin stains.
    BRIGHTFIELD_H_E = ("Brightfield (H&E)", ImageType.BRIGHTFIELD_H_E)
    # Brightfield image with any stains.
    BRIGHTFIELD_OTHER = ("Brightfield (other)", ImageType.BRIGHTFIELD_OTHER)
    # Fluorescence image.
    FLUORESCENCE = ("Fluorescence", ImageType.FLUORESCENCE)
    # Other image type, not covered by any of the alternatives above.
    OTHER = ("Other", ImageType.OTHER)
    # Image type has not been set.
    UNSET = ("Not set", ImageType.UNSET)


class QuPathProjectImageEntry:
    java_object: DefaultProjectImageEntry

    def __init__(self, entry: DefaultProjectImageEntry,
                 *, _project_ref: Optional['paquo.projects.QuPathProject'] = None) -> None:
        """Wrapper for qupath image entries

        this is normally not instantiated by the user
        """
        if not isinstance(entry, DefaultProjectImageEntry):
            raise ValueError("don't instantiate directly. use `QuPathProject.add_image`")
        self.java_object = entry
        self._project_ref = weakref.ref(_project_ref) if _project_ref else lambda: None
        self._metadata = _ProjectImageEntryMetadata(self)

    @property
    def _readonly(self):
        p = self._project_ref()
        return getattr(p, "_readonly", False) if p else True

    @cached_property
    def _image_data(self):
        with redirect(stdout=True, stderr=True):
            try:
                return self.java_object.readImageData()
            # from java land
            except IOException:  # pragma: no cover
                image_data_fn = self.entry_path / "data.qpdata"
                try:
                    image_data = PathIO.readImageData(
                        File(str(image_data_fn)),
                        None, None, BufferedImage
                    )
                except (FileNotFoundException, NoSuchFileException):
                    raise FileNotFoundError("image_data missing")
                return image_data

    @cached_property
    def _properties(self):
        return _ImageDataProperties(self)

    @cached_property
    def _image_server(self):
        server = self._image_data.getServer()
        if not server:
            _log.warning("recovering readonly from server.json")
            server = _RecoveredReadOnlyImageServer(self.entry_path)
        return server

    @property
    def entry_id(self) -> str:
        """the unique image entry id"""
        return str(self.java_object.getID())

    @property
    def entry_path(self) -> Path:
        """path to the image directory"""
        return Path(str(self.java_object.getEntryPath().toString()))

    @property
    def image_name(self) -> str:
        """the image entry name"""
        return str(self.java_object.getImageName())

    @image_name.setter
    def image_name(self, name: str) -> None:
        if self._readonly:
            raise AttributeError("project in readonly mode")
        self.java_object.setImageName(String(name))

    # remove until there's a good use case for this...
    # @property
    # def image_name_original(self) -> Optional[str]:
    #     """original name in case the user has changed the image name"""
    #     org_name = self.java_object.getOriginalImageName()
    #     return str(org_name) if org_name else None

    @property
    def image_type(self) -> QuPathImageType:
        """image type"""
        return QuPathImageType.from_java(self._image_data.getImageType())

    @image_type.setter
    def image_type(self, value: QuPathImageType) -> None:
        if self._readonly:
            raise AttributeError("project in readonly mode")
        if not isinstance(value, QuPathImageType):
            raise TypeError("requires a QuPathImageType enum")
        self._image_data.setImageType(value.java_enum)

    @property
    def description(self) -> str:
        """free text describing the image"""
        text = self.java_object.getDescription()
        if text is None:
            return ""
        return str(text)

    @description.setter
    def description(self, text: str) -> None:
        if self._readonly:
            raise AttributeError("project in readonly mode")
        self.java_object.setDescription(text)

    @property
    def width(self):
        """image width in pixels"""
        return int(self._image_server.getWidth())

    @property
    def height(self):
        """image height in pixels"""
        return int(self._image_server.getHeight())

    @property
    def num_channels(self):
        """number of channels in the image"""
        return int(self._image_server.nChannels())

    @property
    def num_z_slices(self):
        """number of z_slices in the image"""
        return int(self._image_server.nZSlices())

    @property
    def num_timepoints(self):
        """number of time points in the image"""
        return int(self._image_server.nTimepoints())

    @cached_property
    def downsample_levels(self) -> List[Dict[str, float]]:
        """downsample levels provided by the image

        Notes
        -----
        The available downsample levels can differ dependent
        on which image backend is used by QuPath
        """
        md = self._image_server.getMetadata()
        levels = []
        for level in range(int(md.nLevels())):
            resolution_level = md.getLevel(level)
            levels.append({
                'downsample': float(resolution_level.getDownsample()),
                'width': int(resolution_level.getWidth()),
                'height': int(resolution_level.getHeight()),
            })
        return levels

    @property
    def metadata(self) -> _ProjectImageEntryMetadata:
        """the metadata stored on the image as dict-like proxy"""
        return self._metadata

    @metadata.setter
    def metadata(self, value: dict) -> None:
        if self._readonly:
            raise AttributeError("project in readonly mode")
        self._metadata.clear()
        self._metadata.update(value)

    @property
    def properties(self):
        """the properties stored in the image data as a dict-like proxy"""
        return self._properties

    @properties.setter
    def properties(self, value):
        if self._readonly:
            raise AttributeError("project in readonly mode")
        self._properties.clear()
        self._properties.update(value)

    @cached_property
    def hierarchy(self) -> QuPathPathObjectHierarchy:
        """the image entry hierarchy. it contains all annotations"""
        try:
            h = self._image_data.getHierarchy()
        except OSError:
            _log.warning("could not open image data. loading annotation hierarchy from project.")
            h = self.java_object.readHierarchy()

        return QuPathPathObjectHierarchy(h, readonly=self._readonly, image_name=self.image_name)

    def __repr__(self):
        return f"ImageEntry(image_name='{self.image_name}')"

    def _repr_html_(self, compact=False, index=0):
        from base64 import b64encode
        from paquo._repr import br, h4, img, div, p, span

        img_css = {
            "max-width": "100px",
            "max-height": "100px",
            "border": "1px solid",
            "margin": "auto",
        }
        header_css = {
            "position": "absolute",
            "top": "-1.6em",
            "width": "100px",
            "overflow": "hidden",
            "text-overflow": "ellipsis",
            "font-size": "0.75em",
        }
        container_css = {
            "display": "flex",
            "align-items": "center",
            "justify-content": "center",
            "position": "relative",
            "width": "100px",
            "height": "100px",
            "background": "#ddd",
            "margin": "2px",
        }

        try:
            with (self.entry_path / "thumbnail.jpg").open(mode="rb") as f:
                data = b64encode(f.read()).decode('utf-8')
        except FileNotFoundError:  # pragma: no cover
            image = span(style={"font-size": "3em"}, text="?")
        else:
            image = img(title=self.image_name,
                        src=f"data:image/jpeg;base64,{data}",
                        style=img_css)
        if compact:
            container_css["margin-top"] = "1em"
            return div(
                span(text=f"[{index}]\xa0{self.image_name}", style=header_css),
                image,
                style=container_css
            )

        try:
            uri = self.uri[5:]
        except RuntimeError as err:  # pragma: no cover
            uri = f"N/A ({err})"
        return div(
            h4(text=f"Image: {self.image_name}", style={"margin-top": "0"}),
            p(
                span(text="path: ", style={"font-weight": "bold"}),
                span(text=uri),
                br(),
                span(text="type: ", style={"font-weight": "bold"}),
                span(text=str(self.image_type.value)),
                style={"margin": "0.5em"},
            ),
            div(
                image,
                style=container_css,
            )
        )

    @property
    def uri(self):
        """the image entry uri"""
        uris = self.java_object.getServerURIs()
        if len(uris) == 0:
            raise RuntimeError("no server")  # pragma: no cover
        elif len(uris) > 1:
            raise NotImplementedError("unsupported in paquo as of now")
        return str(uris[0].toString())

    def is_readable(self) -> bool:
        """check if the image file is readable"""
        concrete_path = Path(ImageProvider.path_from_uri(self.uri))
        return concrete_path.is_file()

    def is_changed(self) -> bool:
        """check if image_data is changed

        Raises
        ------
        IOError
            if image_data can't be read

        """
        return bool(self._image_data.isChanged())

    def save(self):
        """save image entry"""
        with redirect(stdout=True, stderr=True):
            if self._readonly:
                raise IOError("project in readonly mode")
            if self.is_readable():
                if self.is_changed():
                    self.java_object.saveImageData(self._image_data)
                    _log.info(f"Changes saved for '{self.image_name}'")
                else:
                    _log.info(f"Saving skipped for '{self.image_name}': no changes")
            else:
                _log.warning(f"Saving skipped for '{self.image_name}': uri '{self.uri}' not reachable")
