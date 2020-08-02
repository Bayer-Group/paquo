import os
import platform
import re
from distutils.version import LooseVersion
from itertools import chain
from pathlib import Path
from typing import Tuple, List, Optional, Callable, Union, Iterable, Any, Dict

import jpype

# types
PathOrStr = Union[Path, str]
QuPathJVMInfo = Tuple[Path, Path, Path, List[str]]

__all__ = ["JClass", "start_jvm"]

JClass = jpype.JClass


def find_qupath(*,
                qupath_dir: PathOrStr = None,
                qupath_search_dirs: Union[PathOrStr, List[PathOrStr]] = None,
                qupath_search_dir_regex: str = None,
                qupath_search_conda: bool = None,
                qupath_prefer_conda: bool = None,
                java_opts: List[str] = None,
                **_kwargs) -> QuPathJVMInfo:
    """find current qupath installation and jvm paths/options

    For now this supports a qupath which ships its own JRE installation
    and was installed via `conda install -c sdvillal qupath`

    Returns
    -------
    qupath_jvm_info:
        a tuple (app_dir, runtime_dir, jvm_path, jvm_options)
    """
    if qupath_dir:
        # short circuit in case we provide a qupath_dir
        # --> when qupath_dir is provided, search is disabled
        if isinstance(qupath_dir, str):
            qupath_dir = Path(qupath_dir)
        if java_opts is None:
            java_opts = []
        return qupath_jvm_info_from_qupath_dir(qupath_dir, java_opts)

    if qupath_search_dirs is None:
        qupath_search_dirs = []
    if not isinstance(qupath_search_dirs, list):
        qupath_search_dirs = [qupath_search_dirs]
    qupath_search_dirs = _scan_qupath_dirs(qupath_search_dirs, qupath_search_dir_regex)

    if qupath_search_conda:
        conda_search_dir = [_conda_qupath_dir()]
        if qupath_prefer_conda:
            qupath_search_dirs = chain(conda_search_dir, qupath_search_dirs)
        else:
            qupath_search_dirs = chain(qupath_search_dirs, conda_search_dir)

    for qupath_dir in qupath_search_dirs:
        if qupath_dir is None:
            continue
        try:
            return qupath_jvm_info_from_qupath_dir(qupath_dir, java_opts)
        except FileNotFoundError:
            continue
    else:
        raise ValueError("no valid qupath installation found")


def _scan_qupath_dirs(qupath_search_dirs: List[PathOrStr], qupath_search_dir_regex: str) -> Iterable[Path]:
    """return potential paths for QuPath"""
    qp_match = re.compile(qupath_search_dir_regex).match
    for location in map(Path, qupath_search_dirs):
        if not location.is_dir():
            continue
        with os.scandir(location.absolute()) as it:
            for dir_entry in sorted(it, key=lambda x: x.name.lower(), reverse=True):
                if dir_entry.is_dir() and qp_match(dir_entry.name):
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
        else:  # pragma: no cover
            raise ValueError(f'Unknown platform {system}')
    return None


def qupath_jvm_info_from_qupath_dir(qupath_dir: Path, jvm_options: List[str]) -> QuPathJVMInfo:
    """convert qupath_dir to paths according to platform"""
    system = platform.system()
    if system == "Linux":
        app_dir = qupath_dir / "lib" / "app"
        runtime_dir = qupath_dir / "lib" / "runtime"
        jvm_dir = runtime_dir / "lib" / "server" / "libjvm.so"

    elif system == "Darwin":
        app_dir = qupath_dir / "Contents" / "app"
        runtime_dir = qupath_dir / "Contents" / "runtime" / "Contents" / "Home"
        jvm_dir = runtime_dir / "lib" / "libjli.dylib"  # not server/libjvm.dylib

    elif system == "Windows":
        app_dir = qupath_dir / "app"
        runtime_dir = qupath_dir / "runtime"
        jvm_dir = runtime_dir / "bin" / "server" / "jvm.dll"

    else:  # pragma: no cover
        raise ValueError(f'Unknown platform {system}')

    # verify that paths are sane
    if not (app_dir.is_dir() and runtime_dir.is_dir() and jvm_dir.is_file()):
        raise FileNotFoundError('qupath installation is incompatible')

    # note: jvm_options is just passed through
    #   but this is the best place to have os-specific jvm_options modifications
    #   in case it's needed at some point
    return app_dir, runtime_dir, jvm_dir, jvm_options


# stores qupath version to handle consecutive calls to start_jvm
_QUPATH_VERSION: Optional[LooseVersion] = None


def start_jvm(finder: Optional[Callable[..., QuPathJVMInfo]] = None,
              finder_kwargs: Optional[Dict[str, Any]] = None) -> Optional[LooseVersion]:
    """start the jvm via jpype

    This is automatically called at import of `paquo.java`.
    """
    global _QUPATH_VERSION

    if jpype.isJVMStarted():
        return _QUPATH_VERSION  # nothing to be done

    if finder is None:
        finder = find_qupath

    # For the time being, we assume qupath is our JVM of choice
    app_dir, runtime_dir, jvm_path, jvm_options = finder(**finder_kwargs)
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
