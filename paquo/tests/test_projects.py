import os
import platform
import posixpath
import shutil
import tempfile
from contextlib import nullcontext
from pathlib import Path

import pytest

from paquo.images import ImageProvider, QuPathProjectImageEntry, QuPathImageType
from paquo.projects import QuPathProject


@pytest.fixture(scope='function')
def new_project(tmp_path):
    yield QuPathProject(tmp_path / "paquo-project", mode='x')


@pytest.fixture(scope='function')
def tmp_path2(tmp_path):
    yield tmp_path / "another_path"


def test_project_instance():
    with tempfile.TemporaryDirectory(prefix='paquo-') as tmpdir:
        q = QuPathProject(tmpdir, mode='x')
        repr(q)
        q.save()


def test_project_create_no_dir():
    with tempfile.TemporaryDirectory(prefix='paquo-') as tmpdir:
        project_path = Path(tmpdir) / "new_project"
        q = QuPathProject(project_path, mode='x')
        q.save()


def test_project_creation_input_error(tmp_path):

    p = tmp_path / Path('somewhere')
    p.mkdir()

    with pytest.raises(TypeError):
        # noinspection PyTypeChecker
        QuPathProject(p, image_provider=object())

    with pytest.raises(ValueError):
        QuPathProject(p / 'myproject.proj')  # needs .qpproj

    with pytest.raises(FileNotFoundError):
        QuPathProject(p / 'myproject.qpproj', mode='r+')

    with open(p / 'should-not-be-here', 'w') as f:
        f.write('project directories need to be empty')
    with pytest.raises(ValueError):
        QuPathProject(p, mode='x')


# noinspection PyTypeChecker
@pytest.mark.parametrize(
    "mode", [
        'r', 'r+', 'w', 'w+', 'a', 'a+', 'x', 'x+'
    ]
)
def test_project_creation_mode(mode, tmp_path2, new_project):
    # test creating in empty dir
    cm = pytest.raises(FileNotFoundError) if "r" in mode else nullcontext()
    with cm:
        QuPathProject(tmp_path2, mode=mode).save()

    # prepare an existing proj
    p = new_project.path
    new_project.save()
    del new_project
    assert not p.with_suffix('.qpproj.backup').is_file()
    assert not any(p.parent.parent.glob('*.backup'))

    # test creating in existing dir
    if "x" in mode:
        cm = pytest.raises(FileExistsError)
    elif "r" == mode:
        cm = pytest.raises(IOError)  # can't save!
    else:
        cm = nullcontext()
    with cm:
        QuPathProject(p, mode=mode).save()

    assert p.is_file()
    backups = list(p.parent.parent.glob('*.backup'))

    if 'w' in mode:
        assert len(backups) == 1
        assert backups[0].is_file()
    else:
        assert len(backups) == 0


def test_backup_path_project_stash(tmp_path):
    from paquo.projects import _stash_project_files
    p = Path(tmp_path)
    assert _stash_project_files(p) is None
    f = p / "wrong.file"
    f.touch()
    assert _stash_project_files(f) is None


# noinspection PyTypeChecker
def test_unsupported_mode(tmp_path):
    with pytest.raises(ValueError):
        QuPathProject(tmp_path, mode="???")


def test_project_open_with_filename(new_project):
    new_project.save()
    # this points to path/project.qpproj
    proj_fn = new_project.path
    QuPathProject(proj_fn, mode='r+')


def test_project_name(tmp_path):
    p = Path(tmp_path) / "my_project_123"
    p.mkdir()
    qp = QuPathProject(p, mode='x')
    assert qp.name == "my_project_123"


def test_project_uri(new_project):
    assert new_project.uri.startswith("file:")
    assert new_project.uri.endswith(".qpproj")
    # uri_previous is None for empty projects
    # assert new_project.uri_previous is None


def test_project_save_and_path(new_project):
    assert not new_project.path.is_file()
    new_project.save()
    assert new_project.path.is_file()


def test_project_version(new_project):
    from paquo.java import GeneralTools
    new_project.save()
    qp_version = str(GeneralTools.getVersion())
    assert new_project.version == qp_version

    with QuPathProject(new_project.path, mode='r+') as qp:
        assert qp.version == qp_version


def test_project_add_path_classes(new_project):
    from paquo.classes import QuPathPathClass

    names = {'a', 'b', 'c'}
    new_project.path_classes = map(QuPathPathClass, names)

    assert len(new_project.path_classes) == 3
    assert {c.name for c in new_project.path_classes} == names


def test_download_svs(svs_small):
    assert svs_small.is_file()


def test_timestamps(new_project):
    assert new_project.timestamp_creation > 0
    assert new_project.timestamp_modification > 0


def test_project_add_image(new_project, svs_small):
    with pytest.raises(ValueError):
        # can't add images by instantiating them
        QuPathProjectImageEntry(svs_small)

    entry = new_project.add_image(svs_small)
    assert (Path(entry.entry_path) / "thumbnail.jpg").is_file()

    assert len(new_project.images) == 1
    assert entry in new_project.images
    assert object() not in new_project.images


@pytest.mark.skipif(platform.system() != "Windows", reason="windows only")
def test_project_add_image_windows(new_project, svs_small):
    drive, *parts = svs_small.parts

    uri = posixpath.join(f"file:////localhost/{drive[0].lower()}$", *parts)

    _ = new_project.add_image(uri)
    assert len(new_project.images) == 1


@pytest.mark.skipif(platform.system() != "Windows", reason="windows only")
@pytest.mark.parametrize(
    "renamed_svs_small", [
        pytest.param("abc.svs", id="simple_name"),
        pytest.param("image%image.svs", id="name_with_percentage"),
    ],
    indirect=True,
)
def test_project_add_image_windows_unencoded_uri(new_project, renamed_svs_small):
    drive, *parts = renamed_svs_small.parts

    uri = posixpath.join(f"file:////localhost/{drive[0]}$", *parts)

    _ = new_project.add_image(uri)
    assert len(new_project.images) == 1


def test_project_add_image_writes_project(tmp_path, svs_small):
    qp = QuPathProject(tmp_path, mode='x')
    qp.add_image(svs_small)

    assert qp.path.is_file()


def test_project_add_image_twice(new_project, svs_small):
    new_project.add_image(svs_small)
    with pytest.raises(FileExistsError):
        new_project.add_image(svs_small)
    assert len(new_project.images) == 1

    new_project.add_image(svs_small, allow_duplicates=True)
    assert len(new_project.images) == 2


def test_project_add_image_with_type(new_project, svs_small):
    t = QuPathImageType.BRIGHTFIELD_H_DAB
    entry = new_project.add_image(svs_small, image_type=t)
    assert entry.image_type == t


def test_project_add_unsupported_image(new_project, tmp_path):
    image = Path(tmp_path) / "unsupported.image"
    with open(image, "w") as f:
        f.write("very unsupported image")

    with pytest.raises(IOError):
        new_project.add_image(image)


def test_project_remove_image(new_project, svs_small):
    # Add an image to the project and then remove it:
    new_project.add_image(svs_small)
    assert len(new_project.images) == 1
    new_project.remove_image(new_project.images[0])
    assert len(new_project.images) == 0


def test_project_remove_image_wrong_type(new_project):
    with pytest.raises(TypeError):
        new_project.remove_image("some/file.svs")


def test_project_image_slicing(new_project):
    _ = new_project.images[slice(None, None, None)]


def test_project_image_incorrect_index(new_project):
    with pytest.raises(IndexError):
        # noinspection PyTypeChecker
        _ = new_project.images["abc"]


def test_project_image_repr(new_project):
    assert repr(new_project.images)


def test_project_add_image_incorrect_path(new_project):
    with pytest.raises(FileNotFoundError):
        new_project.add_image("i-do-not-exist.svs")


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


def test_project_delete_image_file_when_opened(new_project, svs_small):
    # prepare new image to be deleted
    new_svs_small = new_project.path.parent / f"image_be_gone{svs_small.suffix}"
    shutil.copy(svs_small, new_svs_small)

    entry = new_project.add_image(new_svs_small)
    assert entry.is_readable()

    # TODO: this test should actually depend on the backend that qupath
    #   uses internally for opening the file. Since we reenabled openslide
    #   we hardcode it here, so that the intention of this test stays clear
    qupath_uses = "OPENSLIDE"

    if qupath_uses == "BIOFORMATS":  # pragma: no cover
        if platform.system() == "Windows":
            # NOTE: on Windows because you can't delete files that have open
            #   file handles. In this test we're deleting the file opened by
            #   the ImageServer on the java side. (this is happening
            #   implicitly when calling is_readable() because the java
            #   implementation of is_readable() loads the ImageData which
            #   creates an instance of an ImageServer)
            cm = pytest.raises(PermissionError)
        else:
            cm = nullcontext()

        with cm:
            os.unlink(new_svs_small)

    elif qupath_uses == "OPENSLIDE":

        os.unlink(new_svs_small)

    else:  # pragma: no cover
        raise ValueError('...')


@pytest.mark.xfail(platform.system() == "Windows", reason="file handles don't get closed by qupath?")
def test_project_image_uri_update(tmp_path, svs_small):

    project_path = tmp_path / "paquo-project"
    new_svs_small = tmp_path / "images" / f"image_be_gone{svs_small.suffix}"
    new_svs_small.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(svs_small, new_svs_small)
    assert new_svs_small.is_file()

    # create a project
    with QuPathProject(project_path, mode='x') as qp:
        entry = qp.add_image(new_svs_small)
        assert entry.is_readable()
        assert all(qp.is_readable().values())

    # cleanup
    del entry
    del qp

    # remove image
    os.unlink(new_svs_small)

    # reload the project
    with QuPathProject(project_path, mode='r+') as qp:
        entry, = qp.images
        assert not entry.is_readable()
        assert not all(qp.is_readable().values())

        # test if there's no remapping
        qp.update_image_paths(uri2uri={})
        # test if we remap to same
        qp.update_image_paths(uri2uri={entry.uri: entry.uri})

        # create mapping for uris
        uri2uri = {
            entry.uri: ImageProvider.uri_from_path(svs_small),
        }
        # update the uris
        qp.update_image_paths(uri2uri=uri2uri)

        # test that entry can be read
        assert entry.is_readable()
        assert all(qp.is_readable().values())


def test_project_image_uri_update_try_relative(tmp_path, svs_small):

    # prepare initial location
    location_0 = tmp_path / "location_0"
    location_0.mkdir()

    # prepare a project and images at location_0
    image_path = location_0 / "images" / "image0.svs"
    image_path.parent.mkdir(parents=True)
    shutil.copy(svs_small, image_path)
    assert image_path.is_file()

    # create a project
    with QuPathProject(location_0 / "project", mode='x') as qp:
        entry = qp.add_image(image_path)
        assert entry.is_readable()
        assert all(qp.is_readable().values())

    # cleanup
    del entry
    del qp

    # NOW move the location
    location_1 = tmp_path / "location_1"
    shutil.move(location_0, location_1)

    with QuPathProject(location_1 / "project", mode='r') as qp:
        entry, = qp.images
        assert not entry.is_readable()
        assert not all(qp.is_readable().values())
        assert 'location_1' in str(qp.path)
        assert 'location_0' in entry.uri  # still points to the old location

        # fixme: testing private api
        assert 'location_0' in str(qp.java_object.getPreviousURI().toString())

        qp.update_image_paths(try_relative=True)

        # test that entry can be read
        assert entry.is_readable()
        assert all(qp.is_readable().values())
