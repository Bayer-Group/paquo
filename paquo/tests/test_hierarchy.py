import uuid
from copy import deepcopy
from functools import partial
from typing import List
from typing import Type
from typing import TypeVar

import pytest
import shapely.geometry
from shapely.geometry import Polygon

from paquo._utils import QuPathVersion
from paquo.classes import QuPathPathClass
from paquo.hierarchy import QuPathPathObjectHierarchy
from paquo.images import QuPathImageType
from paquo.pathobjects import QuPathPathAnnotationObject, _PathROIObject, QuPathPathDetectionObject
from paquo.projects import QuPathProject


@pytest.fixture(scope="function")
def empty_hierarchy():
    yield QuPathPathObjectHierarchy()


def test_initial_state(empty_hierarchy: QuPathPathObjectHierarchy):
    h = empty_hierarchy
    repr(h)
    assert h.is_empty
    assert h.root is not None  # root is auto populated
    assert len(h) == 0


_T = TypeVar('_T', bound=_PathROIObject)


def _make_polygons(obj_cls: Type[_T], amount: int) -> List[_T]:
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


TEST_ANNOTATION_POLYGON_VERSION_0_2_3 = [{
    'type': 'Feature',
    'id': 'PathAnnotationObject',
    'geometry': {
        'type': 'Polygon',
        'coordinates': [[
            [1000, 1300],
            [1011, 1420],
            [1120, 1430],
            [1060, 1380],
            [1000, 1300],
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

# qupath version v0.3.0-rc1 made a few changes to the geojson format
# 1. the 'id' key is removed and replaced by a property key 'object_type'
# 2. the property key 'measurements' is omitted if empty
TEST_ANNOTATION_POLYGON_VERSION_0_3_0_rc1_plus = [{
    'type': 'Feature',
    'geometry': {
        'type': 'Polygon',
        'coordinates': [[
            [1000, 1300],
            [1011, 1420],
            [1120, 1430],
            [1060, 1380],
            [1000, 1300],
        ]]
    },
    'properties': {
        'classification': {
            'name': 'Tumor',
            'colorRGB': -3670016
        },
        'isLocked': False,
        'object_type': 'annotation',
    }
}]


# qupath version v0.4.0 made changes to the geojson format
# 1. the 'id' key is added again but seems to be a UUID for each annotation
TEST_ANNOTATION_POLYGON_VERSION_0_4_0_snapshot = [{
    'type': 'Feature',
    'id': '7d254d72-a9a0-43a6-a455-3fa99e83b7af',
    'geometry': {
        'type': 'Polygon',
        'coordinates': [[
            [1000, 1300],
            [1011, 1420],
            [1120, 1430],
            [1060, 1380],
            [1000, 1300],
        ]]
    },
    'properties': {
        'classification': {
            'name': 'Tumor',
            'colorRGB': -3670016
        },
        'isLocked': False,
        'object_type': 'annotation',
    }
}]


@pytest.fixture
def example_annotation(qupath_version):
    if qupath_version <= QuPathVersion("0.2.3"):
        yield deepcopy(TEST_ANNOTATION_POLYGON_VERSION_0_2_3)
    elif qupath_version < QuPathVersion("0.4.0"):
        yield deepcopy(TEST_ANNOTATION_POLYGON_VERSION_0_3_0_rc1_plus)
    else:
        yield deepcopy(TEST_ANNOTATION_POLYGON_VERSION_0_4_0_snapshot)


def is_uuid(x):
    try:
        uuid.UUID(x)
    except ValueError:
        return False
    else:
        return True


@pytest.mark.parametrize(
    "input_annotation", [
        pytest.param(TEST_ANNOTATION_POLYGON_VERSION_0_2_3, id='v0.2.3'),
        pytest.param(TEST_ANNOTATION_POLYGON_VERSION_0_3_0_rc1_plus, id='v0.3.0rc1'),
        pytest.param(TEST_ANNOTATION_POLYGON_VERSION_0_4_0_snapshot, id='v0.4.0+snapshot'),
    ]
)
def test_geojson_roundtrip_via_annotations(empty_hierarchy, example_annotation, input_annotation, qupath_version):
    h = empty_hierarchy
    assert h.load_geojson(input_annotation)
    output = h.to_geojson()

    if qupath_version < QuPathVersion("0.4.0"):
        pass
    else:
        # these uuids are assigned randomly if they were missing in input
        out_id = output[0].pop("id", "")
        test_id = example_annotation[0].pop("id", "")
        assert is_uuid(out_id) and is_uuid(test_id)
    assert output == example_annotation


@pytest.fixture(scope='function')
def new_project(tmp_path):
    yield QuPathProject(tmp_path / "paquo-project", mode='x')


@pytest.fixture(scope='function')
def project_with_classes(new_project):
    new_project.path_classes = [
        QuPathPathClass("class0", color="#ff0000"),
        QuPathPathClass("class1", color="#00ff00"),
        QuPathPathClass("class2", color="#0000ff"),
    ]
    assert (
        new_project.path_classes
        and all(c.name.startswith('class') for c in new_project.path_classes)
    )
    yield new_project


NUM_ANNOTATIONS = 4

@pytest.fixture(scope='function')
def project_with_annotations(project_with_classes, svs_small):
    pth_cls, *_ = project_with_classes.path_classes

    num_annotations = NUM_ANNOTATIONS

    with project_with_classes as qp:
        entry = qp.add_image(
            svs_small, image_type=QuPathImageType.BRIGHTFIELD_H_E
        )

        for x in range(num_annotations):
            entry.hierarchy.add_annotation(
                roi=Polygon.from_bounds(0 + x, 0 + x, 1 + x, 1 + x),
                path_class=pth_cls,
            )
        assert len(entry.hierarchy.annotations) == num_annotations
    yield project_with_classes


def test_hierarchy_annotation_proxy_getitem(project_with_annotations):
    h = project_with_annotations.images[0].hierarchy

    assert len(h.annotations) == NUM_ANNOTATIONS
    assert len(h.annotations[NUM_ANNOTATIONS//2:]) == NUM_ANNOTATIONS//2
    assert len(h.annotations[[0, 3]]) == 2
    for idx in range(len(h.annotations)):
        _ = h.annotations[idx]


def test_add_to_existing_hierarchy(project_with_annotations):
    # create a project with an image and annotations
    from shapely.geometry import Point
    from paquo.projects import QuPathProject

    p = project_with_annotations.path
    num_annotations = len(project_with_annotations.images[0].hierarchy)
    del project_with_annotations

    # read project
    with QuPathProject(p, mode="a") as qp:
        entry1 = qp.images[0]

        assert len(entry1.hierarchy) == num_annotations
        entry1.hierarchy.add_annotation(
            roi=Point(2, 2)
        )
        assert len(entry1.hierarchy) == num_annotations + 1


def test_add_duplicate_to_hierarchy(project_with_annotations):
    """adding duplicate annotations works"""
    # create a project with an image and annotations
    from paquo.projects import QuPathProject

    p = project_with_annotations.path
    num_annotations = len(project_with_annotations.images[0].hierarchy)
    annotation = next(iter(project_with_annotations.images[0].hierarchy.annotations))
    del project_with_annotations

    # read project
    with QuPathProject(p, mode="a") as qp:
        entry1 = qp.images[0]
        entry1.hierarchy.add_annotation(
            roi=annotation.roi
        )
        assert len(entry1.hierarchy) == num_annotations + 1


def test_hierarchy_update_on_annotation_update(project_with_annotations):
    """updating annotation or detection objects triggers is_changed on hierarchy"""
    # create a project with an image and annotations
    from paquo.projects import QuPathProject
    from paquo.classes import QuPathPathClass

    p = project_with_annotations.path
    num_annotations = len(project_with_annotations.images[0].hierarchy)
    del project_with_annotations

    # test update
    with QuPathProject(p, mode="a") as qp:
        entry1 = qp.images[0]

        assert len(entry1.hierarchy) == num_annotations

        for annotation in entry1.hierarchy.annotations:
            annotation.update_path_class(QuPathPathClass("new"))
            assert entry1.is_changed()  # every update changes
            assert len(entry1.hierarchy) == num_annotations

        assert all(a.path_class.name == "new" for a in entry1.hierarchy.annotations)


def test_hierarchy_no_autoflush_annotation_update(project_with_annotations):
    """updating annotation or detection objects doesn't immediately trigger update"""
    from paquo.classes import QuPathPathClass

    with project_with_annotations as qp:
        entry1 = qp.images[0]
        with entry1.hierarchy.no_autoflush():
            for annotation in entry1.hierarchy.annotations:
                annotation.update_path_class(QuPathPathClass("new"))
                assert not entry1.is_changed()

        assert entry1.is_changed()
        assert all(a.path_class.name == "new" for a in entry1.hierarchy.annotations)


@pytest.fixture(scope='function')
def entry_with_annotations(project_with_annotations):
    # test update
    with project_with_annotations as qp:
        yield qp.images[0]


def test_add_incorrect_to_hierarchy(empty_hierarchy):
    with pytest.raises(TypeError):
        # noinspection PyTypeChecker
        empty_hierarchy.annotations.add("abc")

    with pytest.raises(TypeError):
        # noinspection PyTypeChecker
        empty_hierarchy.annotations.discard("abc")
