from functools import partial
from typing import Type

import pytest
import shapely.geometry

from paquo.hierarchy import QuPathPathObjectHierarchy
from paquo.pathobjects import QuPathPathAnnotationObject, _PathROIObject, QuPathPathDetectionObject


@pytest.fixture(scope="function")
def empty_hierarchy():
    yield QuPathPathObjectHierarchy()


def test_initial_state(empty_hierarchy: QuPathPathObjectHierarchy):
    h = empty_hierarchy
    repr(h)
    assert h.is_empty
    assert h.root is not None  # root is auto populated
    assert len(h) == 0


def _make_polygons(obj_cls: Type[_PathROIObject], amount: int):
    """returns a list of amount Path Objects"""
    path_objects = []
    for x in range(0, 10 * amount, 10):
        roi = shapely.geometry.Polygon.from_bounds(x, 0, x+5, 5)
        ao = obj_cls.from_shapely(roi)
        path_objects.append(ao)
    return path_objects


_make_polygon_annotations = partial(_make_polygons, QuPathPathAnnotationObject)
_make_polygon_detections = partial(_make_polygons, QuPathPathDetectionObject)


def test_attach_annotations(empty_hierarchy):
    h = empty_hierarchy
    # repr empty
    repr(h.annotations)

    annotations = _make_polygon_annotations(10)

    # add many
    h.annotations.update(annotations)

    # length
    assert len(h) == len(annotations)
    # contains
    assert annotations[3] in h.annotations
    assert 123 not in h.annotations
    # discard
    h.annotations.discard(annotations[7])
    assert len(h) == len(annotations) - 1
    # repr full
    repr(h.annotations)


def test_add_annotation_detection_tile(empty_hierarchy):
    empty_hierarchy.add_annotation(
        roi=shapely.geometry.Polygon.from_bounds(0, 0, 5, 5)
    )
    empty_hierarchy.add_detection(
        roi=shapely.geometry.Polygon.from_bounds(0, 0, 5, 5)
    )
    empty_hierarchy.add_tile(
        roi=shapely.geometry.Polygon.from_bounds(0, 0, 5, 5)
    )


def test_attach_detections(empty_hierarchy):
    h = empty_hierarchy
    detections = _make_polygon_detections(10)

    # add many
    h.detections.update(detections)

    # length
    assert len(h) == len(detections)
    # contains
    assert detections[3] in h.detections
    # discard
    h.detections.discard(detections[7])
    assert len(h) == len(detections) - 1


def test_annotations_detections_separation(empty_hierarchy):
    h = empty_hierarchy
    annotations = _make_polygon_annotations(5)
    detections = _make_polygon_detections(7)
    h.annotations.update(annotations)
    h.detections.update(detections)
    assert len(h.annotations) == 5
    assert len(h.detections) == 7


def test_geojson_roundtrip_via_geojson(empty_hierarchy):
    h = empty_hierarchy
    annotations = _make_polygon_annotations(10)

    h.annotations.update(annotations)
    assert len(h) == len(annotations)
    geojson = h.to_geojson()

    h.annotations.clear()
    assert len(h) == 0

    with pytest.raises(TypeError):
        # noinspection PyTypeChecker
        h.load_geojson("[]")

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


def test_add_to_existing_hierarchy(svs_small, tmp_path):
    # create a project with an image and annotations
    from shapely.geometry import Point
    from paquo.projects import QuPathProject
    from paquo.images import QuPathImageType

    p = tmp_path / "my_project"
    # prepare project
    with QuPathProject(p, mode="x") as qp:
        entry0 = qp.add_image(svs_small, image_type=QuPathImageType.BRIGHTFIELD_H_E)
        entry0.hierarchy.add_annotation(
            roi=Point(1, 1)
        )

        assert len(entry0.hierarchy) == 1
    del qp

    # read project
    with QuPathProject(p, mode="a") as qp:
        entry1 = qp.images[0]

        assert len(entry1.hierarchy) == 1
        entry1.hierarchy.add_annotation(
            roi=Point(2, 2)
        )
        assert len(entry1.hierarchy) == 2

    assert len(entry0.hierarchy) == 1


def test_add_duplicate_to_hierarchy(svs_small, tmp_path):
    """adding duplicate annotations works"""
    # create a project with an image and annotations
    from shapely.geometry import Polygon
    from paquo.projects import QuPathProject
    from paquo.images import QuPathImageType

    p = tmp_path / "my_project"
    # prepare project
    with QuPathProject(p, mode="x") as qp:
        entry0 = qp.add_image(svs_small, image_type=QuPathImageType.BRIGHTFIELD_H_E)
        annotation = entry0.hierarchy.add_annotation(
            roi=Polygon.from_bounds(0, 0, 10, 10),
        )
        annotation.name = "abc"

        assert len(entry0.hierarchy) == 1
    del qp

    # read project
    with QuPathProject(p, mode="a") as qp:
        entry1 = qp.images[0]

        assert len(entry1.hierarchy) == 1
        entry1.hierarchy.add_annotation(
            roi=Polygon.from_bounds(0, 0, 10, 10)
        )
        annotation.name = "abc"
        assert len(entry1.hierarchy) == 2
