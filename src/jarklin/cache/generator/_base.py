# -*- coding=utf-8 -*-
r"""

{gallery,video.mp4}/
├─ preview.webp
├─ animated.webp
├─ previews/
│  ├─ 1.webp
│  ├─ 2.webp
├─ meta.json
├─ {gallery,video}.type
├─ is-cache
"""
import logging
import functools
import typing as t
from pathlib import Path
from abc import abstractmethod
from configlib import ConfigInterface
from ...common.fileindex import FileIndex
from ...common.types import PathSource


logger = logging.getLogger(__name__)


class CacheGenerator:
    def __init__(self, source: PathSource, dest: PathSource, config: ConfigInterface):
        self.source = Path(source)
        if not self.source.exists():
            raise FileNotFoundError(str(self.source))
        self.dest = Path(dest)
        self.config = config

    @functools.cached_property
    def root(self) -> Path:
        return Path.cwd()

    @functools.cached_property
    def file_index(self) -> FileIndex:
        index = FileIndex(self.source / "file-index.txt")
        if index.exists():
            index.load()
        return index

    @functools.cached_property
    def previews_dir(self) -> Path:
        path = self.dest.joinpath("previews")
        path.mkdir(parents=True, exist_ok=True)
        return path

    @functools.cache
    def __repr__(self):
        return f"<{type(self).__name__}: {self.source.relative_to(self.root)!s}>"

    @staticmethod
    def remove(fp: PathSource):
        r"""
        cleanly removes the cache. does not touch manually added files
        """
        logger.info(f"Removing {fp!s}")
        fp = Path(fp)

        if not fp.is_dir():
            logger.error(f"{fp!s} is not a directory. can't be cleanly removed")
            return

        files = [
            fp/"meta.json",
            fp/"preview.webp",
            fp/"animated.webp",
            next(fp.glob("*.type"), None),
            *fp.glob("*.vtt"),
            fp/"is-cache",
        ]
        for f in files:
            if f and f.is_file():
                logger.debug(f"Removing {f!s}")
                f.unlink()

        previews = fp/"previews"
        if previews.is_dir():
            for f in previews.glob("*.webp"):
                logger.debug(f"Removing {f!s}")
                f.unlink()
            if next(previews.iterdir(), None) is None:
                logger.debug(f"Removing {previews!s}")
                previews.rmdir()
            else:
                logger.debug(f"Not removing {previews!s} as it contains unknown files")

        if next(fp.iterdir(), None) is None:
            logger.debug(f"Removing {previews!s}")
            fp.rmdir()
        else:
            logger.debug(f"Not removing {fp!s} as it contains unknown files")

    @staticmethod
    def is_incomplete(fp: PathSource) -> bool:
        logger.debug(f"Checking if {fp!s} is incomplete")
        fp = Path(fp)

        if not fp.joinpath("meta.json").is_file():
            logger.debug(f"missing meta.json")
            return True
        if not fp.joinpath("preview.webp").is_file():
            logger.debug(f"missing preview.webp")
            return True
        if not fp.joinpath("animated.webp").is_file():
            logger.debug(f"missing animated.webp")
            return True
        if next(fp.glob("*.type"), None) is None:
            logger.debug(f"missing *.type")
            return True
        if not fp.joinpath("is-cache").is_file():
            logger.debug(f"missing is-cache")
            return True

        previews = fp/"previews"
        if not previews.is_dir():
            logger.debug(f"missing previews/")
            return True
        if next(previews.glob("*.webp"), None) is None:
            logger.debug(f"missing previews/*.webp")
            return True

        logger.debug(f"{fp!s} is not incomplete")
        return False

    @t.final
    def generate(self) -> None:
        logger.info(f"{self}.generate()")
        if self.dest.is_dir():
            CacheGenerator.remove(fp=self.dest)
        self.dest.mkdir(parents=True, exist_ok=True)

        try:
            logger.info(f"{self}.mark_cache()")
            self.mark_cache()
            logger.info(f"{self}.generate_meta()")
            self.generate_meta()
            logger.info(f"{self}.generate_previews()")
            self.generate_previews()
            logger.info(f"{self}.generate_image_preview()")
            self.generate_image_preview()
            logger.info(f"{self}.generate_animated_preview()")
            self.generate_animated_preview()
            logger.info(f"{self}.generate_extra()")
            self.generate_extra()
            logger.info(f"{self}.generate_type()")
            self.generate_type()
            logger.info(f"{self}.cleanup()")
            self.cleanup()
        except Exception as err:
            logger.error(f"Exception while generating cache ({type(err).__name__}). doing cleanup before re-raising")
            self.cleanup()
            self.remove(self.dest)
            raise err

    @t.final
    def mark_cache(self):
        self.dest.joinpath("is-cache").touch()

    @abstractmethod
    def generate_meta(self) -> None: ...

    @abstractmethod
    def generate_previews(self) -> None: ...

    @abstractmethod
    def generate_image_preview(self) -> None: ...

    @abstractmethod
    def generate_animated_preview(self) -> None: ...

    def generate_extra(self) -> None:
        pass

    @abstractmethod
    def generate_type(self) -> None: ...

    def cleanup(self) -> None:
        pass
