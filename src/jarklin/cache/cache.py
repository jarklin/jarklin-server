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
from configlib import ConfigInterface
from ..common.types import InfoEntry, ProblemEntry
from ..common import dot_ignore, scheduling
from ._cache_generator import CacheGenerator
from .video import VideoCacheGenerator
from .gallery import GalleryCacheGenerator
from .util import is_video_file, is_gallery, is_deprecated, get_creation_time, get_modification_time, is_cache
try:
    from better_exceptions import format_exception
except ModuleNotFoundError:
    from traceback import format_exception


__all__ = ['Cache']


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
            logging.info("shutdown signal received. graceful shutdown")
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
        shutil.rmtree(self.jarklin_cache, ignore_errors=ignore_errors)

    def iteration(self) -> None:
        self.invalidate()
        self.generate()

    def invalidate(self) -> None:
        logging.info("cache.invalidate()")
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
                    logging.info(f"removing {str(source)!r} from cache")
                    CacheGenerator.remove(fp=dest)

    def generate(self) -> None:
        logging.info("cache.generate()")
        info: t.List[InfoEntry] = []
        problems: t.List[ProblemEntry] = []
        generators: t.List[CacheGenerator] = self.find_generators()

        def generate_info_file():
            logging.info("generating info.json")
            with open(self.root.joinpath('.jarklin/info.json'), 'w') as fp:
                fp.write(json.dumps(info))
            logging.info("generating problems.json")
            with open(self.root.joinpath('.jarklin/problems.json'), 'w') as fp:
                fp.write(json.dumps(problems))

        for generator in generators:
            source = generator.source
            dest = generator.dest
            logging.debug(f"Cache: adding {generator}")
            try:
                if (
                    is_deprecated(source=source, dest=dest)
                    or CacheGenerator.is_incomplete(fp=dest)
                ):
                    logging.info(f"Cache: generating {generator}")
                    try:
                        generator.generate()
                    except Exception as error:
                        logging.error(f"Cache: generation failed ({generator})", exc_info=error)
                        problems.append(ProblemEntry(
                            file=str(source.relative_to(self.root)),
                            type=type(error).__name__,
                            description=str(error),
                            traceback='\n'.join(format_exception(type(error), error, error.__traceback__))
                        ))
                        if dest.is_dir():
                            shutil.rmtree(dest, ignore_errors=True)
                        continue
                    generate_info_file()
                info.append(InfoEntry(
                    path=str(source.relative_to(self.root)),
                    name=source.stem if source.is_file() else source.name,
                    ext=source.suffix if source.is_file() else "",
                    creation_time=get_creation_time(source),
                    modification_time=get_modification_time(source),
                    meta=json.loads(dest.joinpath("meta.json").read_bytes()),
                ))
            except FileNotFoundError as error:
                logging.error(f"Cache: {generator} failed", exc_info=error)
                continue

        generate_info_file()

    def find_generators(self) -> t.List[CacheGenerator]:
        logging.info("Collecting Generators")
        generators: t.List[CacheGenerator] = []

        for root, dirnames, filenames in os.walk(self.root):
            # galleries
            for dirname in dirnames[:]:
                source = Path(root, dirname)
                dest = self.jarklin_cache.joinpath(source.relative_to(self.root))

                if self.ignorer.ignored(source):
                    dirnames.remove(dirname)
                    continue

                if is_gallery(source):
                    generators.append(GalleryCacheGenerator(source=source, dest=dest, config=self._config))

            # videos
            for filename in filenames[:]:
                source = Path(root, filename)
                dest = self.jarklin_cache.joinpath(source.relative_to(self.root))

                if self.ignorer.ignored(source):
                    filenames.remove(filename)
                    continue

                if is_video_file(source):
                    generators.append(VideoCacheGenerator(source=source, dest=dest, config=self._config))

        return sorted(generators, key=lambda g: str(g.source).lower())
