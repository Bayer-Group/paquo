import tempfile

# noinspection PyPackageRequirements
import pytest
from paquo.projects import QuPathProject


@pytest.fixture(scope='function')
def new_project():
    with tempfile.TemporaryDirectory(prefix='paquo-') as tmpdir:
        yield QuPathProject(tmpdir)


def test_project_instance():
    with tempfile.TemporaryDirectory(prefix='paquo-') as tmpdir:
        q = QuPathProject(tmpdir)
        repr(q)


def test_project_uri(new_project):
    assert new_project.uri.startswith("file:")
    assert new_project.uri.endswith(".qpproj")
    # uri_previous is None for empty projects
    assert new_project.uri_previous is None


def test_project_save_and_path(new_project):
    assert not new_project.path.is_file()
    new_project.save()
    assert new_project.path.is_file()


@pytest.mark.xfail(reason="needs gui running?")
def test_project_version(new_project):
    new_project.save()
    # fixme: update when we update qupath or compare to qupath version
    assert new_project.version == "0.2.1"


def test_project_add_path_classes(new_project):
    from paquo.classes import QuPathPathClass

    names = {'a', 'b', 'c'}
    new_project.path_classes = map(QuPathPathClass.create, names)

    assert len(new_project.path_classes) == 3
    assert set(c.name for c in new_project.path_classes) == names


def test_download_svs(svs_small):
    assert svs_small.is_file()


def test_timestamps(new_project):
    assert new_project.timestamp_creation > 0
    assert new_project.timestamp_modification > 0


def test_create_project(svs_small):
    with tempfile.TemporaryDirectory(prefix='paquo-') as tmpdir:
        qp = QuPathProject(tmpdir)
        qp.add_image(svs_small)
        qp.save()

