from contextlib import nullcontext
from pathlib import Path

import pytest

# noinspection PyProtectedMember
from paquo.jpype_backend import start_jvm, find_qupath, qupath_jvm_info_from_qupath_dir, _conda_qupath_dir


def test_start_jvm_run_twice():
    assert start_jvm() == start_jvm()


def test_non_standard_qupath_installation(tmp_path):
    qupath_dir = Path(tmp_path)
    with pytest.raises(FileNotFoundError):
        qupath_jvm_info_from_qupath_dir(qupath_dir, [])


def test_conda_qupath_dir(monkeypatch, tmp_path):
    monkeypatch.delenv("CONDA_PREFIX", raising=False)
    assert _conda_qupath_dir() is None


def test_find_qupath(tmp_path):
    # prepare dirs
    opt = Path(tmp_path).absolute() / "opt"
    opt.mkdir()
    for qp in ["QuPath-123", "QuPath-234"]:
        (opt / qp).mkdir()

    with pytest.raises(FileNotFoundError):
        # qupath_dir provided by user must point to a valid qupath dir
        find_qupath(qupath_dir=str(tmp_path.absolute()))

    with pytest.raises(ValueError):
        # there is no spoon
        find_qupath(
            qupath_search_dirs=[str(opt), 'not-anything'],
            qupath_search_conda=False
        )

    with pytest.raises(ValueError):
        # search only one
        find_qupath(
            qupath_search_dirs=str(opt),
            qupath_search_conda=False
        )

    # first search others than try conda
    _d = _conda_qupath_dir()
    if _d is not None and _d.is_dir():
        cm = nullcontext()
    else:
        cm = pytest.raises(ValueError)  # pragma: no cover
    with cm:
        # search conda last
        find_qupath(qupath_dir=None, qupath_search_conda=True, qupath_prefer_conda=False)


def test_find_qupath_java_opts_as_string():
    with pytest.raises(ValueError):
        # search only one
        find_qupath(
            java_opts="-Djava.library.path='/123' -Djava.launcher.path='/'",
            qupath_search_conda=False
        )
