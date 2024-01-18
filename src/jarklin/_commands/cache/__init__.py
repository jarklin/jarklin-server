# -*- coding=utf-8 -*-
r"""

"""


def run() -> None:
    from ...cache import Cache
    from .._get_config import get_config

    Cache(config=get_config()).run()


def generate() -> None:
    from ...cache import Cache
    from .._get_config import get_config

    Cache(config=get_config()).iteration()


def remove(ignore_errors: bool) -> None:
    from ...cache import Cache
    from .._get_config import get_config

    Cache(config=get_config()).remove(ignore_errors=ignore_errors)


def regenerate() -> None:
    from ...cache import Cache
    from .._get_config import get_config

    cache = Cache(config=get_config())
    cache.remove()
    cache.generate()
