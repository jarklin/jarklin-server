# -*- coding=utf-8 -*-
r"""

"""
import time
import logging
import subprocess
import typing as t
import flask
from werkzeug.exceptions import BadRequest as HTTPBadRequest
from configlib import config


__all__ = ['optimize_video', 'BITRATE_MAP']


logger = logging.getLogger(__name__)


def optimize_video(fp: str):
    resolution = flask.request.args.get("resolution")
    logger.info(f"Optimizing video... ({resolution})")
    video_config = BITRATE_MAP.get(resolution)
    if video_config is None:
        raise HTTPBadRequest(f"Invalid resolution: {resolution!r}")

    ffmpeg_executable = config.getstr('ffmpeg', fallback="ffmpeg")

    def generator():
        process = subprocess.Popen([
            ffmpeg_executable, '-hide_banner', '-loglevel', "error",
            '-i', str(fp),
            '-vf', fr"scale=if(lt(iw\,ih)\,min({video_config.height}\,iw)\,-2)"
                   fr":if(gte(iw\,ih)\,min({video_config.height}\,ih)\,-2)",
            '-movflags', "faststart",  # web optimized. faster readiness
            '-fpsmax', f"{video_config.max_fps}",
            "-b:v", video_config.video_bitrate,
            "-b:a", video_config.audio_bitrate,
            # "-acodec", "libmp3lame",  # audio-codec
            # "-scodec", "copy",  # copy subtitles
            '-f', "mpeg",
            "pipe:stdout",
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=-1)
        time.sleep(0.1)  # wait for startup and something in the buffer
        try:
            while process.poll() is None:
                line = process.stdout.read(1024)
                logger.debug(f"Sending {len(line)} bytes")
                yield line
        except GeneratorExit:
            process.terminate()
        except Exception as error:
            logging.critical("video optimization failed", exc_info=error)
            raise error
        else:
            logger.info("video optimization completed")
            if process.returncode > 0:
                stderr = process.stderr.read().decode()
                logging.error(f"ffmpeg failed for unknown reason:\n{stderr}")
                # raise subprocess.CalledProcessError(process.returncode, process.args)

    return flask.Response(flask.stream_with_context(generator()), mimetype="video/mpeg", direct_passthrough=True)


class OptimizationInfo(t.NamedTuple):
    video_bitrate: str
    audio_bitrate: str
    max_fps: int
    height: int


BITRATE_MAP: t.Dict[str, OptimizationInfo] = {
    '240p': OptimizationInfo(video_bitrate="300k", audio_bitrate="32k", max_fps=30, height=240),
    '360p': OptimizationInfo(video_bitrate="500k", audio_bitrate="48k", max_fps=30, height=360),
    '480p': OptimizationInfo(video_bitrate="1000k", audio_bitrate="64k", max_fps=30, height=480),
    '720p': OptimizationInfo(video_bitrate="1500k", audio_bitrate="128k", max_fps=30, height=720),
    '720p60': OptimizationInfo(video_bitrate="2250k", audio_bitrate="128k", max_fps=60, height=720),
    '1080p': OptimizationInfo(video_bitrate="3000k", audio_bitrate="192k", max_fps=30, height=1080),
    '1080p60': OptimizationInfo(video_bitrate="4500k", audio_bitrate="192k", max_fps=60, height=1080),
    '1440p': OptimizationInfo(video_bitrate="6000k", audio_bitrate="320k", max_fps=30, height=1440),
    '1440p60': OptimizationInfo(video_bitrate="9000k", audio_bitrate="320k", max_fps=60, height=1440),
    '2160p': OptimizationInfo(video_bitrate="13000k", audio_bitrate="448k", max_fps=30, height=2160),
    '2160p60': OptimizationInfo(video_bitrate="20000k", audio_bitrate="448k", max_fps=60, height=2160),
}
