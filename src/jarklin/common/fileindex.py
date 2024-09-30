# -*- coding=utf-8 -*-
r"""

"""
import typing as t
from os import PathLike
from pathlib import Path


__all__ = ['FileIndex']


class FileIndex:
    fp: Path
    root: Path = None
    _index: t.List[Path]

    def __init__(self, fp: PathLike):
        self.fp = Path(fp)
        self.root = self.fp.parent
        self._index = []

    def exists(self) -> bool:
        return self.fp.exists()

    def load(self) -> None:
        r""" loads the index from disk """
        with open(self.fp, "r") as f:
            self._index.clear()
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"): continue
                self._index.append(self.root / line)

    def save(self) -> None:
        r""" saves the index to disk """
        with open(self.fp, "w") as f:
            for fp in self._index:
                f.write(f"{fp.relative_to(self.root)!s}")

    def add_file(self, file: PathLike):
        r""" add a file to the index (memory only) """
        self._index.append(self.root / file)

    def unlink(self, missing_ok: bool=False) -> None:
        r""" unlinks the file-index itself """
        self.fp.unlink(missing_ok=missing_ok)

    def unlink_indexed(self) -> None:
        r""" unlinks all indexed files """
        for fp in self._index:
            fp.unlink(missing_ok=True)
