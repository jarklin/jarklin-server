# -*- coding=utf-8 -*-
r"""
Types for the ffprobe json output (only important fields)
"""
import typing as t


class FFProbeResult(t.TypedDict):
    streams: t.List[t.Union['FFProbeVideoStream', 'FFProbeAudioStream', 'FFProbeSubtitleStream']]
    chapters: t.List['FFProbeChapter']
    format: 'FFProbeFormat'


class FFProbeVideoStream(t.TypedDict):
    codec_type: t.Literal['video']
    width: int
    height: int
    avg_frame_rate: str  # eg"25/1"
    duration: str  # str(float)
    nb_frames: str  # str(int)
    disposition: 'FFProbeStreamDisposition'
    tags: 'FFProbeStreamTags'


class FFProbeAudioStream(t.TypedDict):
    codec_type: t.Literal['audio']
    channel_layout: str
    disposition: 'FFProbeStreamDisposition'
    tags: 'FFProbeStreamTags'


class FFProbeSubtitleStream(t.TypedDict):
    codec_type: t.Literal['subtitle']
    disposition: 'FFProbeStreamDisposition'
    tags: 'FFProbeStreamTags'


class FFProbeStreamDisposition(t.TypedDict):
    default: t.Literal[0, 1]


class FFProbeStreamTags(t.TypedDict):
    creation_time: str
    language: str


class FFProbeChapter(t.TypedDict):
    id: int
    start: int
    start_time: str  # str(float)
    end: int
    end_time: str  # str(float)
    tags: 'FFProbeChapterTags'


class FFProbeChapterTags(t.TypedDict):
    title: str


class FFProbeFormat(t.TypedDict):
    filename: str
    nb_streams: int
    duration: str  # str(float)
    size: str  # str(int)
