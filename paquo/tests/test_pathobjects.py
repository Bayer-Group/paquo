import pytest
import shapely.geometry
from shapely import Polygon

from paquo._utils import QuPathVersion
from paquo.classes import QuPathPathClass
from paquo.pathobjects import QuPathPathAnnotationObject
from paquo.projects import QuPathProject


def test_qupath_to_shapely_conversion():
    from paquo.java import ROIs
    from paquo.pathobjects import _qupath_roi_to_shapely_geometry
    from shapely.geometry import Point

    roi = ROIs.createPointsROI(1.0, 2.0, None)
    point = _qupath_roi_to_shapely_geometry(roi)

    assert isinstance(point, Point)
    assert point.x == 1.0 and point.y == 2.0


def test_shapely_to_qupath_conversion():
    from paquo.pathobjects import _shapely_geometry_to_qupath_roi
    from shapely.geometry import Point

    point = Point(1.0, 2.0)
    roi = _shapely_geometry_to_qupath_roi(point)

    assert roi.getRoiName() == "Points"


@pytest.fixture(
    scope="function",
    params=[
        shapely.geometry.Polygon.from_bounds(10, 20, 100, 200),
        shapely.geometry.Point(1, 2),
        shapely.geometry.LineString([[1, 1], [2, 2]]),
        shapely.geometry.MultiPolygon(
            [shapely.geometry.Polygon.from_bounds(10, 20, 100, 200),
             shapely.geometry.Polygon.from_bounds(110, 20, 200, 200)]
        )
    ],
    ids=[
        "Polygon",
        "Point",
        "LineString",
        "MultiPolygon"
    ],
)
def path_annotation(request):
    """parameterized fixture for different Annotation Objects"""
    roi = request.param
    path_class = QuPathPathClass("myclass")

    ao = QuPathPathAnnotationObject.from_shapely(roi, path_class)

    yield ao


def test_geojson_serialization(path_annotation, qupath_version):
    geo_json = path_annotation.to_geojson()

    assert geo_json["type"] == "Feature"

    # bad practice
    if qupath_version <= QuPathVersion("0.2.3"):
        assert geo_json["id"] == "PathAnnotationObject"
    elif qupath_version < QuPathVersion("0.4.0"):
        assert geo_json["properties"]["object_type"] == "annotation"
    else:
        assert geo_json["properties"]["objectType"] == "annotation"

    assert "geometry" in geo_json
    geom = geo_json["geometry"]

    p = shapely.geometry.shape(geom)
    assert p.equals(path_annotation.roi)

    assert "properties" in geo_json
    prop = geo_json["properties"]

    if path_annotation.locked:
        assert prop["isLocked"] is True
    else:
        if qupath_version < QuPathVersion("0.4.0"):
            assert prop["isLocked"] is False
        else:
            assert "isLocked" not in prop

    # bad practice
    if qupath_version <= QuPathVersion("0.2.3"):
        assert prop["measurements"] == path_annotation.measurements.to_records()
    else:
        measurements = path_annotation.measurements.to_records()
        if not measurements:
            assert "measurements" not in prop
        else:
            assert prop["measurements"] == measurements

    assert prop["classification"]["name"] == path_annotation.path_class.name
    if qupath_version < QuPathVersion("0.4.0"):
        assert prop["classification"]["colorRGB"] == path_annotation.path_class.color.to_java_rgba()
    else:
        assert tuple(prop["classification"]["color"]) == path_annotation.path_class.color.to_rgb()


def test_annotation_object():
    with pytest.raises(TypeError):
        # noinspection PyTypeChecker
        QuPathPathAnnotationObject.from_shapely(roi=123)

    ao = QuPathPathAnnotationObject.from_shapely(
        shapely.geometry.Point(1, 1),
        path_class=QuPathPathClass('myclass'),
        measurements={'measurement1': 1.23},
        path_class_probability=0.5,
    )

    assert ao.path_class.name == "myclass"
    assert ao.path_class_probability == 0.5
    with pytest.raises(TypeError):
        # noinspection PyTypeChecker
        ao.update_path_class(123)
    ao.update_path_class(None)
    assert ao.path_class is None
    assert ao.is_editable
    assert not ao.locked
    ao.locked = True
    assert ao.locked
    assert ao.level == 0

    # name
    assert ao.name is None
    ao.name = "my annotation"
    assert ao.name == "my annotation"
    ao.name = None

    # description
    assert ao.description is None
    ao.description = "my description"
    assert ao.description == "my description"
    with pytest.raises(TypeError):
        ao.description = None

    # roi
    pt = shapely.geometry.Point(2, 2)
    ao.update_roi(pt)
    assert ao.roi == pt

    # repr
    ao.name = "abc"
    ao.update_path_class(QuPathPathClass('myclass'))
    assert repr(ao)


def test_measurements():
    ao = QuPathPathAnnotationObject.from_shapely(
        shapely.geometry.Point(1, 1),
        path_class=QuPathPathClass('myclass'),
        measurements={'measurement1': 1.23},
        path_class_probability=0.5,
    )

    assert 123 not in ao.measurements
    assert "measurement1" in ao.measurements
    assert len(ao.measurements) == 1
    assert repr(ao.measurements)
    assert str(ao.measurements)

    # allow index access (note this depends on order of insertion)
    assert ao.measurements[0] == ao.measurements['measurement1']

    with pytest.raises(KeyError):
        _ = ao.measurements[None]

    with pytest.raises(KeyError):
        _ = ao.measurements["this-key-does-not-exist"]

    with pytest.raises(KeyError):
        del ao.measurements[None]

    del ao.measurements['measurement1']
    ao.measurements.clear()


@pytest.fixture(scope="function")
def project_with_detections(tmp_path, svs_small):
    pth = tmp_path / "paquo-project"
    with QuPathProject(pth, mode='x') as proj:
        entry = proj.add_image(svs_small)
        entry.hierarchy.add_detection(
            roi=Polygon.from_bounds(20, 20, 100, 100),
        )
        assert len(entry.hierarchy.detections) == 1
    yield pth


def test_saving_measurements(project_with_detections):
    with QuPathProject(project_with_detections, mode="a") as proj:
        det = proj.images[0].hierarchy.detections[0]
        assert len(det.measurements) == 0
        det.measurements["something"] = 1.0
        assert dict(det.measurements) == {"something": 1.0}

    with QuPathProject(project_with_detections, mode="r") as proj:
        det = proj.images[0].hierarchy.detections[0]
        assert det.measurements["something"] == 1.0
