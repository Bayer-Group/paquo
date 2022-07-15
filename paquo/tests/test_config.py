import os
from unittest import mock

from paquo._config import _get_settings
from paquo._config import to_kwargs


def test_double_underscore_envvar_override():
    with mock.patch.dict(os.environ, {"PAQUO__QUPATH_DIR": "/somewhere"}):
        settings = _get_settings()
        kw = to_kwargs(settings)
    assert kw["qupath_dir"] == "/somewhere"
    assert "_qupath_dir" not in kw


def test_single_underscore_envvar_override():
    with mock.patch.dict(os.environ, {"PAQUO_QUPATH_DIR": "/somewhere"}):
        settings = _get_settings()
        kw = to_kwargs(settings)
    assert kw["qupath_dir"] == "/somewhere"
