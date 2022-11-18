import platform
import shutil
import tempfile
from contextlib import nullcontext
from operator import itemgetter
from pathlib import Path, PureWindowsPath, PurePosixPath
from typing import Dict

import pytest

from paquo.hierarchy import QuPathPathObjectHierarchy
from paquo.images import QuPathImageType, ImageProvider
from paquo.projects import QuPathProject


@pytest.fixture(scope='module')
def image_entry(svs_small):
    with tempfile.TemporaryDirectory(prefix='paquo-') as tmpdir:
        qp = QuPathProject(tmpdir, mode='x')
        entry = qp.add_image(svs_small)
        yield entry


@pytest.fixture(scope='function')
def removable_svs_small(svs_small):
    with tempfile.TemporaryDirectory(prefix='paquo-') as tmpdir:
        new_path = Path(tmpdir) / svs_small.name
        shutil.copy(svs_small, new_path)
        yield new_path


@pytest.fixture(scope='function')
def project_with_removed_image(removable_svs_small):
    with tempfile.TemporaryDirectory(prefix='paquo-') as tmpdir:
        qp = QuPathProject(tmpdir, mode='x')
        _ = qp.add_image(removable_svs_small, image_type=QuPathImageType.BRIGHTFIELD_H_E)
        qp.save()
        removable_svs_small.unlink()
        yield qp.path


@pytest.fixture(scope='function')
def project_with_removed_image_without_image_data(removable_svs_small):
    with tempfile.TemporaryDirectory(prefix='paquo-') as tmpdir:
        qp = QuPathProject(tmpdir, mode='x')
        _ = qp.add_image(removable_svs_small)
        qp.save()
        removable_svs_small.unlink()
        yield qp.path


def test_image_entry_return_hierarchy(image_entry):
    assert isinstance(image_entry.hierarchy, QuPathPathObjectHierarchy)


def test_identifiers(image_entry):
    assert image_entry.entry_id == "1"  # first image...
    assert image_entry.image_name == "CMU-1-Small-Region.svs"
    # not changed yet.
    image_entry.image_name = "new_name"
    assert image_entry.image_name == "new_name"
    assert repr(image_entry)


def test_path(image_entry):
    assert image_entry.entry_path.is_dir()


def test_image_properties_from_image_server(image_entry):
    assert image_entry.width == 2220
    assert image_entry.height == 2967
    assert image_entry.num_channels == 3
    assert image_entry.num_timepoints == 1
    assert image_entry.num_z_slices == 1


@pytest.mark.xfail(
    platform.uname().machine == "arm64",
    reason="QuPath-vendored openslide not working on arm64"
)
def test_image_downsample_levels(image_entry):
    levels = [
        {'downsample': 1.0,
         'height': 2967,
         'width': 2220},
        # todo: when openslide can be used by qupath, this downsample level
        #   in the test image disappears. investigate...
        # {'downsample': 3.865438534407666,
        #  'height': 768,
        #  'width': 574},
    ]
    assert image_entry.downsample_levels == levels


def test_metadata_interface(image_entry):

    assert repr(image_entry.metadata)

    assert len(image_entry.metadata) == 0
    image_entry.metadata["test_key"] = "test_value"
    assert "test_key" in image_entry.metadata
    assert image_entry.metadata["test_key"] == "test_value"

    image_entry.metadata.update({
        "123": "123", "1": "abc"
    })
    assert len(image_entry.metadata) == 3
    assert "1" in image_entry.metadata
    assert "not-found" not in image_entry.metadata

    with pytest.raises(TypeError):
        # noinspection PyTypeChecker
        del image_entry.metadata[123]
    with pytest.raises(TypeError):
        # noinspection PyTypeChecker
        _ = image_entry.metadata[123]
    with pytest.raises(KeyError):
        _ = image_entry.metadata['not-found']

    image_entry.metadata = {}
    assert dict(image_entry.metadata) == {}

    image_entry.metadata['a'] = '2'
    del image_entry.metadata['a']
    assert len(image_entry.metadata) == 0


# noinspection PyTypeChecker
def test_metadata_non_str_items(image_entry):

    with pytest.raises(TypeError):
        image_entry.metadata[1] = "abc"

    with pytest.raises(TypeError):
        image_entry.metadata["1"] = 123


def test_imagedata_saving_for_removed_images(project_with_removed_image):
    with QuPathProject(project_with_removed_image, mode='r+') as qp:
        entry = qp.images[0]
        assert (entry.entry_path / "data.qpdata").is_file()


def test_imagedata_saving_for_removed_images_without_type(project_with_removed_image_without_image_data):
    with QuPathProject(project_with_removed_image_without_image_data, mode='r+') as qp:
        entry = qp.images[0]
        # todo: check if we actually want this behavior.
        #   at least it's documented now
        assert not (entry.entry_path / "data.qpdata").is_file()


def test_readonly_recovery_hierarchy(project_with_removed_image_without_image_data):
    with QuPathProject(project_with_removed_image_without_image_data, mode='r+') as qp:
        entry = qp.images[0]
        assert repr(entry.hierarchy)


def test_readonly_recovery_image_server(project_with_removed_image):
    from paquo.java import compatibility
    if not compatibility.supports_image_server_recovery():
        pytest.skip(f"unsupported in {compatibility.version}")

    with QuPathProject(project_with_removed_image, mode='r') as qp:
        image_entry = qp.images[0]

        assert image_entry.height
        assert image_entry.width
        assert image_entry.num_channels
        assert image_entry.num_timepoints
        assert image_entry.num_z_slices
        assert image_entry.downsample_levels

        assert repr(image_entry.hierarchy)


def test_properties_interface(image_entry):
    from paquo.java import DefaultProject

    assert repr(image_entry.properties)

    assert len(image_entry.properties) == 1
    assert str(DefaultProject.IMAGE_ID) in image_entry.properties

    with pytest.raises(TypeError):
        image_entry.properties[1] = 123

    image_entry.properties["annotated"] = "no"

    assert image_entry.properties["annotated"] == "no"

    assert 123 not in image_entry.properties

    with pytest.raises(TypeError):
        # noinspection PyTypeChecker
        del image_entry.properties[123]
    with pytest.raises(KeyError):
        _ = image_entry.properties['not-found']
    with pytest.raises(TypeError):
        _ = image_entry.properties[123]

    image_entry.properties = {}
    assert dict(image_entry.properties) == {}


def test_description(image_entry):
    assert image_entry.description == ""
    image_entry.description = "abc"
    assert image_entry.description == "abc"


def test_image_type(image_entry):
    # initially unset
    assert image_entry.image_type == QuPathImageType.UNSET

    with pytest.raises(TypeError):
        image_entry.image_type = 123

    image_entry.image_type = QuPathImageType.BRIGHTFIELD_H_E
    assert image_entry.image_type == QuPathImageType.BRIGHTFIELD_H_E


TEST_URIS: Dict[str, Dict] = {
    "no-uri": {  # weird non-uri found in one project
        "uri": "\\\\SHARE\\site\\2020-01-01\\image 123-X,X.svs",
        "parts": None,
        "path": None,
        "exception": ValueError,
    },
    "network-share": {  # share on win
        "uri": "file:////SHARE/site/ABC/image.svs",
        "parts": ('ABC', 'image.svs'),
        "path": PureWindowsPath("//SHARE/site/", 'ABC', 'image.svs'),
        "exception": None,
    },
    "win-simple": {  # win-style uris
        "uri": "file:/C:/ABC/image.svs",
        "parts": ('ABC', 'image.svs'),
        "path": PureWindowsPath("C:/", 'ABC', 'image.svs'),
        "exception": None,
    },
    "win-spaces": {
        "uri": "file:/C:/ABC%20-%20ABC/image.svs",
        "parts": ('ABC - ABC', 'image.svs'),
        "path": PureWindowsPath("C:/", 'ABC - ABC', 'image.svs'),
        "exception": None,
    },
    "win-commas": {
        "uri": "file:/C:/ABC,ABC/image.svs",
        "parts": ('ABC,ABC', 'image.svs'),
        "path": PureWindowsPath("C:/", 'ABC,ABC', 'image.svs'),
        "exception": None,
    },
    "win-space-comma": {
        "uri": "file:/C:/ABC%20,%20ABC/image.svs",
        "parts": ('ABC , ABC', 'image.svs'),
        "path": PureWindowsPath("C:/", 'ABC , ABC', 'image.svs'),
        "exception": None,
    },
    "win-comb-01": {
        "uri": "file:/D:/2020-01-01/image.svs",
        "parts": ('2020-01-01', 'image.svs'),
        "path": PureWindowsPath("D:/", '2020-01-01', 'image.svs'),
        "exception": None,
    },
    "win-comb-02": {
        "uri": "file:/F:/2020-01-01/image-123-abc.svs",
        "parts": ('2020-01-01', 'image-123-abc.svs'),
        "path": PureWindowsPath("F:/", '2020-01-01', 'image-123-abc.svs'),
        "exception": None,
    },
    "win-comb-03": {
        "uri": "file:/U:/site/ABC%20ABC/image.svs",
        "parts": ('site', 'ABC ABC', 'image.svs'),
        "path": PureWindowsPath("U:/", 'site', 'ABC ABC', 'image.svs'),
        "exception": None,
    },
    "posix": {  # posix-style uri
        "uri": "file:/site/image.svs",
        "parts": ('site', 'image.svs'),
        "path": PurePosixPath("/", 'site', 'image.svs'),
        "exception": None,
    },
}


@pytest.mark.parametrize(
    "uri,exc", list(map(itemgetter("uri", "exception"), TEST_URIS.values())),
    ids=list(TEST_URIS.keys())
)
def test_image_provider_raise_if_invalid_uri(uri, exc):
    cm = pytest.raises(exc) if exc else nullcontext()
    with cm:
        ImageProvider.path_from_uri(uri)


@pytest.mark.parametrize(
    "uri,path", [(x["uri"], x["path"]) for x in TEST_URIS.values() if x["exception"] is None],
    ids=[k for k, x in TEST_URIS.items() if x["exception"] is None]
)
def test_image_provider_uri_from_path(uri, path):
    # noinspection PyTypeChecker
    new_uri = ImageProvider.uri_from_path(path)
    assert uri == new_uri
    # NOTE: the following test is of course weaker
    assert ImageProvider.compare_uris(uri, new_uri)


@pytest.mark.parametrize(
    "uri,path", [(x["uri"], x["path"]) for x in TEST_URIS.values() if x["exception"] is None],
    ids=[k for k, x in TEST_URIS.items() if x["exception"] is None]
)
def test_image_provider_path_from_uri(uri: str, path: Path):
    c_path = ImageProvider.path_from_uri(uri)
    assert c_path.is_absolute()
    assert type(c_path) is type(path)
    assert c_path.parts == path.parts


def test_image_provider_uri_from_relpath_and_abspath():
    with pytest.raises(ValueError):
        ImageProvider.uri_from_path(Path('./abc.svs'))

    p = '/abc.svs' if platform.system() != "Windows" else 'C:/abc.svs'
    assert ImageProvider.uri_from_path(Path(p)).startswith('file:')
