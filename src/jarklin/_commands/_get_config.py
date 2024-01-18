# -*- coding=utf-8 -*-
r"""

"""
from functools import cache
import configlib.finder


@cache
def get_config() -> 'configlib.ConfigInterface':
    try:
        fp = configlib.find(
            ".jarklin.ext",
            ".jarklin/config.ext",
            places=[
                configlib.finder.places.cwd(),
            ]
        )
    except configlib.ConfigNotFoundError:
        raise FileNotFoundError("no jarklin config file found in current directory") from None
    else:
        return configlib.load(fp=fp)