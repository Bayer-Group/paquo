import shutil
import tempfile

# noinspection PyPackageRequirements
from pathlib import Path

# noinspection PyPackageRequirements
import pytest

from paquo.images import ImageProvider
from paquo.projects import QuPathProject


@pytest.fixture(scope='function')
def new_project(tmp_path):
    yield QuPathProject(tmp_path / "paquo-project")


def test_project_instance():
    with tempfile.TemporaryDirectory(prefix='paquo-') as tmpdir:
        q = QuPathProject(tmpdir)
        repr(q)
        q.save()


def test_project_create_no_dir():
    with tempfile.TemporaryDirectory(prefix='paquo-') as tmpdir:
        project_path = Path(tmpdir) / "new_project"
        q = QuPathProject(project_path)
        q.save()


def test_project_open_with_filename(new_project):
    new_project.save()
    # this points to path/project.qpproj
    proj_fn = new_project.path
    QuPathProject(proj_fn, create=False)


def test_project_uri(new_project):
    assert new_project.uri.startswith("file:")
    assert new_project.uri.endswith(".qpproj")
    # uri_previous is None for empty projects
    assert new_project.uri_previous is None


def test_project_save_and_path(new_project):
    assert not new_project.path.is_file()
    new_project.save()
    assert new_project.path.is_file()


def test_project_version(new_project):
    from paquo.java import GeneralTools
    new_project.save()
    assert new_project.version == str(GeneralTools.getVersion())


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


def test_project_add_image(new_project, svs_small):
    entry = new_project.add_image(svs_small)
    assert (Path(entry.entry_path) / "thumbnail.jpg").is_file()


def test_project_save_image_data(new_project, svs_small):
    from paquo.pathobjects import QuPathPathAnnotationObject
    from shapely.geometry import Point
    entry = new_project.add_image(svs_small)
    entry.hierarchy.annotations.add(
        QuPathPathAnnotationObject.from_shapely(
            Point(1, 2)
        )
    )
    new_project.save()
    assert (entry.entry_path / "data.qpdata").is_file()


def test_project_image_uri_update(new_project, svs_small):

    with tempfile.TemporaryDirectory(prefix="paquo-") as tmp:
        new_svs_small = Path(tmp) / svs_small.name
        shutil.copy(svs_small, new_svs_small)

        entry = new_project.add_image(new_svs_small)

        # test that entry can be read
        assert entry.is_readable()
        assert all(new_project.is_readable().values())

    # tempdir is cleanup up, entry is not readable anymore
    assert not entry.is_readable()
    assert not any(new_project.is_readable().values())

    # mapping for uris
    uri2uri = {
        entry.uri: ImageProvider.uri_from_path(svs_small)
    }
    new_project.update_image_paths(uri2uri=uri2uri)

    # test that entry can be read
    assert entry.is_readable()
    assert all(new_project.is_readable().values())
