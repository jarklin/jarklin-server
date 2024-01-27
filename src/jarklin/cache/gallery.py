# -*- coding=utf-8 -*-
r"""
todo: support for .cb_ file formats
- .cb7 → 7z  # pip install py7zr
- .cba → ACE  # pip install acefile
- .cbr → RAR  # pip install python-unrar  (requires manually installed library)
- .cbt → TAR  # import tarfile
- .cbz → ZIP  # import zipfile

todo: what if image is extremely height (eg. 512x8192)
- crop for animated preview!?

video.mp4/
├─ preview.jpg
├─ preview.gif
├─ previews/
│  ├─ 1.jpg
│  ├─ 2.jpg
├─ meta.json
├─ video.type
"""
import re
import shutil
import typing as t
from pathlib import Path
from contextlib import ExitStack
from functools import cached_property
from ..common.types import GalleryMeta, GalleryImageMeta, PathSource
from ._cache_generator import CacheGenerator
from .util import is_image_file
from PIL import Image


class GalleryCacheGenerator(CacheGenerator):
    @cached_property
    def max_dimensions(self) -> t.Tuple[int, int]:
        width = self.config.getint('cache', 'gallery', 'dimensions', 'width', fallback=None)
        height = self.config.getint('cache', 'gallery', 'dimensions', 'height', fallback=None)
        if width is None:
            width = height or 512
        if height is None:
            height = width
        return width, height

    @cached_property
    def frame_time(self) -> float:
        return self.config.getfloat('cache', 'gallery', 'animated', 'frame_time', fallback=1.0)

    @cached_property
    def max_images(self) -> int:
        return self.config.getint('cache', 'gallery', 'animated', 'max_images', fallback=20)

    # ---------------------------------------------------------------------------------------------------------------- #

    def generate_meta(self) -> None:
        import json
        with open(self.dest / "meta.json", "w") as file:
            file.write(json.dumps(self.meta))

    def generate_previews(self) -> None:
        for i, info in enumerate(self.meta['images']):
            with Image.open(self.source.joinpath(info['filename'])) as image:
                image_rgb = image.convert('RGB')
                image_rgb.thumbnail(self.max_dimensions)
                image_rgb.save(self.previews_dir.joinpath(f"{i+1}.jpg"), format='JPEG',
                               progressive=True, optimize=True, quality=85)

    def generate_image_preview(self) -> None:
        first_preview = self.previews_dir.joinpath("1.jpg")
        if first_preview.is_file():
            shutil.copyfile(first_preview, self.dest.joinpath("preview.jpg"))

    def generate_animated_preview(self) -> None:
        images = sorted(self.previews_dir.glob("*.jpg"), key=lambda f: int(f.stem))[:self.max_images]
        with ExitStack() as stack:
            first, *frames = (stack.enter_context(Image.open(fp)) for fp in images)
            # this step is done to ensure all images have the same dimensions. otherwise the save will fail
            frames = [stack.enter_context(frame.resize(first.size)) for frame in frames]
            # minimize_size=True => warned as slow
            # method=6 => bit slower but better results
            first.save(self.dest.joinpath("preview.webp"), format="WEBP", save_all=True, minimize_size=False,
                       append_images=frames, duration=round(self.frame_time * 1000), loop=0, method=6, quality=100)

    def generate_type(self) -> None:
        self.dest.joinpath("gallery.type").touch()

    @cached_property
    def meta(self) -> GalleryMeta:
        relevant_files = self.get_relevant_files_for_source(self.source)
        return GalleryMeta(
            type='gallery',
            n_previews=len(relevant_files),
            images=list(map(self.meta_for_image, relevant_files)),
        )

    @staticmethod
    def meta_for_image(fp: PathSource) -> GalleryImageMeta:
        fp = Path(fp)
        with Image.open(fp) as image:
            return GalleryImageMeta(
                filename=fp.name,
                width=image.width,
                height=image.height,
                filesize=fp.stat().st_size,
                is_animated=getattr(image, 'is_animated', False),
            )

    @staticmethod
    def get_relevant_files_for_source(source: PathSource) -> t.List[PathSource]:
        all_files = [fp for fp in source.iterdir() if fp.is_file()]
        pattern = re.compile(r'(?P<id>\d+)$')
        possible_files: t.List[t.Tuple[Path, int]] = []
        for fp in all_files:
            if not is_image_file(fp):
                continue
            match = pattern.search(fp.stem)
            if match is None:
                continue
            possible_files.append((fp, int(match.group('id'))))
        return [fp for fp, _ in sorted(possible_files, key=lambda p: p[1])]
