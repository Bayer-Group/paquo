import tempfile
import unittest.mock
from pathlib import Path

import pytest
import shapely.geometry

from paquo._repr import repr_html, repr_svg
from paquo.colors import QuPathColor
from paquo.images import QuPathProjectImageEntry
from paquo.pathobjects import QuPathPathAnnotationObject
from paquo.projects import QuPathProject


@pytest.fixture(scope='function')
def new_project(tmp_path):
    yield QuPathProject(tmp_path / "paquo-project", mode='x')


@pytest.fixture(scope='module')
def image_entry(svs_small):
    with tempfile.TemporaryDirectory(prefix='paquo-') as tmpdir:
        qp = QuPathProject(tmpdir, mode='x')
        entry = qp.add_image(svs_small)
        yield entry


def test_repr_helper_fallback():
    obj_without_ipynb_repr = "a"
    assert repr(obj_without_ipynb_repr) == repr_html(obj_without_ipynb_repr)
    assert repr(obj_without_ipynb_repr) == repr_svg(obj_without_ipynb_repr)


def test_ipython_repr(new_project):
    assert new_project._repr_html_()


def test_pathobject_repr():
    p = QuPathPathAnnotationObject.from_shapely(
        roi=shapely.geometry.Point(1, 2)
    )
    assert repr_html(p)


def test_color_repr():
    c = QuPathColor.from_hex("#123456")
    assert repr_html(c)


def test_hierarchy_repr(image_entry):
    assert repr_html(image_entry.hierarchy)


def test_image_repr(image_entry, monkeypatch):
    assert repr_html(image_entry)
    assert repr_html(image_entry, compact=True)
