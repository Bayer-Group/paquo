import io
import tempfile
from collections import namedtuple
from contextlib import redirect_stdout
from pathlib import Path

import pytest

from paquo.__main__ import main

_Output = namedtuple("_Output", "return_code stdout")


def run(func, argv1):
    f = io.StringIO()
    with redirect_stdout(f):
        return_code = func(argv1)
    return _Output(return_code, f.getvalue().rstrip())


@pytest.fixture(scope="module")
def project_with_data(svs_small):
    from shapely.geometry import Point
    from paquo.classes import QuPathPathClass
    from paquo.images import QuPathImageType
    from paquo.projects import QuPathProject

    with tempfile.TemporaryDirectory(prefix='paquo-') as tmp_path:
        with QuPathProject(tmp_path, mode='x') as qp:
            entry = qp.add_image(svs_small, image_type=QuPathImageType.BRIGHTFIELD_OTHER)
            entry.hierarchy.add_annotation(
                roi=Point(500, 500)
            )
            pcs = list(qp.path_classes)
            pcs.append(QuPathPathClass("myclass"))
            qp.path_classes = pcs
            entry.metadata["mykey"] = "myval"
            qp.save()
            yield qp.path


def test_no_args():
    assert main([]) == 1


def test_version():
    from paquo import __version__
    assert run(main, ['--version']) == (0, __version__)


def test_config_cmd(tmp_path):
    assert main(['config']) == 0  # shows help

    assert run(main, ['config', '-l']).stdout
    assert run(main, ['config', '-l', '--default']).stdout

    paquo_toml = Path(tmp_path) / ".paquo.toml"
    paquo_toml.touch()

    # error when folder does not exist
    with pytest.raises(SystemExit):
        assert run(main, ['config', '-l', '-o', str(tmp_path / "not-there")])
    # error when file exists
    assert run(main, ['config', '-l', '-o', str(tmp_path)]).return_code == 1
    # force allows overwrite
    assert run(main, ['config', '-l', '-o', str(tmp_path), '--force']).return_code == 0
    # allow showing all folders where you can store you paquo config
    assert run(main, ['config', '--search-tree']).return_code == 0


def test_list_cmd(project_with_data):
    assert run(main, ['list']).return_code == 0
    assert run(main, ['list', 'somewhere-non-existent']).return_code != 0
    assert run(main, ['list', str(project_with_data)]).return_code == 0


def test_create_cmd_errors(tmpdir):
    with tmpdir.as_cwd():
        # test help
        assert run(main, ['create']).return_code == 0
        # test classes class_colors mismatch
        assert run(main, ['create', 'test_project', '--classes', 'A', 'B', '--class-colors', '1']).return_code != 0
        # test duplicate classes
        assert run(main, ['create', 'test_project', '--classes', 'A', 'B', 'A']).return_code != 0
        # test image not there
        assert run(main, ['create', 'test_project', '--images', 'not-there.svs']).return_code != 0
        # test project is there
        p = Path(tmpdir) / "test_project"
        p.mkdir()
        qp = p / "project.qpproj"
        qp.touch()
        assert run(main, ['create', 'test_project', '--classes', 'A', 'B']).return_code != 0


def test_create_cmd_works(tmpdir, svs_small):
    with tmpdir.as_cwd():
        options = [
            'create',
            'test_project',
            '--classes', 'A',
            '--remove-default-classes',
            '--images', str(svs_small),
        ]
        assert run(main, options).return_code == 0
        assert (Path(tmpdir) / "test_project" / "project.qpproj").is_file()


def test_export_cmd(tmpdir, project_with_data):
    proj_path = project_with_data
    # help
    assert run(main, ['export']).return_code == 0
    # wrong index
    assert run(main, ['export', str(proj_path), '-i', '26']).return_code == 1
    # get index
    assert run(main, ['export', str(proj_path), '-i', '0']).return_code == 0
    # check pretty print
    assert run(main, ['export', str(proj_path), '-i', '0', '--pretty']).return_code == 0
    # check file output
    with tmpdir.as_cwd():
        assert run(main, ['export', str(proj_path), '-i', '0', '--pretty', '-o', 'data.geojson']).return_code == 0
        assert (Path(tmpdir) / "data.geojson").is_file()
