# -*- coding=utf-8 -*-
r"""

"""
import re
import os
import typing as t
import os.path as p
import wcmatch.glob as wcglob


PathResource: t.TypeAlias = t.Union[str, os.PathLike]


class DotIgnore:
    _rules: t.List[t.Tuple[bool, re.Pattern]]

    def __init__(self, *rules: str, root: PathResource = "."):
        self._rules = []

        root = p.abspath(root)
        for rule in rules:
            negated = rule.startswith("!")
            if negated:
                rule = rule[1:]

            if rule.startswith("/"):
                rule = f"{root}{rule}"
            else:
                rule = f"**/{rule}"

                if rule.endswith("/"):  # currently directory-detection not supported
                    rule = rule[:-1]

            (pattern, *_), _ = wcglob.translate(rule, flags=wcglob.IGNORECASE | wcglob.GLOBSTAR)
            self._rules.append((negated, re.compile(pattern)))

    def ignored(self, path: PathResource) -> bool:
        path = p.abspath(path)
        is_ignored = False
        for negated, check in self._rules:
            if check.match(path) is not None:
                if negated:
                    is_ignored = False
                else:
                    is_ignored = True
        # logging.debug(f"{path!s} is {'' if is_ignored else 'not '}ignored")
        return is_ignored
