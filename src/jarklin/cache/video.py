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
import shutil
import typing as t
from pathlib import Path
from functools import cached_property
import ffmpeg
from PIL import Image
from ..common.types import VideoMeta, VideoStreamMeta, AudioStreamMeta, SubtitleStreamMeta, ChapterMeta
from ._ffprope_typing import FFProbeResult, FFProbeVideoStream, FFProbeAudioStream, FFProbeSubtitleStream, \
    FFProbeChapter
from ._cache_generator import CacheGenerator


class VideoCacheGenerator(CacheGenerator):
    DIMS: t.Tuple[int, int] = (512, 512)
    SECONDS_PER_SCENE: int = 2
    SCENE_FPS: int = 10

    def generate_meta(self) -> None:
        import json
        with open(self.dest / "meta.json", "w") as file:
            file.write(json.dumps(self.meta))

    def generate_previews(self) -> None:
        main_frames: t.List[int]
        if self.chapters:
            main_frames = [
                # start-frame of the chapters + 5s
                round(float(chapter['start_time']) * self.stat_fps + (self.stat_fps * 5))
                for chapter in self.chapters
            ]
        else:
            number_of_scenes = self.scenes_for_length(duration=self.stat_duration)
            every_n_seconds = self.stat_duration / number_of_scenes
            main_frames = list(range(
                round(self.stat_fps),  # from start
                round(self.stat_n_frames - self.stat_fps),  # to end
                round(every_n_seconds * self.stat_fps),  # every x frame
            ))

        scene_offsets = [round((self.stat_fps / self.SCENE_FPS) * i)
                         for i in range(self.SECONDS_PER_SCENE * self.SCENE_FPS)]

        extract_frames = [round(main + offset)
                          for main in main_frames
                          for offset in scene_offsets]

        vw, vh = self.stat_width, self.stat_height
        scale = (min(self.DIMS[0], vw), -1) if (vw > vh) else (-1, min(self.DIMS[1], vh))

        (
            ffmpeg
            .input(str(self.source))
            .filter('select', "+".join(f"eq(n,{frame})" for frame in extract_frames))
            .filter('scale', *scale)
            .output(str(self.previews_cache.joinpath("%d.jpg")), vframes=len(extract_frames), vsync=0)
            .run(quiet=True, overwrite_output=True)
        )

        for i in range(len(main_frames)):
            shutil.copyfile(
                self.previews_cache.joinpath(f"{i*(self.SECONDS_PER_SCENE*self.SCENE_FPS)+1}.jpg"),
                self.previews_dir.joinpath(f"{i+1}.jpg")
            )

    def generate_image_preview(self) -> None:
        import shutil
        first_preview = self.previews_dir.joinpath("1.jpg")
        if first_preview.is_file():
            shutil.copyfile(first_preview, self.dest.joinpath("preview.jpg"))

    def generate_animated_preview(self) -> None:
        images = sorted(self.previews_cache.glob("*.jpg"), key=lambda f: int(f.stem))
        first, *frames = map(Image.open, images)
        # saved as gif. better compatibility, but larger in size
        # first.save(self.dest.joinpath("preview.gif"), format="GIF", save_all=True, interlace=True,
        #            append_images=frames, duration=round(1000 / self.FRAMES_PER_SCENE), loop=0, optimize=True)
        # save as newer webp format. way smaller but not as well-supported
        first.save(self.dest.joinpath("preview.webp"), format="WEBP", save_all=True, minimize_size=False,
                   append_images=frames, duration=round(1000 / self.SCENE_FPS), loop=0, method=6)  # , quality=100

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
    def chapters(self) -> t.Iterable[FFProbeChapter]:
        return self.ffprobe['chapters']

    @cached_property
    def meta(self) -> VideoMeta:
        return VideoMeta(
            type='video',
            filename=self.source.name,
            duration=float(self.ffprobe['format']['duration']),
            width=self.main_video_stream['width'],
            height=self.main_video_stream['height'],
            filesize=self.source.stat().st_size,
            video_streams=[VideoStreamMeta(
                is_default=bool(stream['disposition']['default']),
                duration=float(stream['duration']),
                width=stream['width'],
                height=stream['height'],
                avg_fps=int.__truediv__(*map(int, stream['avg_frame_rate'].split("/"))),
            ) for stream in self.video_streams],
            audio_streams=[AudioStreamMeta(
                is_default=bool(stream['disposition']['default']),
                language=stream['tags'].get('language', "<unknown>"),
            ) for stream in self.audio_streams],
            subtitles=[SubtitleStreamMeta(
                is_default=bool(stream['disposition']['default']),
                language=stream['tags'].get('language', "<unknown>"),
            ) for stream in self.subtitle_streams],
            chapters=[ChapterMeta(
                id=chapter['id'],
                # start=chapter['start'],
                start_time=float(chapter['start_time']),
                # end=chapter['end'],
                end_time=float(chapter['end_time']),
                title=chapter['tags']['title'],
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
        return int(self.main_video_stream['nb_frames'])
        # return round(self.stat_duration * self.stat_fps)

    @cached_property
    def stat_fps(self) -> float:
        avg_frame_rate: str = self.main_video_stream['avg_frame_rate']  # '25/1'
        numerator, denominator = avg_frame_rate.split('/')  # ('25', '1')
        return int(numerator) / int(denominator)  # 25 / 1
