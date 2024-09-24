# -*- coding=utf-8 -*-
r"""

"""
import logging
import mimetypes
import flask
from .image import optimize_image
from .video import optimize_video, BITRATE_MAP as VIDEO_BITRATE_MAP


__all__ = ['optimize_file', 'VIDEO_BITRATE_MAP']


def optimize_file(fp: str):
    mimetype, _ = mimetypes.guess_type(fp)
    if not mimetype:
        return None
    maintype, _, subtype = mimetype.partition("/")
    jit_optimization = flask.current_app.config.get('JIT_OPTIMIZATION', {})
    allows_optimization = jit_optimization.get(mimetype, False) or jit_optimization.get(maintype, False)
    if not allows_optimization:
        return None

    if maintype == "image":
        logging.debug("Attempt to optimize image")
        return optimize_image(fp)
    if maintype == "video":
        logging.debug("Attempt to optimize video")
        return optimize_video(fp)
