import platform
import sys
from argparse import ArgumentTypeError
from collections import defaultdict
from functools import partial
from pathlib import Path


# -- argparse improvements ---------------------------------------------

def subcommand(*arguments, parent):  # type: ignore
    """decorator helper for commandline"""
    def decorator(func):
        fn = func.__name__.rstrip('_')
        started_via_m = Path(sys.argv[0]).name == "__main__.py"
        subparser = parent.add_parser(
            name=fn,
            prog=f"python -m paquo {fn}" if started_via_m else f"paquo {fn}",
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


# -- create related commands -------------------------------------------

def list_project(path):
    """print information about the project"""
    from paquo.projects import QuPathProject

    with QuPathProject(path, mode='r') as qp:
        print("Project:", qp.name)
        print("Classes: #", len(qp.path_classes), sep='')
        for path_class in qp.path_classes:
            color = path_class.color
            color_str = f" [{color.to_hex()}]" if color else ""
            print(f"- {path_class.id}{color_str}")

        _md_keys = set()
        _md_value_len = defaultdict(int)
        print("Images: #", len(qp.images), sep='')
        for idx, image in enumerate(qp.images):
            print(f"- [{idx}] {image.image_name}")
            for k, v in image.metadata.items():
                _md_keys.add(k)
                _md_value_len[k] = max(_md_value_len[k], len(v), len(k))

        print("Project Metadata: #", len(_md_keys), sep='')
        if len(_md_keys):
            _md_keys = list(sorted(_md_keys))
            hdr = ["#    "]
            for _key in _md_keys:
                hdr.append(f"{_key:<{_md_value_len[_key]}}")
            print(" ".join(hdr))
            for idx, image in enumerate(qp.images):
                line = [f"- [{idx}]"]
                for _key in _md_keys:
                    val = image.metadata.get(_key, '')
                    line.append(f"{val:<{_md_value_len[_key]}}")
                print(" ".join(line))


# -- create related commands -------------------------------------------

def create_project(project_path, class_names_colors, images,
                   annotations_json_func=None,
                   remove_default_classes=False, force_write=False):
    """create a qupath project"""
    from paquo.classes import QuPathPathClass
    from paquo.images import QuPathImageType
    from paquo.projects import QuPathProject
    from paquo._logging import get_logger
    from paquo._utils import load_json_from_path

    _logger = get_logger(__name__)

    mode = 'x' if not force_write else 'w'

    if annotations_json_func is not None and not callable(annotations_json_func):
        raise ValueError("annotations_json_func should be callable")

    # noinspection PyTypeChecker
    with QuPathProject(project_path, mode=mode) as qp:
        if remove_default_classes:
            qp.path_classes = ()
        path_classes = list(qp.path_classes)
        for name, color in class_names_colors:
            path_classes.append(
                QuPathPathClass(name, color=color)
            )
        qp.path_classes = path_classes

        for image in images:
            qp_image = qp.add_image(image, image_type=QuPathImageType.BRIGHTFIELD_H_E)

            if annotations_json_func:
                annotations_jsons = annotations_json_func(Path(image).name)
                for annotations_json in annotations_jsons:
                    _logger.info(f"loading '{annotations_json}'")
                    geojson = load_json_from_path(annotations_json)
                    qp_image.hierarchy.load_geojson(geojson["annotations"])

        name = qp.name
    return name


# -- export related commands -------------------------------------------

def export_annotations(path, image_idx, pretty=False):
    """print annotations as geojson"""
    from paquo.projects import QuPathProject
    import pprint

    with QuPathProject(path, mode='r') as qp:
        image = qp.images[image_idx]
        data = image.hierarchy.to_geojson()
        if pretty:
            pprint.pprint(data)
        else:
            print(data)


# -- open related commands ------------------------------------------

def open_qupath(project_path):
    """launch qupath with the provided project"""
    import subprocess
    from zipfile import ZipFile
    from contextlib import contextmanager, ExitStack
    from tempfile import TemporaryDirectory
    from paquo._config import settings, to_kwargs
    from paquo.jpype_backend import find_qupath

    # retrieve the path of the qupath executable
    app_dir, _, _, _ = find_qupath(**to_kwargs(settings))
    system = platform.system()
    if system == "Linux":
        qupath, = Path(app_dir).parent.parent.joinpath("bin").glob("QuPath*")

    elif system == "Darwin":
        qupath, = Path(app_dir).parent.joinpath("MacOS").glob("QuPath*")

    elif system == "Windows":
        _qp_exes = list(Path(app_dir).parent.glob("QuPath*.exe"))
        assert len(_qp_exes) == 2, f"this should have returned two paths, got {_qp_exes}"
        qupath, = (qp for qp in _qp_exes if "console" in qp.stem)

    else:
        raise ValueError(f"Unknown platform {system}")

    @contextmanager
    def prepare_dir(path: Path):
        # unzip a qpzip file to a temporary directory
        if path.is_file() and path.suffix == ".qpzip":
            with ExitStack() as stack:
                tmp_path = stack.enter_context(
                    TemporaryDirectory(prefix="pado", suffix="qpzip")
                )
                with ZipFile(path) as qpzip:
                    qpzip.extractall(tmp_path)
                print(f"Extracted qpzip to {tmp_path}")
                yield Path(tmp_path)
                # dont clean up tmp if no errors were raised
                stack.pop_all()
        else:
            yield path

    with prepare_dir(Path(project_path)) as p:
        if p.is_dir():
            p /= "project.qpproj"
        if not (p.is_file() and p.suffix == ".qpproj"):
            raise ValueError(f"Not a qupath project: '{p}'")

        subprocess.run([qupath, '-p', p.resolve()])


# -- quzip related commands -------------------------------------------

def qpzip_project(project_path):
    """create a zip archive of a qupath project that can be used with `paquo open`"""
    import shutil
    from tempfile import TemporaryDirectory

    p = Path(project_path).expanduser().absolute()
    if p.is_dir():
        p /= "project.qpproj"
    if not (p.is_file() and p.suffix == ".qpproj"):
        raise ValueError(f"Not a qupath project: '{p}'")

    project_path = p.parent
    with TemporaryDirectory() as tmpdir:
        tmp_base_name = Path(tmpdir) / project_path.name
        tmp_zip = shutil.make_archive(tmp_base_name, "zip", root_dir=project_path, base_dir=".")
        qpzip = shutil.move(tmp_zip, project_path.with_suffix(".qpzip"))
    print(f"created: {qpzip}")
