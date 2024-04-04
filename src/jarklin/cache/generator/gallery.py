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

gallery/
├─ preview.webp
├─ animated.webp
├─ previews/
│  ├─ 1.webp
│  ├─ 2.webp
├─ meta.json
├─ gallery.type
├─ is-cache
"""
import re
import shutil
import logging
import typing as t
from pathlib import Path
from contextlib import ExitStack
from functools import cached_property
from PIL import Image
from ...common.types import GalleryMeta, GalleryImageMeta, PathSource
from ...cache.util import is_image_file
from ._base import CacheGenerator


logger = logging.getLogger(__name__)


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
        animated_count = 0

        for i, info in enumerate(self.meta['images']):
            fp = self.source.joinpath(info['filename'])
            with Image.open(fp) as image:

                if animated_count < self.max_images:
                    # note: quality=0 & method=0 during save. we don't care about the size of these temp-images
                    if image.height > image.width * 3:
                        logger.debug(f"{self}: {fp.name} - image height is too much."
                                     f" splitting into multiple smaller for animated preview")
                        width, height = image.size
                        rough_ratio = 9 / 16  # portrait
                        times = round((height * rough_ratio) / width)
                        pheight = round(height / times)
                        for j in range(times):
                            logger.debug(f"{self}: {fp.name}#{j} - resizing for animated preview")
                            animated_count += 1
                            offset = j * pheight
                            img = image.crop((0, offset, width, offset + pheight))
                            img.thumbnail(self.max_dimensions, resample=Image.Resampling.LANCZOS)
                            img.save(self.animated_cache / f"{animated_count}.webp", format="WEBP",
                                     lossless=True, quality=0, method=0)
                    else:
                        logger.debug(f"{self}: {fp.name} - resizing for animated preview")
                        animated_count += 1
                        img = image.copy()
                        img.thumbnail(self.max_dimensions, resample=Image.Resampling.LANCZOS)
                        img.save(self.animated_cache / f"{animated_count}.webp", format="WEBP",
                                 lossless=True, quality=0, method=0)

                image.thumbnail(self.max_dimensions, resample=Image.Resampling.LANCZOS)
                image.save(self.previews_dir.joinpath(f"{i + 1}.webp"), format='WEBP', method=6, quality=80)

    def generate_image_preview(self) -> None:
        first_preview = self.previews_dir.joinpath("1.webp")
        shutil.copyfile(first_preview, self.dest.joinpath("preview.webp"))

    def generate_animated_preview(self) -> None:
        import statistics

        filepaths = sorted(self.animated_cache.glob("*.webp"), key=lambda f: int(f.stem))[:self.max_images]
        if not filepaths:
            raise FileNotFoundError("no previews found")

        with ExitStack() as stack:
            images: t.List[Image.Image] = [stack.enter_context(Image.open(fp)) for fp in filepaths]
            avg_width = round(statistics.mean((img.width for img in images)))
            avg_height = round(statistics.mean((img.height for img in images)))
            logger.debug(f"{self}: animated size calculated to {avg_width}x{avg_height}")

            # this step is done to ensure all images have the same dimensions. otherwise the save will fail
            logger.debug(f"{self}: resizing frames to fit animated preview")
            images = [frame.resize((avg_width, avg_height), resample=Image.Resampling.LANCZOS) for frame in images]
            first, *frames = images
            # minimize_size=True => warned as slow
            # method=6 => bit slower but better results
            first.save(self.dest.joinpath("animated.webp"), format="WEBP", save_all=True, minimize_size=True,
                       append_images=frames, duration=round(self.frame_time * 1000), loop=0, method=6, quality=80)

    def generate_type(self) -> None:
        self.dest.joinpath("gallery.type").touch()

    def cleanup(self) -> None:
        shutil.rmtree(self.animated_cache, ignore_errors=True)

    @cached_property
    def animated_cache(self):
        path = self.dest.joinpath(".animated")
        shutil.rmtree(path, ignore_errors=True)
        path.mkdir(parents=True)
        return path

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
                ext=fp.suffix,
                width=image.width,
                height=image.height,
                filesize=fp.stat().st_size,
                is_animated=getattr(image, 'is_animated', False),
            )

    @staticmethod
    def get_relevant_files_for_source(source: PathSource) -> t.List[PathSource]:
        pattern = re.compile(r'(?P<id>\d+)$')  # prefer last digits
        fallback_pattern = re.compile(r'(?P<id>\d+)')  # but accept any if possible

        all_files = [fp for fp in source.iterdir() if fp.is_file()]
        possible_files: t.List[t.Tuple[Path, int]] = []

        for fp in all_files:
            if not is_image_file(fp):
                continue
            match = pattern.search(fp.stem)
            if match is None:
                match = fallback_pattern.search(fp.stem)
            if match is None:
                continue
            possible_files.append((fp, int(match.group('id'))))

        if not possible_files:
            raise FileNotFoundError('No image files found')

        return [fp for fp, _ in sorted(possible_files, key=lambda p: p[1])]
