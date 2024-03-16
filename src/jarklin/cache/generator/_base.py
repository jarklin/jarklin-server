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
import shutil
import functools
import typing as t
from pathlib import Path
from abc import abstractmethod
from configlib import ConfigInterface
from jarklin.common.types import PathSource


class CacheGenerator:
    def __init__(self, source: PathSource, dest: PathSource, config: ConfigInterface):
        self.source = Path(source)
        if not self.source.exists():
            raise FileNotFoundError(str(self.source))
        self.dest = Path(dest)
        self.config = config

    @functools.cache
    def __repr__(self):
        return f"<{type(self).__name__}: {self.source.relative_to(Path.cwd())!s}>"

    @staticmethod
    def remove(fp: PathSource):
        fp = Path(fp)

        if not fp.is_dir():
            return

        files = [
            fp/"meta.json",
            fp/"preview.webp",
            fp/"animated.webp",
            next(fp.glob("*.type"), None),
            fp/"is-cache",
        ]
        for f in files:
            if f and f.is_file():
                f.unlink()

        previews = fp/"previews"
        if previews.is_dir():
            for f in previews.glob("*.webp"):
                f.unlink()
            if next(previews.iterdir(), None) is None:
                previews.rmdir()

        if next(fp.iterdir(), None) is None:
            fp.rmdir()

    @staticmethod
    def is_incomplete(fp: PathSource) -> bool:
        fp = Path(fp)

        if not fp.joinpath("meta.json").is_file():
            return True
        if not fp.joinpath("preview.webp").is_file():
            return True
        if not fp.joinpath("animated.webp").is_file():
            return True
        if next(fp.glob("*.type"), None) is None:
            return True
        if not fp.joinpath("is-cache").is_file():
            return True

        previews = fp/"previews"
        if not previews.is_dir():
            return True
        if next(previews.iterdir(), None) is None:
            return True

        return False

    @t.final
    def generate(self) -> None:
        logging.info(f"{self}.generate()")
        if self.dest.is_dir():
            CacheGenerator.remove(fp=self.dest)
        self.dest.mkdir(parents=True)

        try:
            logging.info(f"{self}.mark_cache()")
            self.mark_cache()
            logging.info(f"{self}.generate_meta()")
            self.generate_meta()
            logging.info(f"{self}.generate_previews()")
            self.generate_previews()
            logging.info(f"{self}.generate_image_preview()")
            self.generate_image_preview()
            logging.info(f"{self}.generate_animated_preview()")
            self.generate_animated_preview()
            logging.info(f"{self}.generate_type()")
            self.generate_type()
            logging.info(f"{self}.cleanup()")
            self.cleanup()
        except KeyboardInterrupt:
            shutil.rmtree(self.dest, ignore_errors=True)
            raise

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

    @abstractmethod
    def generate_type(self) -> None: ...

    def cleanup(self) -> None:
        pass

    @functools.cached_property
    def previews_dir(self) -> Path:
        path = self.dest.joinpath("previews")
        path.mkdir(parents=True, exist_ok=True)
        return path
