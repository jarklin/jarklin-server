# -*- coding=utf-8 -*-
r"""

"""
import logging.handlers
from pathlib import Path
from configlib import ConfigInterface


SHORT_LOGGING_FORMAT = "{asctime} | {levelname:.3} | {name} | {message}"
LONG_LOGGING_FORMAT = "{asctime} | {levelname:.3} | {name} | {module} | {funcName} | {lineno} | {message}"
DEFAULT_DATEFORMAT = "%Y-%m-%d %H:%M:%S"


def configure_logging(config: ConfigInterface) -> None:
    handlers = []

    if config.getbool('logging', 'console', fallback=True):
        handlers.append(logging.StreamHandler())
        handlers[-1].setFormatter(logging.Formatter(SHORT_LOGGING_FORMAT, DEFAULT_DATEFORMAT, '{'))
        handlers[-1].addFilter(PillowFilter())

    if config.has('logging', 'file'):
        filepath = Path(config.getpath('logging', 'file', 'path', fallback=".jarklin/logs/jarklin.log")).absolute()
        filepath.parent.mkdir(parents=True, exist_ok=True)
        handlers.append(logging.handlers.RotatingFileHandler(
            filename=filepath,
            maxBytes=config.getint('logging', 'file', 'max_bytes', fallback=1024*1024*5),
            backupCount=config.getint('logging', 'file', 'backup_count', fallback=5),
            delay=True,
        ))
        handlers[-1].setFormatter(logging.Formatter(LONG_LOGGING_FORMAT, DEFAULT_DATEFORMAT, '{'))
        handlers[-1].addFilter(PillowFilter())

    logging.basicConfig(
        level=config.getstr('logging', 'level', fallback="WARNING").upper(),
        style='{',
        format=SHORT_LOGGING_FORMAT,
        datefmt=DEFAULT_DATEFORMAT,
        handlers=handlers,
    )


class PillowFilter(logging.Filter):
    def filter(self, record: logging.LogRecord):
        return not record.name.startswith('PIL.')
