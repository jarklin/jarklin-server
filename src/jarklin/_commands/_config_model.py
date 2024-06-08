# -*- coding=utf-8 -*-
r"""

"""
from configlib import validation as v


__all__ = ['ConfigModel']


class ConfigModel(v.StrictConfigModel):
    web: v.Optional['WebConfigModel'] = None
    cache: v.Optional['CacheConfigModel'] = None
    logging: v.Optional['LoggingConfigModel'] = None


class WebConfigModel(v.StrictConfigModel):
    debug: bool = None
    baseurl: v.constr(strip_whitespace=True, pattern=r'^/.*$') = None
    server: v.Optional['ServerConfigModel'] = None
    session: v.Optional['SessionConfigModel'] = None
    auth: v.Optional['AuthConfigModel'] = None
    optimize: v.Optional['OptimizeConfigModel'] = None
    image_optimization_minimum_size: v.PositiveInt = None

    class ServerConfigModel(v.StrictConfigModel):
        host: v.IPvAnyAddress = None
        port: v.PositiveInt = None

    class SessionConfigModel(v.StrictConfigModel):
        permanent: bool = None
        lifetime: v.PositiveInt = None
        refresh_each_request: bool = None

    class AuthConfigModel(v.StrictConfigModel):
        username: str = None
        password: str = None
        userpass: str = None

    class OptimizeConfigModel(v.StrictConfigModel):
        image: bool = None
        video: bool = None


class CacheConfigModel(v.StrictConfigModel):
    gallery: v.Optional['GalleryConfigModel'] = None
    video: v.Optional['VideoConfigModel'] = None
    ignore: v.Optional[v.Sequence[str]] = None

    class GalleryConfigModel(v.StrictConfigModel):
        dimensions: v.Optional['DimensionsModel'] = None
        animated: v.Optional['AnimatedConfigModel'] = None

        class DimensionsModel(v.StrictConfigModel):
            width: v.PositiveInt = None
            height: v.PositiveInt = None

        class AnimatedConfigModel(v.StrictConfigModel):
            frame_time: v.PositiveFloat = None
            max_images: v.PositiveInt = None

    class VideoConfigModel(v.StrictConfigModel):
        dimensions: v.Optional['DimensionsModel'] = None
        animated: v.Optional['AnimatedConfigModel'] = None

        class DimensionsModel(v.StrictConfigModel):
            width: v.PositiveInt = None
            height: v.PositiveInt = None

        class AnimatedConfigModel(v.StrictConfigModel):
            scene_length: v.PositiveFloat = None
            fps: v.PositiveInt = None


class LoggingConfigModel(v.StrictConfigModel):
    level: v.Union[
        v.Literal['DEBUG'],
        v.Literal['INFO'],
        v.Literal['WARNING'],
        v.Literal['ERROR'],
        v.Literal['CRITICAL'],
    ] = None
    file: v.Optional['FileConfigModel'] = None

    class FileConfigModel(v.StrictConfigModel):
        path: v.constr(strip_whitespace=True, max_length=1) = None
        max_bytes: v.PositiveInt = None
        backup_count: v.PositiveInt = None
