# -*- coding=utf-8 -*-
r"""

"""


def run():
    from ...system import SystemJarklin
    from .._logging import configure_logging

    system = SystemJarklin()
    configure_logging(config=system.config)
    system.run()
