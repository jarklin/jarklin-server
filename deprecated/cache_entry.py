# -*- coding=utf-8 -*-
r"""

"""
import typing as t
from pathlib import Path
from functools import cached_property
import orjson
from .types import PathSource


__all__ = ["CacheEntry"]


class CacheEntry:
    def __init__(self, path: PathSource):
        self._path = Path(path).absolute().relative_to(Path.cwd())
        self._mtime: int = 0
        self._cached_meta: dict = {}

    @classmethod
    def from_cache_path(cls, path: PathSource) -> 'CacheEntry':
        return CacheEntry(path=Path(path).absolute().relative_to(Path(".jarklin/cache").absolute()))

    @property
    def file_path(self) -> Path:
        return self._path

    @cached_property
    def cache_path(self) -> Path:
        return Path(".jarklin/cache").joinpath(self._path)

    @cached_property
    def meta_path(self) -> Path:
        return self.cache_path.joinpath("meta.json")

    @cached_property
    def static_preview(self) -> Path:
        return self.cache_path.joinpath("preview.jpg")

    @cached_property
    def animated_preview(self) -> Path:
        return self.cache_path.joinpath("preview.gif")

    @cached_property
    def previews_dir(self) -> Path:
        return self.cache_path.joinpath("previews")

    @cached_property
    def previews(self) -> t.Iterable[Path]:
        return self.previews_dir.glob("*.jpg")

    def exists(self):
        self.cache_path.exists()

    @property
    def is_cache(self) -> bool:
        return self.is_video or self.is_gallery

    @property
    def is_video(self) -> bool:
        return self.cache_path.joinpath("video.type").is_file()

    @property
    def is_gallery(self) -> bool:
        return self.cache_path.joinpath("gallery.type").is_file()

    @property
    def meta(self) -> dict:
        if not self.exists():
            raise FileNotFoundError(str(self.cache_path))

        # check if changed. if not then return memcached
        mtime = self.cache_path.stat().st_mtime
        if mtime <= self._mtime:
            return self._cached_meta

        # load, cache and return
        meta = self._cached_meta = orjson.loads(self.meta_path.read_bytes())
        self._mtime = mtime
        return meta
