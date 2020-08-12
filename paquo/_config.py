try:
    from importlib.resources import path as importlib_resources_path  # type: ignore
except ImportError:
    # noinspection PyUnresolvedReferences
    from importlib_resources import path as importlib_resources_path  # type: ignore

from pathlib import Path
from typing import Any, Dict, List

from dynaconf import Dynaconf, Validator
from dynaconf.base import Settings
from dynaconf.utils import files as _files

PAQUO_CONFIG_FILENAME = '.paquo.toml'


def to_kwargs(s: Settings) -> Dict[str, Any]:
    """convert dynaconf settings to lowercase"""
    return {k.lower(): v for k, v in s.to_dict().items()}


with importlib_resources_path("paquo", ".paquo.defaults.toml") as default_config:

    settings = Dynaconf(
        envvar_prefix="PAQUO",
        settings_file=[PAQUO_CONFIG_FILENAME],
        root_path=Path.home(),
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


def get_searchtree() -> List[str]:
    """return the current search tree for the settings"""
    if not settings.configured:
        settings.configure()  # pragma: no cover
    # note: SEARCHTREE is updated after configure
    searchtree: List[str] = getattr(_files, 'SEARCHTREE', [])
    return searchtree
