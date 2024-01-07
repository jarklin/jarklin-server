# -*- coding=utf-8 -*-
r"""

"""
import re


USER_NAME_PAIR = re.compile(r'^\w+/\w+$')
FULL_URL = re.compile(r'^$')


def download_web_ui(dest: str = None, source: str = None) -> None:
    import urllib.request

    source = _download_source_url(base=source)
    dest = _download_dest(base=dest)
    urllib.request.urlretrieve(url=source, filename=dest)


def _download_source_url(base: str = None) -> str:
    if base is None:
        return f"https://github.com/jarklin/jarklin-web/releases/download/latest/web-ui.tgz"
    if USER_NAME_PAIR.search(base) is not None:  # we assume it's a forked repository
        return f"https://github.com/{base}/releases/download/latest/web-ui.tgz"
    return base


def _download_dest(base: str = None) -> str:
    if base is None:
        return "./web-ui.tgz"
    elif base.endswith("/"):  # directory
        return base + "web-ui.tgz"
    else:
        return base
