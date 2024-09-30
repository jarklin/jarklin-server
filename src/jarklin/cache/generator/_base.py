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
        return FileIndex(root=self.dest).ensure_loaded()

    @functools.cached_property
    def previews_dir(self) -> Path:
        path = self.dest.joinpath("previews")
        if path.is_dir():
            for fp in path.glob("*.webp"):
                fp.unlink(missing_ok=True)
        path.mkdir(parents=True)
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
        index = FileIndex(root=fp)
        if index.exists():
            index.load()
            index.unlink_indexed(cleanup_directories=True)
            index.unlink()
        else:
            logger.warning("file-index does no exist. no idea what should to be removed")

    @staticmethod
    def is_incomplete(fp: PathSource) -> bool:
        logger.debug(f"Checking if %s is incomplete", fp)
        return not FileIndex(root=fp).exists()

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
            self.file_index.unlink_indexed(cleanup_directories=True)
            raise err
        else:
            logger.info(f"{self} - Saving file-index")
            self.file_index.save()

    @t.final
    def mark_cache(self):
        self.file_index.add_file(self.dest / "is-cache").touch()

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
