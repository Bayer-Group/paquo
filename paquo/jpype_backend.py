import os
import platform
import re
import shlex
import sys
import textwrap
from contextlib import contextmanager
from contextlib import nullcontext
from itertools import chain
from pathlib import Path
from textwrap import dedent
from typing import Any
from typing import Callable
from typing import ContextManager
from typing import Dict
from typing import Iterable
from typing import List
from typing import NamedTuple
from typing import Optional
from typing import Union
from warnings import warn

import jpype

from paquo._utils import QuPathVersion

# types
PathOrStr = Union[Path, str]

__all__ = ["JClass", "start_jvm", "find_qupath"]

JClass = jpype.JClass


class QuPathJVMInfo(NamedTuple):
    app_dir: Path
    runtime_dir: Path
    jvm_path: Path
    jvm_options: List[str]


def find_qupath(*,
                qupath_dir: Optional[PathOrStr] = None,
                qupath_search_dirs: Optional[Union[PathOrStr, List[PathOrStr]]] = None,
                qupath_search_dir_regex: Optional[str] = None,
                qupath_search_conda: Optional[bool] = None,
                qupath_prefer_conda: Optional[bool] = None,
                java_opts: Optional[Union[List[str], str]] = None,
                jvm_path_override: Optional[PathOrStr] = None,
                **_kwargs) -> QuPathJVMInfo:
    """find current qupath installation and jvm paths/options

    For now this supports a qupath which ships its own JRE installation
    and was installed via `conda install -c sdvillal qupath`

    Returns
    -------
    qupath_jvm_info:
        a tuple (app_dir, runtime_dir, jvm_path, jvm_options)
    """
    if java_opts is None:
        java_opts = []
    elif isinstance(java_opts, str):
        java_opts = shlex.split(java_opts)

    if jvm_path_override:
        jvm_path_override = Path(jvm_path_override)
        if not jvm_path_override.exists():
            raise FileNotFoundError(jvm_path_override)
        if jvm_path_override.is_dir():
            raise IsADirectoryError(jvm_path_override)
    else:
        jvm_path_override = None

    if qupath_dir:
        # short circuit in case we provide a qupath_dir
        # --> when qupath_dir is provided, search is disabled
        if isinstance(qupath_dir, str):
            qupath_dir = Path(qupath_dir)
        info = qupath_jvm_info_from_qupath_dir(qupath_dir, java_opts)
        if jvm_path_override:
            return info._replace(jvm_path=jvm_path_override)
        return info

    if qupath_search_dirs is None:
        qupath_search_dirs = []
    if not isinstance(qupath_search_dirs, list):
        qupath_search_dirs = [qupath_search_dirs]
    if qupath_search_dir_regex is None:
        qupath_search_dir_regex = ""  # match everything
    search_dirs = _scan_qupath_dirs(qupath_search_dirs, qupath_search_dir_regex)

    if qupath_search_conda:
        conda_search_dir = _conda_qupath_dir()
        if conda_search_dir is not None:
            if qupath_prefer_conda:
                search_dirs = chain([conda_search_dir], search_dirs)
            else:
                search_dirs = chain(search_dirs, [conda_search_dir])

    for qupath_dir in search_dirs:
        try:
            info = qupath_jvm_info_from_qupath_dir(qupath_dir, java_opts)
        except FileNotFoundError:
            continue
        else:
            if jvm_path_override:
                return info._replace(jvm_path=jvm_path_override)
            return info
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
        jvm_path = runtime_dir / "lib" / "server" / "libjvm.so"

    elif system == "Darwin":
        app_dir = qupath_dir / "Contents" / "app"
        runtime_dir = qupath_dir / "Contents" / "runtime" / "Contents" / "Home"
        jvm_path = runtime_dir / "lib" / "libjli.dylib"  # not server/libjvm.dylib

    elif system == "Windows":
        app_dir = qupath_dir / "app"
        runtime_dir = qupath_dir / "runtime"
        jvm_path = runtime_dir / "bin" / "server" / "jvm.dll"

    else:  # pragma: no cover
        raise ValueError(f'Unknown platform {system}')

    # verify that paths are sane
    if not (app_dir.is_dir() and runtime_dir.is_dir() and jvm_path.is_file()):
        raise FileNotFoundError('qupath installation is incompatible')

    # Add java.library.path so that the qupath provided openslide works
    jvm_options.append(f"-Djava.library.path={app_dir}")
    jvm_options = list(dict.fromkeys(jvm_options))  # keep options unique and in order

    return QuPathJVMInfo(app_dir, runtime_dir, jvm_path, jvm_options)


# stores qupath version to handle consecutive calls to start_jvm
_QUPATH_VERSION: Optional[QuPathVersion] = None


def start_jvm(
    finder: Optional[Callable[..., QuPathJVMInfo]] = None,
    finder_kwargs: Optional[Dict[str, Any]] = None,
) -> Optional[QuPathVersion]:
    """start the jvm via jpype

    This is automatically called at import of `paquo.java`.
    """
    global _QUPATH_VERSION

    if jpype.isJVMStarted():
        return _QUPATH_VERSION  # nothing to be done

    if finder is None:
        finder = find_qupath

    if finder_kwargs is None:
        finder_kwargs = {}  # pragma: no cover

    # For the time being, we assume qupath is our JVM of choice
    app_dir, runtime_dir, jvm_path, jvm_options = finder(**finder_kwargs)

    patched_env: Callable[[], ContextManager[Any]]
    if platform.system() == "Windows":
        # workaround for EXCEPTION_ACCESS_VIOLATION crash
        # see: https://github.com/bayer-science-for-a-better-life/paquo/issues/67
        @contextmanager
        def patched_env():
            _old = os.environ.copy()
            os.environ.update({
                "PATH": f"{os.path.join(runtime_dir, 'bin')}{os.pathsep}{os.environ['PATH']}"
            })
            try:
                yield
            finally:
                os.environ.clear()
                os.environ.update(_old)

        # the above workaround doesn't fix the issue for python versions installed
        # via the Microsoft Store. Let's warn users that this might cause problems
        def is_windows_store_python() -> bool:
            parts = Path(sys.base_exec_prefix).parts
            try:
                idx = parts.index("WindowsApps")
            except ValueError:
                return False
            try:
                return parts[idx + 1].startswith("PythonSoftwareFoundation")
            except IndexError:
                return False

        if finder_kwargs.pop("warn_microsoft_store_python", True) and is_windows_store_python():
            msg = dedent("""\
            MicrosoftStore Python installation detected
            Your Python version seems to be installed via the MicrosoftStore.
            If paquo crashes with a EXCEPTION_ACCESS_VIOLATION try installing Python from https://www.python.org
            To silence this warning set the following in your .paquo.toml configfile:
            >>> warn_microsoft_store_python = false <<<
            """)
            warn(msg, stacklevel=2)

    else:
        patched_env = nullcontext

    # This is not really needed, but beware we might need SL4J classes (see warning)
    jpype.addClassPath(str(app_dir / '*'))

    with patched_env():
        try:
            jpype.startJVM(
                str(jvm_path),
                *jvm_options,
                ignoreUnrecognized=False,
                convertStrings=False
            )
        except OSError as err:
            if (
                err.errno == 0
                and "JVM DLL not found:" in str(err)
                and jvm_path.is_file()
                and platform.uname().machine == "arm64"
            ):
                msg = textwrap.dedent("""\
                Probably a JVM and Python architecture issue on M1:
                You can fix this by running a JVM with the same architecture as your
                Python interpreter. Usually paquo uses the JVM that ships with QuPath,
                but you can override this by setting 'jvm_path_override' in `.paquo.toml`

                In case you are running an arm64 Python interpreter on your mac try
                installing an arm jvm from
                https://www.azul.com/downloads/?version=java-17-lts&os=macos&architecture=arm-64-bit&package=jdk
                ```
                $ cat .paquo.toml
                # use the path to libjli.dylib valid on your machine:
                jvm_path_override = "/Library/Java/JavaVirtualMachines/zulu-17.jdk/Contents/Home/lib/libjli.dylib"
                ```
                If this doesn't work, please open an issue on github.
                """)
                raise RuntimeError(msg) from err
        except RuntimeError as jvm_error:  # pragma: no cover
            # there's a chance that this RuntimeError occurred because a user provided
            # jvm_option is incorrect. let's try if that is the case and crash with a
            # more verbose error message
            try:
                jpype.startJVM(
                    str(jvm_path),
                    *jvm_options,
                    ignoreUnrecognized=True,
                    convertStrings=False
                )
            except RuntimeError:
                raise jvm_error
            else:
                msg = f"Provided JAVA_OPTS prevent the JVM from starting! {jvm_options}"
                exc = RuntimeError(msg)
                exc.__cause__ = jvm_error
                raise exc

    # we'll do this explicitly here to verify the QuPath version
    try:
        _version = str(JClass("qupath.lib.common.GeneralTools").getVersion())
    except (TypeError, AttributeError):  # pragma: no cover
        version = _QUPATH_VERSION = None
    else:
        version = _QUPATH_VERSION = QuPathVersion(_version)
    return version
