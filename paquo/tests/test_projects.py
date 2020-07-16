import tempfile

# noinspection PyPackageRequirements
import pytest
from paquo.projects import QuPathProject


@pytest.fixture(scope='function')
def small_project(svs_small):
    with tempfile.TemporaryDirectory(prefix='paquo-') as tmpdir:
        qp = QuPathProject(tmpdir)
        qp.images.add(svs_small)
        qp.save()
        yield qp


@pytest.fixture(scope='function')
def new_project():
    with tempfile.TemporaryDirectory(prefix='paquo-') as tmpdir:
        yield QuPathProject(tmpdir)


def test_project_instance():
    with tempfile.TemporaryDirectory(prefix='paquo-') as tmpdir:
        QuPathProject(tmpdir)


def test_project_uri(new_project):
    assert new_project.uri
    # uri_previous is None for empty projects
    assert new_project.uri_previous is None


def test_download_svs(svs_small):
    assert svs_small.is_file()


def test_create_project(svs_small):
    with tempfile.TemporaryDirectory(prefix='paquo-') as tmpdir:
        qp = QuPathProject(tmpdir)
        qp.images.add(svs_small)
        qp.save()


def test_load_annotations(small_project):
    image, = small_project.images
    geojson = image.hierarchy.to_geojson()
    assert geojson == []


