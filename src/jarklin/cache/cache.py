# -*- coding=utf-8 -*-
r"""

"""
import os
import shutil
import typing as t
from pathlib import Path
from functools import cached_property
import orjson
from ..common.types import InfoEntry
from ._cache_generator import CacheGenerator
from .video import VideoCacheGenerator
from .gallery import GalleryCacheGenerator
from .util import is_video_file, is_gallery, is_deprecated, is_incomplete


__all__ = ['Cache']


class Cache:
    def __init__(self) -> None:
        self._shutdown: bool = False

    @cached_property
    def root(self) -> Path:
        return Path.cwd().absolute()

    @cached_property
    def jarklin_path(self) -> Path:
        return self.root.joinpath('.jarklin')

    @cached_property
    def jarklin_cache(self) -> Path:
        return self.jarklin_path.joinpath('cache')

    def run(self) -> None:
        self.invalidate()

    def shutdown(self) -> None:
        self._shutdown = True

    def remove(self, ignore_errors: bool = False) -> None:
        shutil.rmtree(self.jarklin_path, ignore_errors=ignore_errors)

    def iteration(self) -> None:
        self.invalidate()
        self.generate()

    def invalidate(self) -> None:
        for root, dirnames, files in os.walk(self.jarklin_cache):
            for dirname in dirnames:
                dest = Path(root, dirname)
                source = dest.relative_to(self.jarklin_cache)
                if not dest.joinpath("meta.json").is_file():
                    continue
                if not source.exists() or is_deprecated(source=source, dest=dest):
                    shutil.rmtree(dest)

    def generate(self) -> None:
        generator_jobs: t.List[CacheGenerator] = []
        info: t.List[InfoEntry] = []

        for root, dirnames, files in os.walk(self.root):
            # galleries
            for dirname in dirnames:
                if dirname.startswith("."):  # filter eg .jarklin/ out
                    dirnames.remove(dirname)
                    continue

                source = Path(root, dirname)
                dest = self.jarklin_cache.joinpath(source.relative_to(self.root))
                if is_gallery(source):
                    generator = GalleryCacheGenerator(source=source, dest=dest)
                    info.append(InfoEntry(
                        path=str(source.relative_to(self.root)),
                        name=source.name,
                        ext=source.suffix,
                        meta=generator.meta
                    ))
                    if is_deprecated(source=source, dest=dest) or is_incomplete(dest=dest):
                        generator_jobs.append(generator)
            # videos
            for filename in files:
                if filename.startswith("."):  # filter eg .jarklin.conf out
                    files.remove(filename)
                    continue

                source = Path(root, filename)
                dest = self.jarklin_cache.joinpath(source.relative_to(self.root))
                if is_video_file(source):
                    generator = VideoCacheGenerator(source=source, dest=dest)
                    info.append(InfoEntry(
                        path=str(source.relative_to(self.root)),
                        name=source.name,
                        ext=source.suffix,
                        meta=generator.meta
                    ))
                    if is_deprecated(source=source, dest=dest) or is_incomplete(dest=dest):
                        generator_jobs.append(generator)

        for generator in generator_jobs:
            if self._shutdown:
                break
            generator.generate()

        with open(self.root.joinpath('.jarklin/info.json'), 'wb') as fp:
            fp.write(orjson.dumps(info))
