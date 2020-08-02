try:
    from importlib.resources import path as importlib_resources_path
except ImportError:
    # noinspection PyUnresolvedReferences
    from importlib_resources import path as importlib_resources_path

from pathlib import Path

from dynaconf import Dynaconf, Validator


with importlib_resources_path("paquo", ".paquo.defaults.toml") as default_config:

    settings = Dynaconf(
        envvar_prefix="PAQUO",
        settings_file=['.paquo.toml'],
        root_path=Path.home(),
        core_loaders=['TOML'],
        preload=[str(default_config.absolute())],
        validators=[
            Validator("java_opts", is_type_of=(list, tuple, str)),
            Validator("qupath_search_dirs", is_type_of=(list, tuple, str)),
            Validator("qupath_search_conda", is_type_of=(bool, int), is_in=(0, 1)),
            Validator("qupath_prefer_conda", is_type_of=(bool, int), is_in=(0, 1)),
            Validator("mock_backend", is_type_of=(bool, int), is_in=(0, 1)),
        ]
    )
