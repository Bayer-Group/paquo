import hashlib
import pathlib
import shutil
import tempfile
import urllib.request

# noinspection PyPackageRequirements
import pytest
from paquo.objects.projects import QuPathProject

OPENSLIDE_APERIO_TEST_IMAGES_URL = "http://openslide.cs.cmu.edu/download/openslide-testdata/Aperio/"


def md5(fn):
    m = hashlib.md5()
    with open(fn, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            m.update(chunk)
    return m.hexdigest()


@pytest.fixture(scope='session')
def svs_small():
    small_image = "CMU-1-Small-Region.svs"
    small_image_md5 = "1ad6e35c9d17e4d85fb7e3143b328efe"
    data_dir = pathlib.Path(__file__).parent / "data"

    data_dir.mkdir(parents=True, exist_ok=True)
    img_fn = data_dir / small_image

    if not img_fn.is_file():
        # download svs from openslide test images
        url = OPENSLIDE_APERIO_TEST_IMAGES_URL + small_image
        with urllib.request.urlopen(url) as response, open(img_fn, 'wb') as out_file:
            shutil.copyfileobj(response, out_file)

    if md5(img_fn) != small_image_md5:
        shutil.rmtree(img_fn)
        pytest.skip("incorrect md5")
    else:
        yield img_fn.absolute()


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
