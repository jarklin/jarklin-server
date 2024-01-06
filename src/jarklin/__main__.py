# -*- coding=utf-8 -*-
r"""

"""
import sys
import argparse as ap
from . import __version__


parser = ap.ArgumentParser('jarklin', description=__doc__)
parser.set_defaults(fn=parser.print_help)
parser.add_argument('-v', '--version', action='version', version=__version__)


def main():
    arguments = vars(parser.parse_args())
    fn = arguments.pop('fn')
    return fn(**arguments)


if __name__ == '__main__':
    sys.exit(main() or 0)
