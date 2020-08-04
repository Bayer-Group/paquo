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
