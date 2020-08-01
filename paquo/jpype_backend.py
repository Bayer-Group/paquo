from distutils.version import LooseVersion
import os
import platform
import shlex
import collections.abc as collections_abc
from pathlib import Path
from typing import Tuple, List, Optional, Callable, Union, Iterable, Any

import jpype

# types
PathOrFunc = Union[Path, str, Callable[[], Iterable[Path]], Callable[[], Optional[Path]], None]
QuPathJVMInfo = Tuple[Path, Path, Path, List[str]]

__all__ = ["JClass", "start_jvm", "find_qupath"]

JClass = jpype.JClass


def find_qupath(search_dirs: Union[PathOrFunc, List[PathOrFunc]] = None,
                *,
                search_default_locations: bool = True,
                prefer_conda_qupath: Optional[bool] = True) -> QuPathJVMInfo:
    """find current qupath installation and jvm paths/options

    For now this supports a qupath which ships its own JRE installation
    and was installed via `conda install -c sdvillal qupath`

    Returns
    -------
    qupath_jvm_info:
        a tuple (app_dir, runtime_dir, jvm_path, jvm_options)
    """
    if search_dirs is None:
        search_dirs = []

    if not isinstance(search_dirs, list):
        search_dirs = [search_dirs]

    if search_default_locations:
        search_dirs.append(_default_qupath_dirs)

    if prefer_conda_qupath is not None:
        loc = 0 if prefer_conda_qupath else len(search_dirs)
        search_dirs.insert(loc, _conda_qupath_dir)

    for qupath_dir in _iter_nested_paths(search_dirs):
        try:
            return qupath_jvm_info_from_qupath_dir(qupath_dir)
        except FileNotFoundError:
            continue
    else:
        raise ValueError("no valid qupath installation found")


def _iter_nested_paths(paths: Any) -> Iterable[Path]:
    """iterate lists of paths and callables that return paths or lists of paths

    this helper returns a flat iterator of pathlib.Paths
    """
    if callable(paths):
        paths = paths()
    if isinstance(paths, str):
        yield Path(paths)  # single path
    elif isinstance(paths, Path):
        yield paths
    elif paths is None:
        return
    elif isinstance(paths, collections_abc.Iterable):
        for p in paths:
            yield from _iter_nested_paths(p)
    else:
        raise ValueError(f"unsupported value '{paths}'")


def _default_qupath_dirs() -> Iterable[Path]:
    """return default search paths for QuPath"""
    # todo: this needs to be configurable via config files (dynaconf?)
    system = platform.system()
    locations: List[Union[str, Path]]
    if system == "Linux":
        locations = ["/opt", "/usr/local", Path.home()]
        def match(x): return x.startswith("qupath")
    elif system == "Darwin":
        locations = ["/opt", "/Applications", Path.home() / "Applications", Path.home()]
        def match(x): return x.startswith("qupath") and x.endswith('.app')
    elif system == "Windows":
        locations = ["c:/Program Files/", Path.home() / "AppData" / "Local"]
        def match(x): return x.startswith("qupath")
    else:
        raise ValueError(f'Unknown platform {system}')

    for location in map(Path, locations):
        if not location.is_dir():
            continue
        # noinspection PyTypeChecker
        with os.scandir(location.absolute()) as it:
            for dir_entry in sorted(it, key=lambda x: x.name.lower(), reverse=True):
                if dir_entry.is_dir() and match(dir_entry.name.lower()):
                    yield Path(dir_entry.path)


def _conda_qupath_dir() -> Optional[Path]:
    """return the conda qupath if running in a conda env"""
    prefix = os.environ.get('CONDA_PREFIX')
    if prefix:
        system = platform.system()
        if system == "Linux":
            return Path(prefix) / "opt" / "QuPath"
        elif system == "Darwin":
            return Path(prefix) / "bin" / "QuPath.app"
        elif system == "Windows":
            return Path(prefix) / "Library" / "QuPath"
        else:
            raise ValueError(f'Unknown platform {system}')
    return None


def qupath_jvm_info_from_qupath_dir(qupath_dir: Path) -> QuPathJVMInfo:
    """convert qupath_dir to paths according to platform"""
    system = platform.system()
    if system == "Linux":
        app_dir = qupath_dir / "lib" / "app"
        runtime_dir = qupath_dir / "lib" / "runtime"
        jvm_dir = runtime_dir / "lib" / "server" / "libjvm.so"
        jvm_options = []

    elif system == "Darwin":
        app_dir = qupath_dir / "Contents" / "app"
        runtime_dir = qupath_dir / "Contents" / "runtime" / "Contents" / "Home"
        jvm_dir = runtime_dir / "lib" / "libjli.dylib"  # not server/libjvm.dylib
        jvm_options = [
            f'-Djava.library.path={app_dir}:{qupath_dir}/Contents/MacOS',
            f'-Djava.launcher.path={qupath_dir}/Contents/MacOS',
        ]

    elif system == "Windows":
        app_dir = qupath_dir / "app"
        runtime_dir = qupath_dir / "runtime"
        jvm_dir = runtime_dir / "bin" / "server" / "jvm.dll"
        jvm_options = []

    else:
        raise ValueError(f'Unknown platform {system}')

    # verify that paths are sane
    if not (app_dir.is_dir() and runtime_dir.is_dir() and jvm_dir.is_file()):
        raise FileNotFoundError('qupath installation is incompatible')

    # append JAVA_OPTS env
    java_opts = os.environ.get('JAVA_OPTS')
    if java_opts:
        jvm_options.extend(shlex.split(java_opts))

    return app_dir, runtime_dir, jvm_dir, jvm_options


# stores qupath version to handle consecutive calls to start_jvm
_QUPATH_VERSION: Optional[LooseVersion] = None


def start_jvm(finder: Optional[Callable[[], QuPathJVMInfo]] = None) -> Optional[LooseVersion]:
    """start the jvm via jpype

    This is automatically called at import of `paquo.java`.
    """
    global _QUPATH_VERSION

    if jpype.isJVMStarted():
        return _QUPATH_VERSION  # nothing to be done

    if finder is None:
        finder = find_qupath

    # For the time being, we assume qupath is our JVM of choice
    app_dir, runtime_dir, jvm_path, jvm_options = finder()
    # This is not really needed, but beware we might need SL4J classes (see warning)
    jpype.addClassPath(str(app_dir / '*'))
    jpype.startJVM(str(jvm_path), *jvm_options, convertStrings=False)

    # we'll do this explicitly here to verify the QuPath version
    try:
        _version = str(JClass("qupath.lib.common.GeneralTools").getVersion())
    except (TypeError, AttributeError):
        version = _QUPATH_VERSION = None
    else:
        version = _QUPATH_VERSION = LooseVersion(_version)
    return version
