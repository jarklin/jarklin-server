# -*- coding=utf-8 -*-
r"""

"""


def run() -> None:
    from ...cache import Cache
    from .._get_config import get_config

    config, _ = get_config()

    Cache(config=config).run()


def generate() -> None:
    from ...cache import Cache
    from .._get_config import get_config

    config, _ = get_config()

    Cache(config=config).iteration()


def remove(ignore_errors: bool) -> None:
    from ...cache import Cache
    from .._get_config import get_config

    config, _ = get_config()

    Cache(config=config).remove(ignore_errors=ignore_errors)


def regenerate() -> None:
    from ...cache import Cache
    from .._get_config import get_config

    config, _ = get_config()

    cache = Cache(config=config)
    cache.remove()
    cache.generate()
