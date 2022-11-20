import importlib.util
import shutil
import tempfile
from contextlib import contextmanager
from pathlib import Path

import pytest
import shapely.geometry

from paquo.images import ImageProvider
from paquo.projects import QuPathProject
from paquo._utils import cached_property


@pytest.fixture(scope='module')
def project_and_changes(svs_small):
    with tempfile.TemporaryDirectory(prefix='paquo-') as tmpdir:
        qp = QuPathProject(tmpdir, mode='x')
        entry = qp.add_image(svs_small)
        entry.hierarchy.add_annotation(
            roi=shapely.geometry.Point(1, 2)
        )
        qp.save()
        project_path = qp.path.parent
        del qp

        last_changes = {}
        for file in project_path.glob("**/*.*"):
            p = str(file.absolute())
            last_changes[p] = file.stat().st_mtime

        yield project_path, last_changes


@pytest.fixture(scope='function')
def copy_svs_small(svs_small):
    with tempfile.TemporaryDirectory(prefix='paquo-') as tmpdir:
        new_path = Path(tmpdir) / svs_small.name
        shutil.copy(svs_small, new_path)
        yield new_path


@pytest.fixture(scope="function")
def readonly_project(project_and_changes):
    project_path, changes = project_and_changes
    qp = QuPathProject(project_path, mode="r")
    qp.__changes = changes
    yield qp


def iter_readonly_properties(obj):
    cls = obj.__class__
    for prop in dir(cls):
        cls_prop = getattr(cls, prop)
        if isinstance(cls_prop, property) and cls_prop.fset is None:
            yield prop
        if isinstance(cls_prop, cached_property):
            yield prop


@contextmanager
def assert_no_modification(qp):
    ctime, mtime = qp.timestamp_creation, qp.timestamp_modification
    yield qp
    project_path = qp.path.parent
    files = project_path.glob("**/*.*")
    assert files
    for file in files:
        p = str(file.absolute())
        assert qp.__changes.get(p, None) == file.stat().st_mtime, f"{str(file.relative_to(project_path))} was modified"
    assert qp.timestamp_creation == ctime
    assert qp.timestamp_modification == mtime


def test_fixture(readonly_project):
    pass


class _Accessor:
    def __init__(self, instance):
        self._if = set(filter(lambda x: not x.startswith('_'), dir(type(instance))))
        self._i = instance

    def setattr(self, item, value):
        self._if.discard(item)
        setattr(self._i, item, value)

    def callmethod(self, method, *args, ignore_exception=False, **kwargs):
        self._if.discard(method)
        try:
            return getattr(self._i, method)(*args, **kwargs)
        except BaseException as e:
            if ignore_exception:
                pass
            else:
                raise e

    def unused_public_interface(self):
        return self._if


def test_project_attrs_and_methods(readonly_project, copy_svs_small):
    with assert_no_modification(readonly_project) as qp:
        a = _Accessor(qp)

        assert qp._readonly

        # these are readonly anyways
        for ro_prop in iter_readonly_properties(qp):
            with pytest.raises(AttributeError):
                a.setattr(ro_prop, "abc")
        #with pytest.raises(AttributeError):
        #    a.setattr("images", [])

        # these dont do anything
        a.callmethod("is_readable")

        # modifiable: These should all raise AttributeError in readonly mode
        with pytest.raises(AttributeError):
            a.setattr("path_classes", ())

        # These should raise an IOError when readonly
        with pytest.raises(IOError):
            a.callmethod("add_image", copy_svs_small, allow_duplicates=True)
        with pytest.raises(IOError):
            a.callmethod("save")
        with pytest.raises(IOError):
            image_entry = qp.images[0]
            a.callmethod("remove_image", image_entry)

        # test that we can reassign uri's even in readonly mode
        cur_uri = qp.images[0].uri
        new_uri = ImageProvider.uri_from_path(copy_svs_small)
        assert cur_uri != new_uri
        # test that this does not change the project
        a.callmethod("update_image_paths", uri2uri={cur_uri: new_uri})
        assert qp.images[0].uri == new_uri

        # make sure everything is covered in case we extend the classes later
        assert not a.unused_public_interface()


def test_images_attrs_methods_readonly(readonly_project):
    with assert_no_modification(readonly_project) as qp:
        image = qp.images[0]
        i = _Accessor(image)

        assert image._readonly

        # readonly properties
        for ro_prop in iter_readonly_properties(image):
            with pytest.raises(AttributeError):
                i.setattr(ro_prop, "abc")

        # test writable properties
        with pytest.raises(AttributeError):
            i.setattr("description", "abc")
        with pytest.raises(AttributeError):
            i.setattr("image_name", "abc")
        with pytest.raises(AttributeError):
            i.setattr("image_type", "abc")

        # these do nothing
        i.callmethod("is_changed")
        i.callmethod("is_readable")

        # these need to be blocked
        with pytest.raises(AttributeError):
            i.setattr("metadata", {})
        with pytest.raises(AttributeError):
            i.setattr("properties", {})

        # methods that are not allowed
        with pytest.raises(IOError):
            i.callmethod("save")

        assert not i.unused_public_interface()


def test_images_metadata_and_properties(readonly_project):

    with assert_no_modification(readonly_project) as qp:
        image = qp.images[0]
        assert image._readonly

        with pytest.raises(AttributeError):
            image.metadata[12] = 3
        with pytest.raises(AttributeError):
            image.metadata.clear()
        with pytest.raises(AttributeError):
            del image.metadata[12]

        with pytest.raises(AttributeError):
            image.properties[12] = 3
        with pytest.raises(AttributeError):
            image.properties.clear()
        with pytest.raises(AttributeError):
            del image.properties[12]


def test_hierarchy(readonly_project):

    OME_NOT_INSTALLED = importlib.util.find_spec("ome_types") is None

    with assert_no_modification(readonly_project) as qp:
        image = qp.images[0]
        hierarchy = image.hierarchy
        assert hierarchy._readonly

        h = _Accessor(hierarchy)

        # readonly properties
        for ro_prop in iter_readonly_properties(hierarchy):
            with pytest.raises(AttributeError):
                h.setattr(ro_prop, "abc")

        # these do nothing
        h.callmethod("to_geojson")
        h.callmethod("to_ome_xml", ignore_exception=OME_NOT_INSTALLED)

        # these are not allowed in readonly
        with pytest.raises(IOError):
            h.callmethod("add_annotation", '--placeholder--')
        with pytest.raises(IOError):
            h.callmethod("add_detection", '--placeholder--')
        with pytest.raises(IOError):
            h.callmethod("add_tile", '--placeholder--')
        with pytest.raises(IOError):
            h.callmethod("load_geojson", '--placeholder--')

        # autoflush has no influence
        h.setattr("autoflush", False)
        h.callmethod("no_autoflush")
        h.callmethod("flush")

        assert not h.unused_public_interface()


def test_hierarchy_annotations_detections(readonly_project):
    with assert_no_modification(readonly_project) as qp:
        image = qp.images[0]
        hierarchy = image.hierarchy
        assert hierarchy._readonly

        with pytest.raises(IOError):
            hierarchy.annotations.add(1)
        with pytest.raises(IOError):
            hierarchy.annotations.discard(1)
        with pytest.raises(IOError):
            hierarchy.detections.add(1)
        with pytest.raises(IOError):
            hierarchy.detections.discard(1)
