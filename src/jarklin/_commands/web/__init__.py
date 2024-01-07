# -*- coding=utf-8 -*-
r"""

"""


def run(host: str = None, port: int = None) -> None:
    from ...web import application
    application.run(host=host, port=port)
