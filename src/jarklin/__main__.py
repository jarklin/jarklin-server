# -*- coding=utf-8 -*-
r"""

"""
import sys
import argparse as ap
from . import __version__
from . import _commands as commands
try:
    import better_exceptions
    better_exceptions.hook()
except ModuleNotFoundError:
    pass

# ==================================================================================================================== #

parser = ap.ArgumentParser('jarklin', description=__doc__, formatter_class=ap.ArgumentDefaultsHelpFormatter)
parser.set_defaults(fn=parser.print_help)
parser.add_argument('-v', '--version', action='version', version=__version__)
subparsers = parser.add_subparsers()

# ==================================================================================================================== #

web_parser = subparsers.add_parser('web')
web_parser.set_defaults(fn=web_parser.print_help)
web_subparsers = web_parser.add_subparsers()

# -------------------------------------------------------------------------------------------------------------------- #

web_run_parser = web_subparsers.add_parser('run')
web_run_parser.set_defaults(fn=commands.web.run)
web_run_parser.add_argument('--host', type=str)
web_run_parser.add_argument('--port', type=int)
web_run_parser.add_argument('--dev', '--development', action=ap.BooleanOptionalAction, dest="development",
                            help="start in debug mode")

# ==================================================================================================================== #

cache_parser = subparsers.add_parser('cache')
cache_parser.set_defaults(fn=cache_parser.print_help)
cache_subparsers = cache_parser.add_subparsers()

# -------------------------------------------------------------------------------------------------------------------- #

cache_run_parser = cache_subparsers.add_parser('run')
cache_run_parser.set_defaults(fn=commands.cache.run)

# -------------------------------------------------------------------------------------------------------------------- #

cache_generate_parser = cache_subparsers.add_parser('generate')
cache_generate_parser.set_defaults(fn=commands.cache.generate)

# -------------------------------------------------------------------------------------------------------------------- #

cache_remove_parser = cache_subparsers.add_parser('remove')
cache_remove_parser.set_defaults(fn=commands.cache.remove)
cache_remove_parser.add_argument('-I', '--ignore-errors', action=ap.BooleanOptionalAction, default=False,
                                 help="ignore errors during removal")

# ==================================================================================================================== #

util_download_web_ui_parser = subparsers.add_parser('download-web-ui')
util_download_web_ui_parser.set_defaults(fn=commands.util.download_web_ui)
util_download_web_ui_parser.add_argument('--dest', type=str,
                                         help="where to place the file")
# util_download_web_ui_parser.add_argument('-x', '--unzip', action=ap.BooleanOptionalAction,
#                                          help="whether or not to unzip the download web-ui archive")
util_download_web_ui_parser.add_argument('--source', type=str,
                                         help="download source (`user/repo` | `https://...`)")

# ==================================================================================================================== #


def main():
    arguments = vars(parser.parse_args())
    fn = arguments.pop('fn')
    return fn(**arguments)


if __name__ == '__main__':
    sys.exit(main() or 0)
