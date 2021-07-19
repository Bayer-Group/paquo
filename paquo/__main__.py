import argparse
import functools
import os
import sys
import tempfile
from contextlib import redirect_stdout
from itertools import repeat
from pathlib import Path

from paquo._cli import subcommand, argument, DirectoryType, \
    config_print_settings, config_print_defaults, list_project, export_annotations, create_project, open_qupath, \
    qpzip_project
from paquo._config import PAQUO_CONFIG_FILENAME, get_searchtree

# noinspection PyTypeChecker
parser = argparse.ArgumentParser(
    prog="python -m paquo" if Path(sys.argv[0]).name == "__main__.py" else None,
    description="""\
 ██████╗  █████╗  ██████╗ ██╗   ██╗ ██████╗ 
 ██╔══██╗██╔══██╗██╔═══██╗██║   ██║██╔═══██╗
 ██████╔╝███████║██║   ██║██║   ██║██║   ██║
 ██╔═══╝ ██╔══██║██║▄▄ ██║██║   ██║██║   ██║
 ██║     ██║  ██║╚██████╔╝╚██████╔╝╚██████╔╝
 ╚═╝     ╚═╝  ╚═╝ ╚══▀▀═╝  ╚═════╝  ╚═════╝ """,
    epilog="#### [PA]thological [QU]path [O]bsession ####",
    formatter_class=argparse.RawDescriptionHelpFormatter,
)
subparsers = parser.add_subparsers(dest="cmd", title="paquo command")
subcommand = functools.partial(subcommand, parent=subparsers)
parser.add_argument('--version', action='store_true', help="print paquo version")
parser.add_argument('--qupath-version', action='store_true', help="print qupath version")


def main(commandline=None):
    """main command line argument handling"""
    args = parser.parse_args(commandline)
    if args.cmd is None:
        if args.version:
            from paquo import __version__
            print(f"{__version__}")
        if args.qupath_version:
            from paquo.java import qupath_version
            print(f"{qupath_version!s}")
        if not (args.version or args.qupath_version):
            parser.print_help()
    else:
        from paquo import settings
        from logging.config import dictConfig
        lvl = 'INFO'
        if settings.cli_force_log_level_error:
            lvl = 'ERROR'
        dictConfig({
            'version': 1,
            'handlers': {
                'console': {
                    'level': 'DEBUG',
                    'class': 'logging.StreamHandler',
                },
            },
            "loggers": {
                'paquo': {
                    'level': lvl,
                    'handlers': ['console'],
                },
                'qupath': {
                    'level': 'CRITICAL',
                    'handlers': ['console'],
                },
            },
        })
        return args.cmd_func(args)
    return 0


@subcommand(
    argument('-l', '--list', action='store_true', help="list the paquo config"),
    argument('--default', action='store_true', help="default instead of current config"),
    argument(
        '-o', '--output',
        action='store',
        type=DirectoryType(), dest='output',
        help="directory where configuration is written to"
    ),
    argument('--force', action='store_true', help="force overwrite existing config"),
    argument('--search-tree', action='store_true', help="list all locations searched for config"),
)
def config(args, subparser):
    """handle paquo configuration"""
    if not (args.list or args.search_tree):
        print(subparser.format_help())
        return 0

    if args.search_tree:
        print(f"paquo is scanning these dirs for '{PAQUO_CONFIG_FILENAME}':")
        for idx, location in enumerate(get_searchtree()):
            print(f"{idx}.", location)
        return 0

    if args.default:
        config_print = config_print_defaults
    else:
        config_print = config_print_settings

    if args.output is None:
        config_print()
    else:
        out_fn = args.output / PAQUO_CONFIG_FILENAME
        mode = "x" if not args.force else "w"
        # write to file
        try:
            with out_fn.open(mode) as f:
                with redirect_stdout(f):
                    config_print()
        except FileExistsError:
            print(f"ERROR: file {out_fn} exists! use --force to overwrite")
            return 1
    return 0


@subcommand(
    argument('project_path', nargs='?', default=None, help="path to your qupath project file/folder"),
)
def list_(args, subparser):
    """list contents of a qupath project"""
    if not args.project_path:
        print(subparser.format_help())
        return 0
    try:
        list_project(args.project_path)
    except FileNotFoundError as err:
        print(str(err), file=sys.stderr)
        return 1
    return 0


@subcommand(
    argument('project_path', nargs='?', default=None, help="path to new qupath project"),
    argument('--classes', nargs='*', help="path classes to add to project"),
    argument('--class-colors', nargs='*', help="path class colors in order of classes"),
    argument('--remove-default-classes', action="store_true", help="don't add default classes"),
    argument('--images', nargs='*', help="images to add to project"),
    argument('--force', action="store_true", help="force overwrite existing projects"),
)
def create(args, subparser):
    """create a new qupath project"""
    if not args.project_path:
        print(subparser.format_help())
        return 0

    if args.class_colors and len(args.class_colors) != len(args.classes):
        print("ERROR: need to specify same number of colors as classes")
        return 1

    if args.classes and len(args.classes) != len(set(args.classes)):
        print("ERROR: classes have to be unique")
        return 1

    class_names_colors = zip(args.classes or [], args.class_colors or repeat(None))

    images = args.images or []
    for image in images:
        if not Path(image).is_file():
            print(f"ERROR: image {image} is not a file")
            return 1

    try:
        name = create_project(
            args.project_path,
            class_names_colors=class_names_colors,
            images=images,
            remove_default_classes=args.remove_default_classes,
            force_write=args.force
        )
    except FileExistsError:
        print(f"ERROR: project {args.project_path} exists! use --force to overwrite")
        return 1
    print(f"project '{name}' created")
    return 0


@subcommand(
    argument('project_path', nargs='?', default=None, help="path to your qupath project file/folder"),
    argument('--image-idx', '-i', default=None, type=int, help="index of a qupath image"),
    argument(
        '-o', '--output',
        action='store',
        type=argparse.FileType('w'), dest='output',
        help="directory where configuration is written to"
    ),
    argument('--pretty', action='store_true', help="pretty format the output"),
)
def export(args, subparser):
    """export annotations of a qupath project image to geojson"""
    if args.project_path is None or args.image_idx is None:
        print(subparser.format_help())
        return 0

    try:
        if args.output is None:
            export_annotations(args.project_path, args.image_idx, args.pretty)
        else:
            with redirect_stdout(args.output):
                export_annotations(args.project_path, args.image_idx, args.pretty)
    except IndexError:
        print(f"ERROR: image index {args.image_idx} out of range")
        return 1
    return 0


@subcommand(
    argument('project_path', nargs='?', default=None, help="path to your qupath project file/folder"),
)
def open_(args, subparser):
    """open qupath with a specified project"""
    if args.project_path is None:
        print(subparser.format_help())
        return 0

    open_qupath(args.project_path)
    return 0


@subcommand(
    argument('project_path', nargs='?', default=None, help="path to your qupath project file/folder"),
)
def qpzip(args, subparser):
    """create a qpzip archive of a project"""
    if args.project_path is None:
        print(subparser.format_help())
        return 0

    qpzip_project(args.project_path)
    return 0


@subcommand(
    argument('image', nargs='?', default=None, help="path to image"),
    argument('--annotations', action="append", help="annotations for image"),
    argument('--annotations-cmd', type=str, help="automatically choose annotations if available")
)
def quickview(args, subparser):
    """open an image in qupath"""
    import subprocess

    if not args.image:
        print(subparser.format_help())
        return 0

    image = Path(args.image)
    if not image.is_file():
        print(f"ERROR: image {args.image} is not a file")
        return 1

    f_annotations = None
    if args.annotations:
        def f_annotations(name):
            if name != image.name:
                return []
            return list(args.annotations)

    f_annotations_cmd = None
    if args.annotations_cmd:
        def f_annotations_cmd(name):
            import shlex
            _cmd = shlex.split(f"{args.annotations_cmd} {name}")
            print("annotations", _cmd)
            output = subprocess.run(_cmd, env=os.environ, check=True, capture_output=True)
            return [line.decode() for line in output.stdout.splitlines() if line.strip()]

    cmd = None
    if f_annotations_cmd or f_annotations:
        def cmd(name):
            l = []
            if f_annotations:
                l.extend(f_annotations(name))
            if f_annotations_cmd:
                l.extend(f_annotations_cmd(name))
            return l

    with tempfile.TemporaryDirectory() as project_path:
        create_project(project_path, class_names_colors=[], images=[image], annotations_json_func=cmd)
        open_qupath(project_path)

    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
