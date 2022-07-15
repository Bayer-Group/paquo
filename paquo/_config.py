import tempfile
from importlib.resources import path as importlib_resources_path
from pathlib import Path
from typing import Any
from typing import Dict
from typing import List

from dynaconf import Dynaconf
from dynaconf import Validator
from dynaconf import loaders
from dynaconf.base import Settings
from dynaconf.utils import files as _files
from dynaconf.utils.boxing import DynaBox

PAQUO_CONFIG_FILENAME = '.paquo.toml'

_PAQUO_FIX_CONFIG_KEYS = {
    # recover prefixed keys due to dynaconf weirdness
    "_qupath_dir",
    "_qupath_search_dirs",
    "_qupath_search_dir_regex",
    "_qupath_search_conda",
    "_qupath_prefer_conda",
    "_java_opts",
    "_safe_truncate",
    "_mock_backend",
    "_cli_force_log_level_error",
    "_warn_microsoft_store_python",
}


def to_kwargs(s: "Settings | DynaBox") -> Dict[str, Any]:
    """convert dynaconf settings to lowercase"""
    dct = s.to_dict()
    out = {}
    for key, value in dct.items():
        k = key.lower()
        if k in _PAQUO_FIX_CONFIG_KEYS:
            k = k[1:]
        out[k] = value
    return out


def to_toml(s: Settings) -> str:
    """convert dynaconf settings to a toml str"""
    # we'll use the current public dynaconf api so that we don't need to import our own
    # toml... that means we need to go via a temporary file to dump the current config,
    # because dynaconf doesn't support it otherwise...
    # github.com/rochacbruno/dynaconf/blob/68df27d2/dynaconf/loaders/toml_loader.py#L56
    data = DynaBox(s.as_dict(internal=False))

    # we create a temporary dir and write to a toml file
    # note: this is to workaround the fact that using NamedTemporaryFile will
    #   error under windows due to loaders.write calling open on the file
    with tempfile.TemporaryDirectory() as tmpdir:
        fn = str(Path(tmpdir) / ".paquo.temporary.toml")  # suffix determines loader
        loaders.write(fn, to_kwargs(data))
        with open(fn) as f:
            output = f.read()
    return output


def _get_settings() -> Dynaconf:
    """load default settings instance"""
    with importlib_resources_path("paquo", ".paquo.defaults.toml") as default_config:

        settings = Dynaconf(
            envvar_prefix="PAQUO",
            settings_file=[PAQUO_CONFIG_FILENAME],
            root_path=Path.cwd(),
            core_loaders=['TOML'],
            preload=[str(default_config.absolute())],
            validators=[
                Validator("java_opts", is_type_of=(list, tuple, str)),
                Validator("qupath_search_dirs", is_type_of=(list, tuple, str)),
                Validator("qupath_search_conda", is_type_of=(bool, int), is_in=(0, 1)),
                Validator("qupath_prefer_conda", is_type_of=(bool, int), is_in=(0, 1)),
                Validator("safe_truncate", is_type_of=(bool, int), is_in=(0, 1)),
                Validator("mock_backend", is_type_of=(bool, int), is_in=(0, 1)),
                Validator("cli_force_log_level_error", is_type_of=(bool, int), is_in=(0, 1)),
            ]
        )
    return settings


settings = _get_settings()


def get_searchtree() -> List[str]:
    """return the current search tree for the settings"""
    if not settings.configured:
        settings.configure()  # pragma: no cover
    # note: SEARCHTREE is updated after configure
    searchtree: List[str] = getattr(_files, 'SEARCHTREE', [])
    return searchtree
