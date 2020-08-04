import argparse
import functools
from contextlib import redirect_stdout

from paquo._cli import subcommand, argument, DirectoryType, \
    config_print_settings, config_print_defaults
from paquo._config import PAQUO_CONFIG_FILENAME, get_searchtree

# noinspection PyTypeChecker
parser = argparse.ArgumentParser(
    prog="python -m paquo",
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
parser.add_argument('--version', action='store_true', help="print version")


def main(commandline=None):
    """main command line argument handling"""
    args = parser.parse_args(commandline)
    if args.cmd is None:
        if args.version:
            from paquo import __version__
            print(f"{__version__}")
        else:
            parser.print_help()
    else:
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
    """handle configuration"""
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


if __name__ == "__main__":  # pragma: no cover
    import sys
    sys.exit(main())
