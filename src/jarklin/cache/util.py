# -*- coding=utf-8 -*-
r"""

"""
import re
import logging
import mimetypes
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


def is_deprecated(source: PathSource, dest: PathSource) -> bool:
    source = Path(source)
    dest = Path(dest)
    if not source.exists():
        raise FileNotFoundError(source)
    if not dest.exists():
        return True
    if source.is_dir():  # gallery
        source_mtime = max(fp.stat().st_mtime for fp in source.iterdir() if fp.is_file())
    else:
        source_mtime = source.stat().st_mtime
    return source_mtime > dest.stat().st_mtime


def is_incomplete(dest: PathSource) -> bool:
    dest = Path(dest)
    return next(dest.glob("*.type"), None) is None


def get_ctime(path: PathSource) -> float:
    path = Path(path)
    if path.is_file():
        return path.stat().st_ctime
    elif path.is_dir():
        return min(p.stat().st_ctime for p in path.iterdir() if p.is_file())
    else:
        raise ValueError(f"can't get ctime for {str(path)!r}")


def get_mtime(path: PathSource) -> float:
    path = Path(path)
    if path.is_file():
        return path.stat().st_mtime
    elif path.is_dir():
        times = [p.stat().st_mtime for p in path.iterdir() if p.is_file()]
        minimum = min(times)
        maximum = max(times)
        # assume that it took at least one hour for the gallery to be created (e.g. download-time)
        return maximum if maximum > (minimum + 3600) else minimum
    else:
        raise ValueError(f"can't get mtime for {str(path)!r}")
