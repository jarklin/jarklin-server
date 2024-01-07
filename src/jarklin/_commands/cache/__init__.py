# -*- coding=utf-8 -*-
r"""

"""


def run() -> None:
    from ...cache import Cache
    Cache().run()


def remove(ignore_errors: bool) -> None:
    from ...cache import Cache
    Cache().remove(ignore_errors=ignore_errors)
