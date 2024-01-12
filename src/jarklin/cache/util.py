# -*- coding=utf-8 -*-
r"""

"""
from pathlib import Path
from ..common.types import PathSource


def get_mimetype(fp: PathSource) -> str:
    fp = Path(fp)
    try:
        import magic
        return magic.from_file(fp, mime=True)
    except (ModuleNotFoundError, FileNotFoundError):
        pass
    except IsADirectoryError:
        return "unknown/unknown"
    import mimetypes
    mime, _ = mimetypes.guess_type(fp)
    return mime or "unknown/unknown"


def is_image_file(fp: PathSource) -> bool:
    return get_mimetype(fp).startswith("image/")


def is_video_file(fp: PathSource) -> bool:
    return get_mimetype(fp).startswith("video/")


def is_gallery(fp: PathSource, boundary: int = 5) -> bool:
    fp = Path(fp)
    return fp.is_dir() and len([f for f in fp.iterdir() if is_image_file(f)]) > boundary


def is_deprecated(source: PathSource, dest: PathSource) -> bool:
    if not dest.exists():
        return True
    return source.stat().st_mtime > dest.stat().st_mtime
