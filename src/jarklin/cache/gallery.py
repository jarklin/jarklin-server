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
from functools import cached_property
from ..common.types import GalleryMeta, GalleryImageMeta, PathSource
from ._cache_generator import CacheGenerator
from .util import is_image_file
from PIL import Image


class GalleryCacheGenerator(CacheGenerator):
    DIMS: t.Tuple[int, int] = (512, 512)
    FRAME_TIME: float = 1.0

    def generate_meta(self) -> None:
        import orjson
        with open(self.dest / "meta.json", "wb") as file:
            file.write(orjson.dumps(self.meta))

    def generate_previews(self) -> None:
        for i, info in enumerate(self.meta['images']):
            with Image.open(self.source.joinpath(info['filename'])) as image:
                image_rgb = image.convert('RGB')
                image_rgb.thumbnail(self.DIMS)
                image_rgb.save(self.previews_dir.joinpath(f"{i+1}.jpg"), format='JPEG',
                               progressive=True, optimize=True, quality=85)

    def generate_image_preview(self) -> None:
        first_preview = self.previews_dir.joinpath("1.jpg")
        if first_preview.is_file():
            shutil.copyfile(first_preview, self.dest.joinpath("preview.jpg"))

    def generate_animated_preview(self) -> None:
        images = sorted(self.previews_dir.glob("*.jpg"), key=lambda f: int(f.stem))[:20]  # max 20!?
        first, *frames = map(Image.open, images)
        # saved as gif. better compatibility, but larger in size
        # first.save(self.dest.joinpath("preview.gif"), format="GIF", save_all=True, interlace=True,
        #            append_images=frames, duration=round(1000 / self.FRAMES_PER_SCENE), loop=0, optimize=True)
        # save as newer webp format. way smaller but not as well-supported
        first.save(self.dest.joinpath("preview.webp"), format="WEBP", save_all=True, minimize_size=False,
                   append_images=frames, duration=round(self.FRAME_TIME * 1000), loop=0, method=6, quality=100)

    def generate_type(self) -> None:
        self.dest.joinpath("gallery.type").touch()

    @cached_property
    def meta(self) -> GalleryMeta:
        return GalleryMeta(
            type='gallery',
            path=str(self.source),
            name=self.source.name,
            images=list(map(self.meta_for_image, self.get_relevant_files_for_source(self.source))),
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
