from argparse import ArgumentTypeError
from functools import partial
from pathlib import Path


# -- argparse improvements ---------------------------------------------

def subcommand(*arguments, parent):  # type: ignore
    """decorator helper for commandline"""
    def decorator(func):
        subparser = parent.add_parser(
            name=func.__name__,
            prog=f"python -m paquo {func.__name__}",
            help=func.__doc__,
        )
        for args, kwargs in arguments:
            subparser.add_argument(*args, **kwargs)
        subparser.set_defaults(cmd_func=partial(func, subparser=subparser))
        return func
    return decorator


def argument(*args, **kwargs):
    """argument helper for subcommand"""
    return args, kwargs


class DirectoryType:
    """Directory parsing for argparse"""
    def __call__(self, cmd_input: str):
        p = Path(cmd_input)
        if p.is_dir():
            return p
        raise ArgumentTypeError(f"'{cmd_input}' is not a directory")


# -- config related commands -------------------------------------------

def config_print_settings():
    """print the current configuration"""
    # we'll use the current public dynaconf api so that we don't need to import our own
    # toml... that means we need to go via a temporary file to dump the current config,
    # because dynaconf doesn't support it otherwise...
    # github.com/rochacbruno/dynaconf/blob/68df27d2/dynaconf/loaders/toml_loader.py#L56
    import tempfile
    from dynaconf import loaders
    from dynaconf.utils.boxing import DynaBox
    from paquo import settings
    from paquo._config import to_kwargs

    data = DynaBox(settings.as_dict(internal=False))
    # we create a temporary dir and write to a toml file
    # note: this is to workaround the fact that using NamedTemporaryFile will
    #   error under windows due to loaders.write calling open on the file
    with tempfile.TemporaryDirectory() as tmpdir:
        fn = str(Path(tmpdir) / ".paquo.temporary.toml")  # suffix determines loader
        loaders.write(fn, to_kwargs(data))
        with open(fn, 'rt') as f:
            output = f.read()

    print("# current paquo configuration")
    print("# ===========================")
    print("# format: TOML")
    print(output)


def config_print_defaults():
    """print the default paquo configuration"""
    try:
        from importlib.resources import read_text  # type: ignore
    except ImportError:
        # noinspection PyUnresolvedReferences
        from importlib_resources import read_text  # type: ignore
    from paquo._config import settings

    output = read_text(
        "paquo",
        ".paquo.defaults.toml",
        encoding=settings.ENCODING_FOR_DYNACONF
    )
    print(output)
