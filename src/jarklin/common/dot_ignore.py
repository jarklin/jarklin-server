# -*- coding=utf-8 -*-
r"""

"""
import re
import os
import os.path as p
import typing as t
import fnmatch


PathResource: t.TypeAlias = t.Union[str, os.PathLike]


class DotIgnore:
    _rules: t.List[t.Tuple[bool, re.Pattern]]

    def __init__(self, file: t.TextIO):
        self._rules = []
        _root = p.abspath(p.dirname(getattr(file, 'name', ".")))
        for line in file:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            negated = line.startswith("!")
            if negated:
                line = line[1:]
            if line.startswith("/"):
                line = p.join(_root, line[1:])
            else:
                line = p.join(_root, '**', line)
            if line.endswith("/"):
                line = line[:-1]
            self._rules.append((negated, re.compile(fnmatch.translate(line))))

    @classmethod
    def from_iterable(cls, *rules: str) -> 'DotIgnore':
        import io
        return DotIgnore(io.StringIO("\n".join(rules)))

    def ignored(self, path: PathResource) -> bool:
        path = p.abspath(path)
        is_ignored = False
        for negated, rule in self._rules:
            if rule.match(path) is not None:
                if negated:
                    is_ignored = False
                else:
                    is_ignored = True
        return is_ignored
