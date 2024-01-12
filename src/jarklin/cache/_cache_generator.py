# -*- coding=utf-8 -*-
r"""

"""
import shutil
import typing as t
from pathlib import Path
from abc import abstractmethod
from functools import cached_property
from ..common.types import PathSource


class CacheGenerator:
    def __init__(self, source: PathSource, dest: PathSource):
        self.source = Path(source)
        if not self.source.exists():
            raise FileNotFoundError(str(self.source))
        self.dest = Path(dest)
        if self.dest.is_dir():
            shutil.rmtree(self.dest, ignore_errors=True)
        self.dest.mkdir(parents=True)

    @t.final
    def generate(self) -> None:
        self.generate_meta()
        self.generate_previews()
        self.generate_image_preview()
        self.generate_animated_preview()
        self.generate_type()
        self.cleanup()

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

    @cached_property
    def previews_dir(self) -> Path:
        path = self.dest.joinpath("previews")
        path.mkdir(parents=True, exist_ok=True)
        return path
