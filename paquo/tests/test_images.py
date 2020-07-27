import tempfile
from contextlib import nullcontext

import pytest
from paquo.hierarchy import QuPathPathObjectHierarchy
from paquo.images import QuPathImageType, ImageProvider
from paquo.projects import QuPathProject


@pytest.fixture(scope='module')
def image_entry(svs_small):
    with tempfile.TemporaryDirectory(prefix='paquo-') as tmpdir:
        qp = QuPathProject(tmpdir)
        entry = qp.add_image(svs_small)
        yield entry


def test_image_entry_return_hierarchy(image_entry):
    assert isinstance(image_entry.hierarchy, QuPathPathObjectHierarchy)


def test_identifers(image_entry):
    assert image_entry.entry_id == "1"  # first image...
    assert image_entry.image_name == "CMU-1-Small-Region.svs"
    assert image_entry.image_name_original == "CMU-1-Small-Region.svs"
    # not changed yet.


def test_path(image_entry):
    assert image_entry.entry_path.is_dir()


def test_metadata_interface(image_entry):

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


# noinspection PyTypeChecker
def test_metadata_non_str_keys(image_entry):

    with pytest.raises(ValueError):
        image_entry.metadata[1] = "abc"

    with pytest.raises(ValueError):
        image_entry.metadata["1"] = 123


def test_properties_interface(image_entry):
    from paquo.java import DefaultProject

    assert len(image_entry.properties) == 1
    assert str(DefaultProject.IMAGE_ID) in image_entry.properties

    with pytest.raises(ValueError):
        image_entry.properties[1] = 123

    image_entry.properties["annotated"] = "no"

    assert image_entry.properties["annotated"] == "no"


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
            pass

    class IPGood(IPBad):  # if all required methods are implemented we're an ImageProvider
        def uri(self, y):
            pass

        def rebase(self, **x):
            pass

    assert not isinstance(IPBad(), ImageProvider)
    assert isinstance(IPGood(), ImageProvider)
