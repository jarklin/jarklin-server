# -*- coding=utf-8 -*-
r"""

"""
import re
import mimetypes
import os.path as p
from pathlib import Path
from ..common.types import PathSource
try:
    import statx
except ModuleNotFoundError:
    statx = None


any_number = re.compile(r"\d")


def get_mimetype(fp: PathSource) -> str:
    r""" no-fail get mimetype """
    fp = Path(fp)
    mime, _encoding = mimetypes.guess_type(fp)
    return mime or "unknown/unknown"


def is_image_file(fp: PathSource) -> bool:
    return get_mimetype(fp).startswith("image/")


def is_video_file(fp: PathSource) -> bool:
    return get_mimetype(fp).startswith("video/")


def is_gallery(fp: PathSource, boundary: int = 5) -> bool:
    r"""
    checks if fp is a directory with at least $boundary image that contain numbers
    """
    fp = Path(fp)
    return fp.is_dir() and len([
        fn for fn in fp.iterdir()
        if any_number.search(fn.stem) is not None
        and is_image_file(fn)
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


def is_deprecated(source: PathSource, dest: PathSource) -> bool:
    r"""
    checks if modification time of source > dest
    """
    source = Path(source)
    dest = Path(dest)
    if not source.exists():
        raise FileNotFoundError(source)
    if not dest.exists():
        return True
    source_mtime = get_modification_time(source)
    dest_mtime = get_modification_time(dest)
    return source_mtime > dest_mtime


def _get_creation_time(fp: PathSource) -> float:
    r"""
    @linux ctime => changed-time, btime => birth-time
    @windows ctime => creation-time
    """
    path = Path(fp)
    try:
        if statx is None:
            raise RuntimeError()
        btime = statx.statx(str(fp)).btime
        if btime is not None:
            return btime
    except RuntimeError:
        pass
    return path.stat().st_ctime


def get_creation_time(path: PathSource) -> float:
    r"""
    returns smallest creation time
    if directory returns earliest from files
    """
    path = Path(path)
    if path.is_dir():
        times = [int(_get_creation_time(fp)) for fp in path.iterdir() if fp.is_file()]
        return min(times) if times else _get_creation_time(path)
    else:
        return int(_get_creation_time(path))


def get_modification_time(path: PathSource) -> float:
    r"""
    returns modification time
    if directory returns biggest from files
    """
    path = Path(path)
    if path.is_dir():
        times = [int(p.getmtime(fp)) for fp in path.iterdir() if fp.is_file()]
        return max(times) if times else p.getmtime(path)
    else:
        return int(p.getmtime(path))
