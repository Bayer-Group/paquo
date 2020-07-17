import tempfile

import pytest
from paquo.hierarchy import QuPathPathObjectHierarchy
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
    assert image_entry.id == "1"  # first image...
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
        "123": "123", 1: "abc"
    })
    assert len(image_entry.metadata) == 3
