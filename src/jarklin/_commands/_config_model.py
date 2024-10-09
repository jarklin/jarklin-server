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
    gzip: bool = None
    optimize: v.Optional['OptimizeConfigModel'] = None
    image_optimization_minimum_size: v.PositiveInt = None
    proxy_fix: v.Optional['ProxyFixConfigModel'] = None

    class ServerConfigModel(v.FlexibleConfigModel):  # yes. allow extra parameters
        host: v.Union[v.Literal["*"], v.Literal["localhost"], v.IPvAnyAddress] = None
        port: v.PositiveInt = None
        listen: str = None
        ipv4: bool = None
        ipv6: bool = None
        unix_socket: str = None
        threads: v.PositiveInt = None
        url_scheme: v.Union[v.Literal["http"], v.Literal["https"]] = None
        backlog: v.PositiveInt = None

    class SessionConfigModel(v.StrictConfigModel):
        permanent: bool = None
        lifetime: v.PositiveInt = None
        refresh_each_request: bool = None
        secret_key: str = None

    class AuthConfigModel(v.StrictConfigModel):
        username: str = None
        password: str = None
        userpass: str = None

    class OptimizeConfigModel(v.StrictConfigModel):
        image: bool = None
        video: bool = None

    class ProxyFixConfigModel(v.StrictConfigModel):
        x_forwarded_for: v.NonNegativeInt = None
        x_forwarded_proto: v.NonNegativeInt = None
        x_forwarded_host: v.NonNegativeInt = None
        x_forwarded_port: v.NonNegativeInt = None
        x_forwarded_prefix: v.NonNegativeInt = None


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
    console: bool = None
    file: v.Optional['FileConfigModel'] = None

    class FileConfigModel(v.StrictConfigModel):
        path: v.constr(strip_whitespace=True, max_length=1) = None
        max_bytes: v.PositiveInt = None
        backup_count: v.PositiveInt = None
