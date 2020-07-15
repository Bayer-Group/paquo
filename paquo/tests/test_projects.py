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


TEST_ANNOTATION_POLYGON = [{
    'type': 'Feature',
    'id': 'PathAnnotationObject',
    'geometry': {
        'type': 'Polygon',
        'coordinates': [[
            [1000, 1300],
            [1011, 1420],
            [1120, 1430],
            [1060, 1380],
            [1000, 1300]
        ]]
    },
    'properties': {
        'classification': {
            'name': 'Tumor',
            'colorRGB': -3670016
        },
        'isLocked': False,
        'measurements': []
    }
}]


def test_input_and_output_annotations(small_project):
    image, = small_project.images
    assert image.hierarchy.from_geojson(TEST_ANNOTATION_POLYGON)

    output = image.hierarchy.to_geojson()

    # fixme: this test needs to be more thorough and is just a poc right now
    assert output == TEST_ANNOTATION_POLYGON
