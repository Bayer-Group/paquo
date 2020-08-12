import io
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


def test_no_args():
    assert main([]) == 0


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


def test_export_cmd(tmpdir, tmp_path, svs_small):
    from shapely.geometry import Point
    from paquo.projects import QuPathProject
    from paquo.images import QuPathImageType

    with QuPathProject(tmp_path) as qp:
        entry = qp.add_image(svs_small, image_type=QuPathImageType.BRIGHTFIELD_OTHER)
        entry.hierarchy.add_annotation(
            roi=Point(500, 500)
        )

    # help
    assert run(main, ['export']).return_code == 0
    # wrong index
    assert run(main, ['export', str(tmp_path), '-i', '26']).return_code == 1
    # get index
    assert run(main, ['export', str(tmp_path), '-i', '0']).return_code == 0
    # check pretty print
    assert run(main, ['export', str(tmp_path), '-i', '0', '--pretty']).return_code == 0
    # check file output
    with tmpdir.as_cwd():
        assert run(main, ['export', str(tmp_path), '-i', '0', '--pretty', '-o', 'data.geojson']).return_code == 0
        assert (Path(tmpdir) / "data.geojson").is_file()
