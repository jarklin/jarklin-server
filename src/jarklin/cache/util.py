# -*- coding=utf-8 -*-
r"""

"""
import re
import logging
import mimetypes
import os.path as p
from pathlib import Path
from ..common.types import PathSource
try:
    import magic
except ImportError:  # not found or system has not libmagic.c stuff
    logging.exception("magic")
    magic = None


any_number = re.compile(r"\d")


def get_mimetype(fp: PathSource, *, quick: bool = True) -> str:
    fp = Path(fp)
    if magic and not quick:
        try:
            return magic.from_file(fp, mime=True)
        except (IsADirectoryError, FileNotFoundError):
            pass
    mime, _ = mimetypes.guess_type(fp)
    return mime or "unknown/unknown"


def is_image_file(fp: PathSource) -> bool:
    return get_mimetype(fp).startswith("image/")


def is_video_file(fp: PathSource) -> bool:
    return get_mimetype(fp).startswith("video/")


def is_gallery(fp: PathSource, boundary: int = 5) -> bool:
    fp = Path(fp)
    return fp.is_dir() and len([
        fn for fn in fp.iterdir()
        if any_number.search(fn.stem) is not None and is_image_file(fn)
    ]) > boundary


def is_cache(fp: PathSource) -> bool:
    fp = Path(fp)
    return fp.joinpath("is-cache").is_file()


def is_gallery_cache(fp: PathSource) -> bool:
    fp = Path(fp)
    return is_cache(fp) and fp.joinpath("gallery.type").is_file()


def is_video_cache(fp: PathSource) -> bool:
    fp = Path(fp)
    return is_cache(fp) and fp.joinpath("video.type").is_file()


def is_incomplete(dest: PathSource) -> bool:
    dest = Path(dest)
    return next(dest.glob("*.type"), None) is None


def is_deprecated(source: PathSource, dest: PathSource) -> bool:
    source = Path(source)
    dest = Path(dest)
    if not source.exists():
        raise FileNotFoundError(source)
    if not dest.exists():
        return True
    if source.is_dir():  # gallery
        source_mtime = max(p.getmtime(fp) for fp in source.iterdir() if fp.is_file())
    else:
        source_mtime = p.getmtime(source)
    return source_mtime > p.getmtime(dest)


def get_creation_time(path: PathSource) -> float:
    # fixme: ctime != creation-time on unix
    path = Path(path)
    if path.is_file():
        return int(p.getctime(path))
    elif path.is_dir():
        return min(int(p.getctime(fp)) for fp in path.iterdir() if fp.is_file())
    else:
        raise ValueError(f"can't get ctime for {str(path)!r}")


def get_modification_time(path: PathSource) -> float:
    path = Path(path)
    if path.is_file():
        return int(p.getmtime(path))
    elif path.is_dir():
        times = [int(p.getmtime(fp)) for fp in path.iterdir() if fp.is_file()]
        minimum = min(times)
        maximum = max(times)
        # assume that it took at least one hour for the gallery to be created (e.g. download-time)
        return maximum if maximum > (minimum + 3600) else minimum
    else:
        raise ValueError(f"can't get mtime for {str(path)!r}")
