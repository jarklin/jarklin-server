# -*- coding=utf-8 -*-
r"""

"""
import shutil
import logging
from functools import cache
from configlib import config


__all__ = ['ffprobe_executable', 'ffmpeg_executable']


logger = logging.getLogger(__name__)


@cache
def ffprobe_executable() -> str:
    raw = config.getstr('ffprobe', fallback="ffprobe")
    exe = shutil.which(raw)
    if exe is None:
        raise FileNotFoundError(f"ffprobe not found for {raw!r}")
    logger.debug(f"ffprobe-executable: {exe}")
    return exe


@cache
def ffmpeg_executable() -> str:
    raw =config.getstr('ffmpeg', fallback="ffmpeg")
    exe = shutil.which(raw)
    if exe is None:
        raise FileNotFoundError(f"ffmpeg not found for {raw!r}")
    logger.debug(f"ffmpeg-executable: {exe}")
    return exe
