# -*- coding=utf-8 -*-
r"""

"""
import typing as t
from functools import cache
import configlib
from ._logging import configure_logging
from ._process_config import configure_process
from ._config_model import ConfigModel


@t.overload
def get_config() -> 'configlib.ConfigInterface': ...
@t.overload
def get_config(return_fp: bool = True) -> t.Tuple['configlib.ConfigInterface', str]: ...


@cache
def get_config(return_fp: bool = False):
    try:
        fp = configlib.find(
            ".jarklin.ext",
            ".jarklin/config.ext",
            places=[
                configlib.places.cwd(),
            ]
        )
    except configlib.ConfigNotFoundError:
        raise FileNotFoundError("no jarklin config file found in current directory") from None
    else:
        config = configlib.config
        config.merge(configlib.load(fp=fp))
        config.merge(configlib.from_environ(prefix="JARKLIN"))
        try:
            config.validate(ConfigModel, update=False)
        except configlib.ValidationError as validation_error:
            print("Bad configuration file")  # yes. print. logging is only configured with a correct config file
            for error in validation_error.args[0]:
                print(f"- {error['type']}: {error['msg']} ({'->'.join(error['loc'])})")
            exit(1)
        configure_logging(config=config)
        configure_process(config=config)
        if return_fp:
            return config, str(fp.absolute())
        else:
            return config
