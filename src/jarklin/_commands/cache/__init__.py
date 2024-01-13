# -*- coding=utf-8 -*-
r"""

"""


def run() -> None:
    from ...cache import Cache
    Cache().run()


def generate() -> None:
    from ...cache import Cache
    Cache().iteration()


def remove(ignore_errors: bool) -> None:
    from ...cache import Cache
    Cache().remove(ignore_errors=ignore_errors)


def regenerate() -> None:
    from ...cache import Cache
    cache = Cache()
    cache.remove()
    cache.generate()
