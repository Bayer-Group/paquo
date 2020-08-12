import platform
import shutil
import tempfile
from pathlib import Path

import pytest

from paquo._utils import nullcontext
from paquo.hierarchy import QuPathPathObjectHierarchy
from paquo.images import QuPathImageType, ImageProvider
from paquo.projects import QuPathProject


@pytest.fixture(scope='module')
def image_entry(svs_small):
    with tempfile.TemporaryDirectory(prefix='paquo-') as tmpdir:
        qp = QuPathProject(tmpdir)
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
        qp = QuPathProject(tmpdir)
        _ = qp.add_image(removable_svs_small, image_type=QuPathImageType.BRIGHTFIELD_H_E)
        qp.save()
        removable_svs_small.unlink()
        yield qp.path


@pytest.fixture(scope='function')
def project_with_removed_image_without_image_data(removable_svs_small):
    with tempfile.TemporaryDirectory(prefix='paquo-') as tmpdir:
        qp = QuPathProject(tmpdir)
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
    with QuPathProject(project_with_removed_image, mode='r+') as qp:
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


@pytest.mark.parametrize(
    "uri,parts1n,exc", [
        ("\\\\SHARE\\site\\2020-01-01\\image 123-X,X.svs", None, ValueError),  # weird non-uri found in one project
        ("file:////SHARE/site/image.svs", ('SHARE', 'site', 'image.svs'), None),  # share on win
        ("file:/C:/ABC/image.svs", ('ABC', 'image.svs'), None),  # win-style uris
        ("file:/C:/ABC%20-%20ABC/image.svs", ('ABC - ABC', 'image.svs'), None),
        ("file:/C:/ABC,ABC/image.svs", ('ABC,ABC', 'image.svs'), None),
        ("file:/C:/ABC%20,%20ABC/image.svs", ('ABC , ABC', 'image.svs'), None),
        ("file:/D:/2020-01-01/image.svs", ('2020-01-01', 'image.svs'), None),
        ("file:/F:/2020-01-01/image-123-abc.svs", ('2020-01-01', 'image-123-abc.svs'), None),
        ("file:/U:/site/ABC%20ABC/image.svs", ('site', 'ABC ABC', 'image.svs'), None),
        ("file:/site/image.svs", ('site', 'image.svs'), None),  # posix-style uri
    ],
    ids=[
        "no-uri",
        "network-share",
        "win-simple",
        "win-spaces",
        "win-commas",
        "win-space-comma",
        "win-comb-01",
        "win-comb-02",
        "win-comb-03",
        "posix",
    ]
)
def test_image_provider_path_from_uri(uri, parts1n, exc):
    cm = pytest.raises(exc) if exc else nullcontext()
    with cm:
        path = ImageProvider.path_from_uri(uri)
        assert path.parts[1:] == parts1n
        new_uri = ImageProvider.uri_from_path(path)
        assert ImageProvider.compare_uris(uri, new_uri)


def test_image_provider_ducktyping():
    class IPBad:
        def id(self, x):
            pass  # pragma: no cover

    class IPGood(IPBad):  # if all required methods are implemented we're an ImageProvider
        def uri(self, y):
            pass  # pragma: no cover

        def rebase(self, **x):
            pass  # pragma: no cover

    assert not isinstance(IPBad(), ImageProvider)
    assert isinstance(IPGood(), ImageProvider)


def test_image_provider_default_implementation():
    class NoneProvider(ImageProvider):
        def id(self, x):
            return super().id(x)

        def uri(self, y):
            return super().uri(y)

        def rebase(self, *x, **y):
            return super().rebase(*x, **y)

    ip = NoneProvider()
    assert set(ip.rebase('file:/abc.svs', 'file:/efg.svs')) == {None}


def test_image_provider_uri_from_path():
    with pytest.raises(ValueError):
        ImageProvider.uri_from_path(Path('./abc.svs'))

    p = '/abc.svs' if platform.system() != "Windows" else 'C:/abc.svs'
    assert ImageProvider.uri_from_path(Path(p)).startswith('file:')
