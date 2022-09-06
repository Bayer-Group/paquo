import json
import lzma
import os
import platform
import re
import shutil
import ssl
import subprocess
import sys
import tarfile
import tempfile
import warnings
import zipfile
from datetime import datetime
from functools import partial
from functools import total_ordering
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import urlopen
from warnings import warn

from packaging.version import Version

__all__ = [
    'QuPathVersion',
    'cached_property',
    'make_backup_filename',
    'load_json_from_path'
]


if sys.version_info >= (3, 8):
    from functools import cached_property as _cached_property

    # noinspection PyPep8Naming
    class cached_property(_cached_property):
        def __set__(self, obj, value):
            raise AttributeError(f"readonly attribute {self.attrname}")
else:
    # noinspection PyPep8Naming
    class cached_property:
        _NOCACHE = object()

        def __init__(self, fget):
            self.fget = fget
            self.attrname = None
            self.__doc__ = fget.__doc__

        def __set_name__(self, owner, name):
            self.attrname = name

        def __get__(self, obj, objtype=None):
            if obj is None:
                return self  # pragma: no cover
            cache = obj.__dict__
            val = cache.get(self.attrname, self._NOCACHE)
            if val is self._NOCACHE:
                val = cache[self.attrname] = self.fget(obj)
            return val

        def __set__(self, obj, value):
            raise AttributeError(f"readonly attribute {self.fget.__name__}")


@total_ordering
class QuPathVersion:
    """Handle the QuPath version strings"""
    def __init__(self, version: str) -> None:
        self.origin = ver_str = str(version).strip()
        # to not having to rely on packaging.version.LegacyVersion
        # we replace the milestone versioning with -devNN
        ver_str = re.sub(r"(?:-)m(?P<num>[0-9]+)", r"dev\g<num>", ver_str, count=1)
        # to allow running snapshot versions we replace the suffix
        # with a local version
        ver_str = ver_str.replace("-SNAPSHOT", "+snapshot")
        self.version = Version(ver_str)

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.origin!r})"

    def __str__(self) -> str:
        return self.origin

    def __eq__(self, other) -> bool:
        if isinstance(other, QuPathVersion):
            return self.version.__eq__(other.version)
        else:
            return self.version.__eq__(other)

    def __lt__(self, other) -> bool:
        if isinstance(other, QuPathVersion):
            return self.version.__lt__(other.version)
        else:
            return self.version.__lt__(other)


def make_backup_filename(path, name, suffix='backup'):
    path = Path(path)
    if not path.is_dir():
        raise ValueError("requires a directory")  # pragma: no cover
    now = datetime.now().strftime('%Y%m%d-%H%M%S')
    backup = path / f"{name}-{now}.{suffix}"
    if backup.is_file():
        raise RuntimeError(f"the file {backup} should not exist!")  # pragma: no cover
    return backup


def load_json_from_path(path):
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(str(path))  # pragma: no cover

    if path.name.endswith(".geojson.xz"):
        ctx = partial(lzma.open, path, 'rt')
    elif path.name.endswith(('.geojson', '.json')):
        ctx = partial(path.open, 'r')
    else:
        raise NotImplementedError(f"unsupported file format '{path}'")

    with ctx() as fobj:
        data = json.load(fobj)

    if isinstance(data, dict):
        return data
    elif isinstance(data, list):
        return {'annotations': data}
    else:
        raise ValueError("expected dict or list of annotations")


def download_qupath(
    version,
    path,
    *,
    system=None,
    callback=(lambda chunk_iter, name: chunk_iter),
    ssl_verify=True
):
    """download qupath from github"""
    if system is None:
        system = platform.system()

    if system == "Linux":
        _sys = "Linux"
        ext = "tar.xz"
    elif system == "Darwin":
        _sys = "Mac"
        ext = "pkg"
    elif system == "Windows":
        _sys = "Windows"
        ext = "zip"
    else:
        raise ValueError(f"unsupported platform.system() == {system!r}")

    if "rc" not in version:
        name = f"QuPath-{version}-{_sys}"
    else:
        name = f"QuPath-{version}"

    url = f"https://github.com/qupath/qupath/releases/download/v{version}/{name}.{ext}"

    chunk_size = 10 * 1024 * 1024

    fn = os.path.basename(urlsplit(url).path)
    out_fn = os.path.join(path, fn)
    if os.path.exists(out_fn):
        return out_fn

    if ssl_verify:
        _ctx = None
    else:
        warn(f"DISABLING SSL VERIFICATION FOR: {url}", stacklevel=2)
        _ctx = ssl.create_default_context()
        _ctx.check_hostname = False
        _ctx.verify_mode = ssl.CERT_NONE

    try:
        with open(out_fn, mode="wb") as tmp, urlopen(url, context=_ctx) as f:  # nosec B310
            for chunk in callback(iter(lambda: f.read(chunk_size), b""), name=url):
                tmp.write(chunk)
    except Exception:
        try:
            os.unlink(out_fn)
        except OSError:
            pass
        raise
    else:
        return out_fn


def extract_qupath(file, destination, system=None):
    """extract downloaded QuPath file to a destination"""
    fn = os.path.basename(file)

    # normalize QuPath App dirname
    m = re.match(
        r"QuPath-(?P<version>[0-9]+[.][0-9]+[.][0-9]+(-rc[0-9]+|-m[0-9]+)?)",
        fn,
    )

    if system is None:
        system = platform.system()

    if system in {"Linux", "Windows"}:
        app_dir = f"QuPath-{m.group('version')}"
    elif system == "Darwin":
        app_dir = f"QuPath-{m.group('version')}.app"
    else:
        raise ValueError(f"unsupported platform.system() == {system!r}")

    destination = os.path.abspath(os.path.expanduser(destination))
    if not os.path.isdir(destination):
        raise ValueError(f"destination: {destination!r} is not a directory")
    qp_dst = os.path.join(destination, app_dir)
    if os.path.isdir(qp_dst):
        warnings.warn(
            f"Skipping! Output directory already exists: {qp_dst!r}",
            stacklevel=2,
        )
        return qp_dst

    if system == "Linux":
        if not os.fspath(file).endswith(".tar.xz"):
            raise ValueError("file does not end with `.tar.xz`")
        with tempfile.TemporaryDirectory() as tmp_dir:
            with tarfile.open(file, mode="r:xz") as tf:
                tf.extractall(tmp_dir)
                for name in os.listdir(tmp_dir):
                    pth = os.path.join(tmp_dir, name)
                    if name.startswith("QuPath") and os.path.isdir(pth):
                        break
                else:
                    raise RuntimeError("no qupath extracted?")
            shutil.move(os.path.join(tmp_dir, name), qp_dst)
        return qp_dst

    elif system == "Darwin":
        if not Path(file).suffix == ".pkg":
            raise ValueError("file does not end with `.pkg`")
        if shutil.which("7z") is None:
            raise RuntimeError("7z is required, run: `brew install p7zip`")

        with tempfile.TemporaryDirectory() as tmp_dir:
            subprocess.run(["7z", "x", os.path.abspath(file)], cwd=tmp_dir, capture_output=True)
            subprocess.run(["7z", "x", "Payload~"], cwd=tmp_dir, capture_output=True)
            for name in os.listdir(tmp_dir):
                if name.startswith("QuPath") and name.endswith(".app"):
                    break
            else:
                raise RuntimeError("no qupath extracted?")
            shutil.move(os.path.join(tmp_dir, name), qp_dst)
        return qp_dst

    elif system == "Windows":
        if not Path(file).suffix == ".zip":
            raise ValueError("file does not end with `.zip`")

        with tempfile.TemporaryDirectory() as tmp_dir:
            with zipfile.ZipFile(file, mode="r") as zf:
                zf.extractall(tmp_dir)
                for name in os.listdir(tmp_dir):
                    pth = os.path.join(tmp_dir, name)
                    if name.startswith("QuPath") and os.path.isdir(pth):
                        break
                else:
                    raise RuntimeError("no qupath extracted?")
            shutil.move(os.path.join(tmp_dir, name), qp_dst)
        return qp_dst

    else:
        raise ValueError(f"unsupported platform.system() == {system!r}")
