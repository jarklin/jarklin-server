# -*- coding=utf-8 -*-
r"""

"""
import logging
import os.path
import sys
import time
import typing as t
from functools import cached_property
import subprocess
import configlib.finder


class SystemJarklin:
    def __init__(self):
        self.processes: t.List[subprocess.Popen] = []

    @cached_property
    def config(self) -> 'configlib.ConfigInterface':
        return configlib.find_and_load(
            "jarklin.yml", "jarklin.yaml",
            "jarklin/config.yml", "jarklin/config.yaml",
            places=[configlib.finder.places.etc()]
        )

    def run(self):
        name: str = ""
        try:
            self.init()
        except Exception as error:
            logging.critical(f"Failed to initialize jarklin {name!r}", exc_info=error)
            self.end()
            sys.exit(1)
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.end()

    def init(self):
        for config in self.config.get("jarklins"):
            config: 'ServiceConfig'
            name = config['name']
            files = config['files']
            if not os.path.isdir(files):
                raise NotADirectoryError(files)
            logging.info(f"Setting up jarklin {name!r} in {files!r}")
            if config.get('web', default=False):
                self.processes.append(
                    subprocess.Popen(
                        [sys.executable, 'web', 'run'],
                        cwd=files,
                        env=config.get('env'),
                    )
                )
            if config.get('cache', default=False):
                self.processes.append(
                    subprocess.Popen(
                        [sys.executable, 'cache', 'run'],
                        cwd=files,
                        env=config.get('env'),
                    )
                )

    def end(self):
        for process in self.processes:
            process.terminate()
        for process in self.processes:
            process.wait()


class ServiceConfig(t.TypedDict):
    name: str
    description: t.Optional[str]
    files: str
    env: t.Optional[t.Dict[str, str]]
    web: t.Optional[bool]
    cache: t.Optional[bool]
