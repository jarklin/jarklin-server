# -*- coding=utf-8 -*-
r"""

"""
import os
import json
import shutil
import logging
import typing as t
from pathlib import Path
from functools import cached_property
from filelock import FileLock
from configlib import ConfigInterface
from ..common.types import MediaEntry, ProblemEntry
from ..common import dot_ignore, scheduling
from .generator import CacheGenerator, GalleryCacheGenerator, VideoCacheGenerator
from .util import is_video_file, is_gallery, is_deprecated, get_creation_time, get_modification_time, is_cache
try:
    from better_exceptions import format_exception
except ModuleNotFoundError:
    from traceback import format_exception


__all__ = ['Cache']


logger = logging.getLogger(__name__)


class Cache:
    def __init__(self, config: ConfigInterface) -> None:
        self._shutdown_event = None
        self._config = config

    @cached_property
    def ignorer(self) -> 'dot_ignore.DotIgnore':
        return dot_ignore.DotIgnore(
            *self._config.getsplit('cache', 'ignore', fallback=[]),
            ".*",  # .jarklin/ | .jarklin.{ext}
            root=self.root,
        )

    @cached_property
    def root(self) -> Path:
        directory = Path.cwd().absolute()
        logger.info(f"Cache - root directory: {directory!s}")
        return directory

    @cached_property
    def jarklin_path(self) -> Path:
        directory = self.root.joinpath('.jarklin')
        directory.mkdir(parents=True, exist_ok=True)
        logger.info(f"Cache - jarklin directory: {directory!s}")
        return directory

    @cached_property
    def jarklin_cache(self) -> Path:
        directory = self.jarklin_path.joinpath('cache')
        directory.mkdir(parents=True, exist_ok=True)
        logger.info(f"Cache - jarklin cache directory: {directory!s}")
        return directory

    @cached_property
    def cache_lock(self) -> FileLock:
        return FileLock(self.jarklin_path / "cache.lock")

    # todo: replace with file-system-monitoring
    def run(self) -> None:
        import time
        import schedule

        scheduler = schedule.Scheduler()
        scheduler.every(1).hour.at(":00").do(self.iteration)
        shutdown_event, thread = scheduling.run_continuously(scheduler, interval=5)
        self._shutdown_event = shutdown_event
        try:
            while thread.is_alive():
                time.sleep(5)  # tiny bit larger for less resources
        except (KeyboardInterrupt, InterruptedError):
            logger.info("shutdown signal received. graceful shutdown")
            # attempt a graceful shutdown
            shutdown_event.set()
            while thread.is_alive():
                time.sleep(1)
        finally:
            self._shutdown_event = None

    def shutdown(self) -> None:
        if self._shutdown_event is None:
            raise RuntimeError("cache is not running")
        self._shutdown_event.set()

    def remove(self, ignore_errors: bool = False) -> None:
        r"""
        removes the jarklin-cache directory
        """
        shutil.rmtree(self.jarklin_cache, ignore_errors=ignore_errors)

    def iteration(self) -> None:
        r"""
        runs invalidate() and then generate() with simple lock against other instances
        """
        with self.cache_lock:
            self.invalidate()
            self.generate()

    def invalidate(self) -> None:
        r"""
        removes all cache entries that don't have their counterpart, are deprecated our incomplete
        """
        logger.info("cache.invalidate()")
        for root, dirnames, files in os.walk(self.jarklin_cache):
            if not dirnames and not files:
                os.rmdir(root)
                continue

            for dirname in dirnames:
                dest = Path(root, dirname)
                source = dest.relative_to(self.jarklin_cache)
                if not is_cache(fp=dest):
                    continue
                if (
                    not source.exists()
                    or is_deprecated(source=source, dest=dest)
                    or CacheGenerator.is_incomplete(fp=dest)
                ):
                    logger.info(f"removing {str(source)!r} from cache")
                    CacheGenerator.remove(fp=dest)

    def generate(self) -> None:
        r"""
        generates the missing or deprecated entries into the cache
        """
        logger.info("cache.generate()")
        media: t.List[MediaEntry] = []
        problems: t.List[ProblemEntry] = []
        generators: t.List[CacheGenerator] = self.find_generators()
        jobs: t.List[CacheGenerator] = []

        # adds existing cache entries into media-list
        for generator in generators:
            source = generator.source
            dest = generator.dest
            logger.debug(f"Cache - adding {generator}")
            if is_deprecated(source=source, dest=dest) or CacheGenerator.is_incomplete(fp=dest):
                jobs.append(generator)
            else:
                logger.debug(f"Cache - adding info for {source!s}")
                media.append(self._get_media_entry(generator))

        self._write_media(media=media)

        # generate missing cache entries and add them to media-list
        for generator in jobs:
            source = generator.source
            dest = generator.dest
            logger.info(f"Cache - generating {generator}")
            try:
                generator.generate()
            except Exception as error:
                logger.error(f"Cache: generation failed ({generator})", exc_info=error)
                problems.append(ProblemEntry(
                    file=str(source.relative_to(self.root)),
                    type=type(error).__name__,
                    description=str(error),
                    traceback='\n'.join(format_exception(type(error), error, error.__traceback__))
                ))
                self._write_problems(problems=problems)
            else:
                media.append(self._get_media_entry(generator=generator))
                self._write_media(media=media)

    def _get_media_entry(self, generator: CacheGenerator) -> MediaEntry:
        source, dest = generator.source, generator.dest
        return MediaEntry(
            path=str(source.relative_to(self.root)),
            name=source.stem if source.is_file() else source.name,
            ext=source.suffix if source.is_file() else "",
            creation_time=get_creation_time(source),
            modification_time=get_modification_time(source),
            meta=json.loads(dest.joinpath("meta.json").read_bytes()),
        )

    def _write_media(self, media: t.List[MediaEntry]) -> None:
        logger.info("Cache - updating media.json")
        with open(self.jarklin_path / 'media.json', 'w') as fp:
            fp.write(json.dumps(media))

    def _write_problems(self, problems: t.List[ProblemEntry]) -> None:
        logger.info("Cache - updating problems.json")
        with open(self.jarklin_path / 'problems.json', 'w') as fp:
            fp.write(json.dumps(problems))

    def find_generators(self) -> t.List[CacheGenerator]:
        r"""
        finds all possible source-entries that should be in the cache
        """
        logger.info("Collecting Generators")
        generators: t.List[CacheGenerator] = []

        for root, dirnames, filenames in os.walk(self.root):
            # galleries
            for dirname in dirnames[:]:
                source = Path(root, dirname)
                dest = self.jarklin_cache.joinpath(source.relative_to(self.root))

                if self.ignorer.ignored(source):
                    logger.debug(f"Cache - ignoring {source!s}")
                    dirnames.remove(dirname)
                    continue

                if is_gallery(source):
                    logger.debug(f"Cache - found gallery {source!s}")
                    generators.append(GalleryCacheGenerator(source=source, dest=dest, config=self._config))

            # videos
            for filename in filenames[:]:
                source = Path(root, filename)
                dest = self.jarklin_cache.joinpath(source.relative_to(self.root))

                if self.ignorer.ignored(source):
                    logger.debug(f"Cache - ignoring {source!s}")
                    filenames.remove(filename)
                    continue

                if is_video_file(source):
                    logger.debug(f"Cache - found video {source!s}")
                    generators.append(VideoCacheGenerator(source=source, dest=dest, config=self._config))

        return sorted(generators, key=lambda g: str(g.source).lower())
