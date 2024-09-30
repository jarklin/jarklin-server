# -*- coding=utf-8 -*-
r"""

"""
import logging
import typing as t
from os import PathLike
from pathlib import Path


__all__ = ['FileIndex']


logger = logging.getLogger(__name__)


class FileIndex:
    fp: Path
    root: Path = None
    _index: t.List[Path]

    def __init__(self, root: PathLike):
        self.root = Path(root)
        self.fp = self.root / "file-index.txt"
        self._index = []

    def __iter__(self):
        return iter(self._index)

    def __len__(self):
        return len(self._index)

    def __bool__(self):
        return bool(self._index)

    def __contains__(self, item: PathLike):
        return item in self._index

    def exists(self) -> bool:
        return self.fp.exists()

    def load(self) -> None:
        r""" loads the index from disk """
        logger.info("Loading index from disk")
        with open(self.fp, "r") as f:
            self._index.clear()
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"): continue
                self._index.append(self.root / line)

    def ensure_loaded(self) -> 'FileIndex':
        if self.exists():
            self.load()
        return self

    def save(self) -> None:
        r""" saves the index to disk """
        logger.info("Saving index to disk")
        with open(self.fp, "w") as f:
            for fp in self._index:
                f.write(f"{fp.relative_to(self.root)!s}\n")

    def add_file(self, file: PathLike) -> Path:
        r""" add a file to the index (memory only) """
        fp = self.root / file
        logger.debug("Adding file to index: %s", fp)
        self._index.append(fp)
        return fp

    def unlink(self, missing_ok: bool=False) -> None:
        r""" unlinks the file-index itself """
        logger.debug("Unlinking file-index from disk")
        self.fp.unlink(missing_ok=missing_ok)

    def unlink_indexed(self, cleanup_directories: bool = True) -> None:
        r""" unlinks all indexed files """
        for fp in self._index:  # remove the files
            logger.warning("Unlinking file: %s", fp)
            fp.unlink(missing_ok=True)
        if cleanup_directories:
            for fp in self._index:  # removes empty directories
                for parent in fp.parents:
                    if parent == self.root: break  # root-dir -> stop
                    if not parent.exists(): break  # does not exist -> stop
                    if next(fp.iterdir(), None) is not None: break  # not empty -> stop
                    logger.warning("Unlinking directory: %s", fp)
                    fp.unlink()  # rmdir
