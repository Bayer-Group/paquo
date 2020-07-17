import pytest

import shapely.geometry

from paquo.hierarchy import QuPathPathObjectHierarchy
from paquo.pathobjects import QuPathPathAnnotationObject


@pytest.fixture(scope="function")
def empty_hierarchy():
    yield QuPathPathObjectHierarchy()


def test_initial_state(empty_hierarchy: QuPathPathObjectHierarchy):
    h = empty_hierarchy
    assert h.is_empty
    assert h.root is not None  # root is auto populated
    assert len(h) == 0


def _make_polygon_annotations(amount: int):
    """returns a list of amount QuPathPathAnnotationObjects"""
    annotations = []
    for x in range(0, 10 * amount, 10):
        roi = shapely.geometry.Polygon.from_bounds(x, 0, x+5, 5)
        ao = QuPathPathAnnotationObject.from_shapely(roi)
        annotations.append(ao)
    return annotations


def test_attach_annotations(empty_hierarchy):
    h = empty_hierarchy
    annotations = _make_polygon_annotations(10)

    # add many
    h.annotations.update(annotations)

    # length
    assert len(h) == len(annotations)
    # contains
    assert annotations[3] in h.annotations
    # discard
    h.annotations.discard(annotations[7])
    assert len(h) == len(annotations) - 1


def test_geojson_roundtrip_via_geojson(empty_hierarchy):
    h = empty_hierarchy
    annotations = _make_polygon_annotations(10)

    h.annotations.update(annotations)
    assert len(h) == len(annotations)
    geojson = h.to_geojson()

    h.annotations.clear()
    assert len(h) == 0

    h.load_geojson(geojson)
    assert len(h) == 10


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


def test_geojson_roundtrip_via_annotations(empty_hierarchy):
    h = empty_hierarchy
    assert h.load_geojson(TEST_ANNOTATION_POLYGON)
    output = h.to_geojson()
    assert output == TEST_ANNOTATION_POLYGON
