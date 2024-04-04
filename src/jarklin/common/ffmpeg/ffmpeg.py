# -*- coding=utf-8 -*-
r"""

"""
import typing as t
import subprocess as sp
from configlib import config


def ffmpeg(args: t.Iterable[str]):
    ffmpeg_executable = config.getstr('ffmpeg', fallback="ffmpeg")

    args = [ffmpeg_executable, '-hide_banner', *args]

    return sp.run(args, check=True, capture_output=True, text=True)
