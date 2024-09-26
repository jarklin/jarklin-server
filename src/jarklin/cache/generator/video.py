# -*- coding=utf-8 -*-
r"""
video.mp4/
├─ preview.webp
├─ animated.webp
├─ previews/
│  ├─ 1.webp
│  ├─ 2.webp
├─ meta.json
├─ video.type
├─ is-cache
"""
import shutil
import logging
import mimetypes
import typing as t
from pathlib import Path
from contextlib import ExitStack
from functools import cached_property
import undertext
from PIL import Image, ImageStat
from ...common.types import (
    VideoMeta, VideoStreamMeta, AudioStreamMeta, SubtitleStreamMeta, ChapterMeta
)
from ...common.ffmpeg import ffmpeg
from ...common.ffprobe import ffprobe
from ...common.ffprobe.model import (
    FFProbe as FFProbeResult,
    Chapter as FFProbeChapter,
)
from ._base import CacheGenerator


logger = logging.getLogger(__name__)


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

    @cached_property
    def thumbnails_enabled(self) -> bool:
        return self.config.getbool('cache', 'video', 'thumbnails', 'enabled', fallback=True)

    @cached_property
    def thumbnails_delay(self) -> float:
        return self.config.getfloat('cache', 'video', 'thumbnails', 'delay', fallback=15)

    @cached_property
    def thumbnails_dimensions(self) -> t.Tuple[int, int]:
        width = self.config.getint('cache', 'video', 'thumbnails', 'dimensions', 'width', fallback=None)
        height = self.config.getint('cache', 'video', 'thumbnails', 'dimensions', 'height', fallback=None)
        if width is None and height is None:  # default sizes
            width, height = 320, 320
        # fallbacks for easier calculations later on
        if width is None:
            width = height * 10
        if height is None:
            height = width * 10
        return width, height

    # ---------------------------------------------------------------------------------------------------------------- #

    def generate_meta(self) -> None:
        import json
        with open(self.dest / "meta.json", 'w') as file:
            file.write(json.dumps(self.meta))

    def generate_previews(self) -> None:
        main_frames: t.List[int]
        total_frames = self.stat_nb_frames
        logger.debug(f"{self} - total frames: {total_frames}")
        if self.chapters:
            logger.debug(f"{self} - chapters found")
            main_frames = [
                round((chapter.start_time * self.stat_fps) + (self.stat_fps * self.scene_offset))
                for chapter in self.chapters
            ]
        else:
            logger.debug(f"{self} - no chapters. fallback to evenly spread scenes")
            number_of_scenes = self.scenes_for_duration(duration=self.stat_duration)
            every_n_seconds = self.stat_duration / number_of_scenes
            main_frames = list(range(
                round(self.stat_fps),  # from start
                round(total_frames - self.stat_fps),  # to end
                round(every_n_seconds * self.stat_fps),  # every x frame
            ))

        scene_offsets = [round((self.stat_fps / self.scene_fps) * i)
                         for i in range(round(self.seconds_per_scene * self.scene_fps))]

        extract_frames = [round(main + offset)
                          for main in main_frames
                          for offset in scene_offsets]

        vw, vh = self.stat_width, self.stat_height
        scale = (min(self.max_dimensions[0], vw), -2) if (vw > vh) else (-2, min(self.max_dimensions[1], vh))

        logger.debug(f"{self}: running ffmpeg to extract images")
        ffmpeg([
            '-i', str(self.source),  # input
            '-vf', ','.join((
                "select=" + "+".join(f"eq(n\\,{frame})" for frame in extract_frames),  # specify the frames we want
                f'scale={scale[0]}:{scale[1]}',  # re-scale images. (remove and with Pillow?)
            )),
            '-vframes', f"{len(extract_frames)}",  # number of frames to output. maybe could help slightly
            '-vsync', f"{0}",  # don't know why anymore
            '-codec', 'libwebp',
            '-lossless', f"{1}",  # no loss is better for resulting images
            # todo: maybe slightly higher compression-level/quality for reduced file size
            '-compression_level', f"{0}", '-quality', f"{0}",  # I am speed.
            '-y',  # overwrite if existing. prevent blocking
            str(self.previews_cache / "%d.webp"),
        ])
        actual_previews = len(list(self.previews_cache.glob("*.webp")))
        expected_previews = len(extract_frames)
        if actual_previews != expected_previews:
            message = (f"The number of extracted frames does not match the expected amount."
                       f" (actual={actual_previews} != expected={expected_previews})")
            logger.error(f"{self} - {message}")
            raise RuntimeError(message)

        logger.debug(f"{self} - copying main-frames to previews/")
        for i, j in enumerate(range(0, len(extract_frames), len(scene_offsets))):
            source = self.previews_cache.joinpath(f"{j+1}.webp")
            dest = self.previews_dir.joinpath(f"{i+1}.webp")
            if not source.is_file():
                logger.error(f"{self} - frame {dest.name} not found")
            with Image.open(source) as image:
                image.save(dest, format='WEBP', minimize_size=True, method=6, quality=80)

    def generate_image_preview(self) -> None:
        # algorythm to prevent frames/previews of basically only one color.
        # (like completely black from scene-transfer or intro)
        for fp in sorted(self.previews_dir.glob("*.webp"), key=lambda f: int(f.stem)):
            with Image.open(fp) as image:
                stat = ImageStat.Stat(image)
                if max(stat.stddev) > 40:  # check if at least one channel contains vastly different colors
                    logger.debug(f"{self} - Selecting preview {fp.stem} as cover")
                    preview_source = fp
                    break
        else:
            logger.debug(f"{self} - Fallback to first preview as cover")
            preview_source = self.previews_dir.joinpath("1.webp")
        shutil.copyfile(preview_source, self.dest.joinpath("preview.webp"))

    def generate_animated_preview(self) -> None:
        filepaths = sorted(self.previews_cache.glob("*.webp"), key=lambda f: int(f.stem))
        with ExitStack() as stack:
            images: t.List[Image.Image] = [stack.enter_context(Image.open(fp)) for fp in filepaths]
            first, *frames = images
            first.save(self.dest.joinpath("animated.webp"), format="WEBP", save_all=True, minimize_size=True,
                       append_images=frames, duration=round(1000 / self.scene_fps), loop=0, method=6, quality=80)

    def generate_extra(self) -> None:
        self.generate_storyboard()
        self.generate_chapters_webvtt()
        self.generate_subtitles_webvtt()

    def generate_storyboard(self) -> None:
        if not self.thumbnails_enabled:
            return
        logger.debug(f"{self} - Generating storyboard")

        width, height = self.thumbnails_dimensions

        aspect_ratio = self.stat_width / self.stat_height
        if (width / height) >= aspect_ratio:
            width = round(height * aspect_ratio)
        else:
            height = round(width / aspect_ratio)
        logger.debug(f"{self} - storyboard thumbnail size: {width}x{height}")

        logger.debug(f"{self}: running ffmpeg to extract thumbnails")
        ffmpeg([
            '-i', str(self.source),  # input
            '-an',
            '-sn',
            '-vf', f"fps=1/{self.thumbnails_delay},scale={width}:{height}",
            '-codec', 'libwebp',
            '-lossless', f"{1}",  # no loss is better for resulting images
            # todo: maybe slightly higher compression-level/quality for reduced file size
            '-compression_level', f"{0}", '-quality', f"{0}",  # I am speed.
            '-y',  # overwrite if existing. prevent blocking
            str(self.thumbnails_cache / "%d.webp"),
        ])

        thumbnails = sorted(self.thumbnails_cache.glob("*.webp"), key=lambda f: int(f.stem))

        n_horizontal: int = 10
        n_vertical: int = len(thumbnails) // n_horizontal + 1

        size = (n_horizontal * width, n_vertical * height)

        vtt_parts: t.List[undertext.Caption] = []
        logger.debug(f"{self} - generating storyboard.{{vtt,webp}}")
        with Image.new('RGB', size) as storyboard:
            for i, fn in enumerate(thumbnails):
                iy, ix = divmod(i, n_horizontal)
                logger.debug(f"{self} - processing thumbnail {i} at {ix}x{iy}")
                x, y = ix * width, iy * height
                with Image.open(fn) as img:
                    storyboard.paste(img, (x, y))
                    start_ts = i * self.thumbnails_delay
                    vtt_parts.append(undertext.Caption(
                        start=start_ts,
                        end=start_ts+self.thumbnails_delay,
                        text=f'storyboard.webp#xywh={x},{y},{img.width},{img.height}'
                    ))
            logger.debug(f"{self} - saving storyboard.webp")
            storyboard.save( self.dest / "storyboard.webp", format="WEBP", minimize_size=True, method=6, quality=80)
        logger.debug(f"{self} - saving storyboard.vtt")
        undertext.dump(vtt_parts, fp=self.dest / "storyboard.vtt")

    def generate_chapters_webvtt(self) -> None:
        if not self.chapters:
            logger.debug(f"{self} - no chapters found. no chapters.vtt generated")
            return
        try:
            captions = [
                undertext.Caption(start=chapter.start_time, end=chapter.end_time,
                                  text=chapter.tags.get('title'))
                for chapter in self.chapters
            ]
            undertext.dump(captions, self.dest.joinpath("chapters.vtt"))
        except Exception as error:
            logger.error(f"{self} - Failed to generate chapters.vtt", exc_info=error)

    def generate_subtitles_webvtt(self) -> None:
        if not self.ffprobe.subtitle_streams:
            logger.debug(f"{self} - no subtitles found. no subtitles.{{lang}}.vtt are generated")
            return

        image_codecs = {'dvb_subtitle', 'dvd_subtitle', 'hdmv_pgs_subtitle', 'xsub'}
        text_codecs = {'ass', 'jacosub', 'microdvd', 'mov_text', 'mpl2', 'pjs', 'realtext', 'sami', 'srt', 'ssa', 'stl',
                       'subrip', 'subviewer', 'subviewer1', 'text', 'vplayer', 'webvtt'}

        for subtitle in self.ffprobe.subtitle_streams:
            index = subtitle.index
            codec = subtitle.codec_name
            lang = subtitle.tags.get('language')
            fp = self.previews_cache.joinpath(f"subtitles.{lang}.vtt")

            if codec in image_codecs:
                logger.warning(f"image-based-subtitles extraction is currently not supported (#{index}:{lang})")
            elif codec in text_codecs:
                try:
                    ffmpeg([
                        '-i', str(self.source),
                        '-map', f"0:{index}",  # maps subtitle-stream to output-stream
                        '-y',  # overwrite if existing. prevent blocking
                        str(fp),
                    ])
                except Exception as error:
                    logger.error(f"{self} - Failed to extract {fp.name}", exc_info=error)
            else:
                logger.error(f"{self} - Unsupported subtitle formast: {codec}")

    def generate_type(self):
        self.dest.joinpath("video.type").touch()

    def cleanup(self) -> None:
        shutil.rmtree(self.previews_cache, ignore_errors=True)
        shutil.rmtree(self.thumbnails_cache, ignore_errors=True)

    @cached_property
    def previews_cache(self) -> Path:
        path = self.dest.joinpath(".previews")
        shutil.rmtree(path, ignore_errors=True)
        path.mkdir(parents=True)
        return path

    @cached_property
    def thumbnails_cache(self) -> Path:
        path = self.dest.joinpath(".thumbnails")
        shutil.rmtree(path, ignore_errors=True)
        path.mkdir(parents=True)
        return path

    @staticmethod
    def scenes_for_duration(duration: float) -> int:
        boundary2scenes: t.Dict[int, int] = {
            9800: 36,  # 3h
            7200: 24,  # 2h
            4800: 18,  # 1h30m
            3600: 12,  # 1h
            2700: 9,  # 45m
            1800: 6,  # 30m
            600: 5,  # 10m
            300: 4,  # 5m
            180: 3,  # 3m
            60: 2,  # 1m
        }

        for boundary, scenes in boundary2scenes.items():
            if duration >= boundary:
                return scenes
        return 1

    @cached_property
    def ffprobe(self) -> FFProbeResult:
        return ffprobe(self.source)

    @property
    def chapters(self) -> t.List[FFProbeChapter]:
        return self.ffprobe.chapters

    @cached_property
    def meta(self) -> VideoMeta:
        info: FFProbeResult = self.ffprobe
        return VideoMeta(
            type='video',
            filename=self.source.name,
            mimetype=mimetypes.guess_type(self.source)[0],
            duration=info.format.duration,
            width=info.main_video_stream.width,
            height=info.main_video_stream.height,
            filesize=self.source.stat().st_size,
            n_previews=len(self.chapters) or self.scenes_for_duration(duration=self.stat_duration),
            video_streams=[VideoStreamMeta(
                is_default=stream.disposition.default,
                # note: not the best to assume only one stream with one global duration
                duration=stream.duration or self.stat_duration,
                width=stream.width,
                height=stream.height,
                avg_fps=float(stream.avg_frame_rate),
            ) for stream in info.video_streams],
            audio_streams=[AudioStreamMeta(
                is_default=stream.disposition.default,
                language=stream.tags.get('language', "<unknown>"),
            ) for stream in info.audio_streams],
            subtitles=[SubtitleStreamMeta(
                is_default=stream.disposition.default,
                language=stream.tags.get('language', "<unknown>"),
            ) for stream in info.subtitle_streams],
            chapters=[ChapterMeta(
                id=chapter.id,
                # start=chapter.start,
                start_time=chapter.start_time,
                # end=chapter.end,
                end_time=chapter.end_time,
                title=chapter.tags.get('title', None),
            ) for chapter in self.chapters],
        )
    @cached_property
    def stat_width(self) -> int:
        return self.ffprobe.main_video_stream.width

    @cached_property
    def stat_height(self) -> int:
        return self.ffprobe.main_video_stream.height

    @cached_property
    def stat_duration(self) -> float:
        return self.ffprobe.main_video_stream.duration or self.ffprobe.format.duration

    @cached_property
    def stat_nb_frames(self) -> int:
        return self.ffprobe.main_video_stream.nb_frames \
                or round(self.stat_duration * self.stat_fps)

    @cached_property
    def stat_fps(self):
        main_stream = self.ffprobe.main_video_stream
        return main_stream.avg_frame_rate or main_stream.r_frame_rate
