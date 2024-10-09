# -*- coding=utf-8 -*-
r"""

"""
import json
import shlex
import logging
import typing as t
from os import PathLike
import subprocess as sp
from pydantic import ValidationError
from ..executables import ffprobe_executable
from ...common.ffprobe.model import FFProbe


__all__ = ['ffprobe']


logger = logging.getLogger(__name__)


def ffprobe(fp: t.Union[str, PathLike]) -> FFProbe:
    args = [
        ffprobe_executable(),
        '-hide_banner',
        '-show_format', '-show_streams', '-show_chapters',
        '-of', 'json', str(fp),
    ]

    logger.debug(f"running: {shlex.join(args)}")

    result = sp.run(args, check=True, capture_output=True, text=True)
    result = json.loads(result.stdout)
    try:
        return FFProbe.model_validate(result)
    except (ValidationError, TypeError, ValueError) as e:
        logger.error(f"Failed to convert ffprobe json to model ({result})", exc_info=e)
        raise e
