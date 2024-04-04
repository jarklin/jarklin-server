# -*- coding=utf-8 -*-
r"""

"""
import json
import shlex
import logging
import typing as t
from os import PathLike
import subprocess as sp
from configlib import config
from .ffprope_typing import FFProbeResult


logger = logging.getLogger(__name__)


def ffprobe(fp: t.Union[str, PathLike]) -> FFProbeResult:

    ffprobe_executable = config.getstr('ffprobe', fallback="ffprobe")

    args = [
        ffprobe_executable, '-hide_banner',
        '-show_format', '-show_streams', '-show_chapters',
        '-of', 'json', str(fp),
    ]

    logger.debug(f"running: {shlex.join(args)}")

    result = sp.run(args, check=True, capture_output=True, text=True)
    return json.loads(result.stdout)
