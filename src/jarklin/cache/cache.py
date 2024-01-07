# -*- coding=utf-8 -*-
r"""

"""
import shutil
from pathlib import Path
from functools import cached_property
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

    @cached_property
    def root(self) -> Path:
        return Path.cwd().absolute()

    @cached_property
    def jarklin_path(self) -> Path:
        return self.root.joinpath('.jarklin')

    @cached_property
    def jarklin_cache(self) -> Path:
        return self.jarklin_path.joinpath('cache')

    def run(self):
        pass

    def remove(self, ignore_errors: bool = False):
        shutil.rmtree(self.jarklin_path, ignore_errors=ignore_errors)
