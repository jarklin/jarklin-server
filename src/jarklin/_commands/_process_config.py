# -*- coding=utf-8 -*-
r"""

"""
import os
import logging
from configlib import ConfigInterface


def configure_process(config: ConfigInterface) -> None:
    if hasattr(os, 'nice'):
        niceness = os.environ.get('NICENESS')
        if niceness is not None:
            niceness = int(niceness)
        if niceness is None:
            niceness = config.getint('process', 'niceness', fallback=None)
        if niceness is not None:
            current = os.nice(0)
            current = os.nice(-current + niceness)
            logging.debug(f'Updated Niceness to: {current}')
