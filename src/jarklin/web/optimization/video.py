# -*- coding=utf-8 -*-
r"""

"""
import os
import time
import logging
import subprocess

import flask
from configlib import config


def optimize_video(fp: str):
    filesize = os.path.getsize(fp)
    if filesize < flask.current_app.config.get('VIDEO_OPTIMIZATION_MINIMUM_SIZE', 1024 * 1024 * 50):
        return None

    ffmpeg_executable = config.getstr('ffmpeg', fallback="ffmpeg")

    def generator():
        process = subprocess.Popen([
            ffmpeg_executable, '-hide_banner', '-loglevel', "error",
            '-i', str(fp),
            '-vf', r"scale=if(gte(iw\,ih)\,min(1080\,iw)\,-2):if(lt(iw\,ih)\,min(1080\,ih)\,-2)",  # max 1080p
            '-movflags', "faststart",  # web optimized. faster readiness
            '-fpsmax', "30",
            # "-b:v", "32k",  # video-bitrate
            # "-b:a", "32k",  # audio-bitrate
            # "-acodec", "libmp3lame",  # audio-codec
            # "-scodec", "copy",  # copy subtitles
            '-f', "mpeg",
            "pipe:stdout",
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=-1)
        time.sleep(1)  # wait for startup and something in the buffer
        try:
            while process.poll() is None:
                line = process.stdout.read(1024)
                yield line
        except GeneratorExit:
            process.terminate()
        except Exception as error:
            logging.critical("video optimization failed", exc_info=error)
            raise error
        else:
            if process.returncode > 0:
                stderr = process.stderr.read().decode()
                logging.error(f"ffmpeg failed for unknown reason:\n{stderr}")
                # raise subprocess.CalledProcessError(process.returncode, process.args)

    return flask.Response(flask.stream_with_context(generator()), mimetype="video/mpeg", direct_passthrough=True)
