# -*- coding=utf-8 -*-
r"""

"""
from .._lib import json
try:
    import magic
except ImportError:
    print("warning: libmagic not found")
    magic = None


__all__ = ['Cache']


class Cache:
    def __init__(self):
        pass

    def run(self):
        pass

    def remove(self):
        pass
