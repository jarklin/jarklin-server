# -*- coding=utf-8 -*-
r"""

"""
import typing as t
from os import PathLike
import subprocess as sp
from configlib import config
from .ffprope_typing import FFProbeResult


def ffprobe(fp: t.Union[str, PathLike]) -> FFProbeResult:
    import json

    ffprobe_executable = config.getstr('ffprobe', fallback="ffprobe")

    result = sp.run([
        ffprobe_executable, '-hide_banner',
        '-show_format', '-show_streams', '-show_chapters', '-count_frames',
        '-of', 'json', str(fp),
    ], check=True, capture_output=True, text=True,
    )
    return json.loads(result.stdout)
