# -*- coding=utf-8 -*-
r"""

"""
import typing as t
from .types import PathSource


def parse_userpass(fp: PathSource) -> t.Dict[str, str]:
    userpass = {}
    with open(fp) as file:
        for i, line in enumerate(file):
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            username, sep, password = line.partition(":")
            if not sep:
                raise SyntaxError(f"invalid username:password pair in line {i+1} of userpass file")
            if username in userpass:
                raise KeyError(f"username {username!r} is duplicate in userpass file")
            userpass[username] = password
    return userpass
