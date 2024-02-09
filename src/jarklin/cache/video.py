# -*- coding=utf-8 -*-
r"""
video.mp4/
├─ preview.jpg
├─ preview.gif
├─ previews/
│  ├─ 1.jpg
│  ├─ 2.jpg
├─ meta.json
├─ video.type
"""
import logging
import shutil
import typing as t
from pathlib import Path
from contextlib import ExitStack
from functools import cached_property
import ffmpeg
from PIL import Image
from ..common.types import VideoMeta, VideoStreamMeta, AudioStreamMeta, SubtitleStreamMeta, ChapterMeta
from ._ffprope_typing import FFProbeResult, FFProbeVideoStream, FFProbeAudioStream, FFProbeSubtitleStream, \
    FFProbeChapter
from ._cache_generator import CacheGenerator


class VideoCacheGenerator(CacheGenerator):
    @cached_property
    def max_dimensions(self) -> t.Tuple[int, int]:
        width = self.config.getint('cache', 'video', 'dimensions', 'width', fallback=None)
        height = self.config.getint('cache', 'video', 'dimensions', 'height', fallback=None)
        if width is None:
            width = height or 512
        if height is None:
            height = width
        return width, height

    @cached_property
    def seconds_per_scene(self) -> float:
        return self.config.getfloat('cache', 'video', 'animated', 'scene_length', fallback=1.5)

    @cached_property
    def scene_fps(self) -> int:
        return self.config.getint('cache', 'video', 'animated', 'fps', fallback=8)

    @cached_property
    def scene_offset(self) -> float:
        return self.config.getfloat('cache', 'video', 'animated', 'scene_offset', fallback=5)

    # ---------------------------------------------------------------------------------------------------------------- #

    def generate_meta(self) -> None:
        import json
        with open(self.dest / "meta.json", "w") as file:
            file.write(json.dumps(self.meta))

    def generate_previews(self) -> None:
        main_frames: t.List[int]
        if self.chapters:
            logging.debug(f"{self}: chapters found")
            main_frames = [
                # start-frame of the chapters + 5s
                round(float(chapter['start_time']) * self.stat_fps + (self.stat_fps * self.scene_offset))
                for chapter in self.chapters
            ]
        else:
            logging.debug(f"{self}: no chapters. fallback to evenly spread scenes")
            number_of_scenes = self.scenes_for_length(duration=self.stat_duration)
            every_n_seconds = self.stat_duration / number_of_scenes
            main_frames = list(range(
                round(self.stat_fps),  # from start
                round(self.stat_n_frames - self.stat_fps),  # to end
                round(every_n_seconds * self.stat_fps),  # every x frame
            ))

        scene_offsets = [round((self.stat_fps / self.scene_fps) * i)
                         for i in range(round(self.seconds_per_scene * self.scene_fps))]

        extract_frames = [round(main + offset)
                          for main in main_frames
                          for offset in scene_offsets]

        vw, vh = self.stat_width, self.stat_height
        scale = (min(self.max_dimensions[0], vw), -1) if (vw > vh) else (-1, min(self.max_dimensions[1], vh))

        logging.debug(f"{self}: running ffmpeg to extract images")
        (
            ffmpeg
            .input(str(self.source))
            .filter('select', "+".join(f"eq(n,{frame})" for frame in extract_frames))
            .filter('scale', *scale)
            .output(str(self.previews_cache.joinpath("%d.jpg")), vframes=len(extract_frames), vsync=0)
            # .global_args('-threads', str(self.config.getint('cache', 'video', 'ffmpeg', 'threads', fallback=0)))
            .run(quiet=True, overwrite_output=True)
        )

        logging.debug(f"{self}: copying frames to previews/")
        for i in range(len(main_frames)):
            shutil.copyfile(
                self.previews_cache.joinpath(f"{round(i * self.seconds_per_scene * self.scene_fps)+1}.jpg"),
                self.previews_dir.joinpath(f"{i+1}.jpg")
            )

    def generate_image_preview(self) -> None:
        # prefer the second as the first could be producer-logo
        preview_source = self.previews_dir.joinpath("2.jpg")
        if not preview_source.is_file():
            preview_source = self.previews_dir.joinpath("1.jpg")
        shutil.copyfile(preview_source, self.dest.joinpath("preview.jpg"))

    def generate_animated_preview(self) -> None:
        images = sorted(self.previews_cache.glob("*.jpg"), key=lambda f: int(f.stem))
        with ExitStack() as stack:
            first, *frames = (stack.enter_context(Image.open(fp)) for fp in images)
            # minimize_size=True => warned as slow
            # method=6 => bit slower but better results
            # note: too many images to use quality=100
            first.save(self.dest.joinpath("preview.webp"), format="WEBP", save_all=True, minimize_size=False,
                       append_images=frames, duration=round(1000 / self.scene_fps), loop=0, method=6)  # , quality=100

    def generate_type(self):
        self.dest.joinpath("video.type").touch()

    def cleanup(self) -> None:
        shutil.rmtree(self.previews_cache, ignore_errors=True)

    @cached_property
    def previews_cache(self) -> Path:
        path = self.dest.joinpath(".previews")
        path.mkdir(parents=True, exist_ok=True)
        return path

    @staticmethod
    def scenes_for_length(duration: float) -> int:
        lengths_list: t.List[int] = [
            7200,  # 2h
            4800,  # 1h30m
            3600,  # 1h
            1800,  # 30m
            600,  # 10m
            300,  # 5m
            60,  # 1m
            30,  # 30s
            10,  # 10s
            0,  # default
        ]

        for i, boundary in enumerate(lengths_list):
            if duration > boundary:
                return len(lengths_list) - i
        return 1  # just to be sure

    @cached_property
    def ffprobe(self) -> FFProbeResult:
        return ffmpeg.probe(str(self.source), show_chapters=None)

    @property
    def video_streams(self) -> t.Iterable[FFProbeVideoStream]:
        return (stream for stream in self.ffprobe["streams"] if stream['codec_type'] == 'video')

    @property
    def audio_streams(self) -> t.Iterable[FFProbeAudioStream]:
        return (stream for stream in self.ffprobe["streams"] if stream['codec_type'] == 'audio')

    @property
    def subtitle_streams(self) -> t.Iterable[FFProbeSubtitleStream]:
        return (stream for stream in self.ffprobe["streams"] if stream['codec_type'] == 'subtitle')

    @property
    def main_video_stream(self) -> FFProbeVideoStream:
        try:
            return next((s for s in self.video_streams if s['disposition']['default']),
                        next(iter(self.video_streams)))
        except StopIteration:
            raise LookupError(f"video stream in {self.source} not found")

    @property
    def chapters(self) -> t.List[FFProbeChapter]:
        return self.ffprobe['chapters']

    @cached_property
    def meta(self) -> VideoMeta:
        duration = float(self.ffprobe["format"]["duration"])
        return VideoMeta(
            type='video',
            filename=self.source.name,
            duration=duration,
            width=self.main_video_stream['width'],
            height=self.main_video_stream['height'],
            filesize=self.source.stat().st_size,
            n_previews=len(self.chapters) or self.scenes_for_length(duration=duration),
            video_streams=[VideoStreamMeta(
                is_default=bool(stream['disposition']['default']),
                duration=float(stream['duration']),
                width=stream['width'],
                height=stream['height'],
                avg_fps=int.__truediv__(*map(int, stream['avg_frame_rate'].split("/"))),
            ) for stream in self.video_streams],
            audio_streams=[AudioStreamMeta(
                is_default=bool(stream['disposition']['default']),
                language=stream.get('tags', {}).get('language', "<unknown>"),
            ) for stream in self.audio_streams],
            subtitles=[SubtitleStreamMeta(
                is_default=bool(stream['disposition']['default']),
                language=stream.get('tags', {}).get('language', "<unknown>"),
            ) for stream in self.subtitle_streams],
            chapters=[ChapterMeta(
                id=chapter['id'],
                # start=chapter['start'],
                start_time=float(chapter['start_time']),
                # end=chapter['end'],
                end_time=float(chapter['end_time']),
                title=chapter.get('tags', {})['title'],
            ) for chapter in self.chapters],
        )

    @cached_property
    def stat_width(self) -> int:
        return self.main_video_stream['width']

    @cached_property
    def stat_height(self) -> int:
        return self.main_video_stream['height']

    @cached_property
    def stat_duration(self) -> float:
        return float(self.main_video_stream['duration'])

    @cached_property
    def stat_n_frames(self) -> int:
        try:
            return int(self.main_video_stream['nb_frames'])
        except KeyError:
            return round(self.stat_duration * self.stat_fps)

    @cached_property
    def stat_fps(self) -> float:
        try:
            frame_rate: str = self.main_video_stream['avg_frame_rate']  # '25/1'
        except KeyError:
            frame_rate: str = self.main_video_stream['r_frame_rate']  # '25/1'
        numerator, denominator = frame_rate.split('/')  # ('25', '1')
        return int(numerator) / int(denominator)  # 25 / 1
