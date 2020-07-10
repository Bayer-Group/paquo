import pytest
import tempfile

from paquo.objects.projects import QuPathProject


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
