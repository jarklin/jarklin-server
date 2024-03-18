#!/usr/bin/python3
# -*- coding=utf-8 -*-
r"""

"""
import sys; sys.path.append('./src')  # noqa
import setuptools
from jarklin import __author__, __version__, __description__, __license__


install_requires = [
    "flask",
    "pillow",
    "ffmpeg-python",
    "config-library[yaml]",
    "flask-compress",
    "waitress",
    "schedule",
    "wcmatch",
    "werkzeug",
]

better_exceptions = ["better-exceptions"]
all_requires = [better_exceptions]

extras_require = {
    'exceptions': better_exceptions,
    'all': all_requires,
}

setuptools.setup(
    name="jarklin",
    version=__version__,
    description=__description__,
    long_description=open("README.md", "r", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    author=__author__,
    license=__license__,
    url="https://github.com/jarklin/jarklin",
    project_urls={
        "Author Github": "https://github.com/PlayerG9",
        "Organisation": "https://github.com/jarklin/",
        "Homepage": "https://jarklin.github.io/",
        "Documentation": "https://jarklin.github.io/",
        "Bug Tracker": "https://github.com/jarklin/jarklin/issues",
    },
    classifiers=[
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
    ],
    python_requires=">=3.6",
    install_requires=install_requires,
    extras_require=extras_require,
    entry_points={
        "console_scripts": [
            "jarklin = jarklin.__main__:main"
        ]
    },
)
