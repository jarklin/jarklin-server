# -*- coding=utf-8 -*-
r"""

"""
import typing as t
from pathlib import Path
from functools import cached_property
from .._lib import json


__all__ = ["CacheEntry"]


class CacheEntry:
    def __init__(self, path: str):
        self._path = Path(path).relative_to(Path.cwd())
        self._mtime: int = 0
        self._cached_meta: dict = {}

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
    def is_video(self) -> bool:
        return self.cache_path.joinpath("video.type").exists()

    @property
    def is_gallery(self) -> bool:
        return self.cache_path.joinpath("gallery.type").exists()

    @property
    def meta(self) -> dict:
        if not self.exists():
            raise FileNotFoundError(str(self.cache_path))

        # check if changed. if not then return memcached
        mtime = self.cache_path.stat().st_mtime
        if mtime <= self._mtime:
            return self._cached_meta

        # load, cache and return
        meta = self._cached_meta = json.loads(self.meta_path.read_bytes())
        self._mtime = mtime
        return meta
