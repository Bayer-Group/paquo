import pathlib
from collections.abc import MutableMapping
from typing import Iterator

from paquo.objects.hierarchy import PathObjectHierarchy
from paquo.qupath.jpype_backend import java_import, jvm_running

# import java classes
with jvm_running():
    _BufferedImage = java_import('java.awt.image.BufferedImage')
    _String = java_import('java.lang.String')
    _DefaultProjectImageEntry = java_import('qupath.lib.projects.DefaultProject.DefaultProjectImageEntry')


class _ProjectImageEntryMetadata(MutableMapping):

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


class ProjectImageEntry:

    def __init__(self, entry):
        if not isinstance(entry, _DefaultProjectImageEntry):
            raise TypeError("don't instantiate ProjectImageEntry yourself")
        self._entry = entry
        self._metadata = _ProjectImageEntryMetadata(entry)
        self._hierarchy = None

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
        self._entry.setThumbnail(value)

    @property
    def metadata(self):
        return self._metadata

    @metadata.setter
    def metadata(self, value):
        self._metadata.clear()
        self._metadata.update(value)

    @property
    def hierarchy(self):
        if self._hierarchy is None:
            self._hierarchy = PathObjectHierarchy(self._entry.readHierarchy())
        return self._hierarchy
