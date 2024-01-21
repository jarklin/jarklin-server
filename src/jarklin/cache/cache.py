# -*- coding=utf-8 -*-
r"""

"""
import os
import json
import shutil
import typing as t
from pathlib import Path
from functools import cached_property
from configlib import ConfigInterface
from ..common.types import InfoEntry
from ..common.dot_ignore import DotIgnore
from ._cache_generator import CacheGenerator
from .video import VideoCacheGenerator
from .gallery import GalleryCacheGenerator
from .util import is_video_file, is_gallery, is_deprecated, is_incomplete


__all__ = ['Cache']


class Cache:
    def __init__(self, config: ConfigInterface) -> None:
        self._shutdown: bool = False
        self._config = config

    @cached_property
    def ignorer(self) -> 'DotIgnore':
        return DotIgnore.from_iterable(
            *self._config.getsplit('cache', 'ignore', fallback=[]),
            ".*",  # .jarklin/ | .jarklin.{ext}
        )

    @cached_property
    def root(self) -> Path:
        return Path.cwd().absolute()

    @cached_property
    def jarklin_path(self) -> Path:
        directory = self.root.joinpath('.jarklin')
        directory.mkdir(parents=True, exist_ok=True)
        return directory

    @cached_property
    def jarklin_cache(self) -> Path:
        directory = self.jarklin_path.joinpath('cache')
        directory.mkdir(parents=True, exist_ok=True)
        return directory

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
                if self.ignorer.ignored(dest):
                    dirnames.remove(dirname)
                    continue
                source = dest.relative_to(self.jarklin_cache)
                if not dest.joinpath("meta.json").is_file():
                    continue
                if not source.exists() or is_deprecated(source=source, dest=dest):
                    shutil.rmtree(dest)

    def generate(self) -> None:
        info: t.List[InfoEntry] = []
        generators: t.List[CacheGenerator] = self.find_generators()

        for generator in generators:
            source = generator.source
            dest = generator.dest
            if is_deprecated(source=source, dest=dest) or is_incomplete(dest=dest):
                generator.generate()
            info.append(InfoEntry(
                path=str(source.relative_to(self.root)),
                name=source.stem,
                ext=source.suffix,
                meta=json.loads(dest.joinpath("meta.json").read_bytes()),
            ))

        with open(self.root.joinpath('.jarklin/info.json'), 'w') as fp:
            fp.write(json.dumps(info))

    def find_generators(self) -> t.List[CacheGenerator]:
        generators: t.List[CacheGenerator] = []

        for root, dirnames, filenames in os.walk(self.root):
            # galleries
            for dirname in dirnames:
                source = Path(root, dirname)
                dest = self.jarklin_cache.joinpath(source.relative_to(self.root))

                if self.ignorer.ignored(source):
                    dirnames.remove(dirname)
                    continue

                if is_gallery(source):
                    generators.append(GalleryCacheGenerator(source=source, dest=dest, config=self._config))
            # videos
            for filename in filenames:
                source = Path(root, filename)
                dest = self.jarklin_cache.joinpath(source.relative_to(self.root))

                if self.ignorer.ignored(source):
                    filenames.remove(filename)
                    continue

                if is_video_file(source):
                    generators.append(VideoCacheGenerator(source=source, dest=dest, config=self._config))

        return generators
