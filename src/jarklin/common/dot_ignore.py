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

    def __init__(self, *rules: str, root: PathResource = "."):
        self._rules = []

        root = p.abspath(root)
        for rule in rules:
            rule = rule.strip()
            negated = rule.startswith("!")
            if negated:
                rule = rule[1:]

            if rule.startswith("/"):
                rule = f"{root}{rule}"
            else:
                rule = f"*/{rule}"

            if rule.endswith("/"):  # currently directory-detection not supported
                rule = rule[:-1]

            self._rules.append((negated, re.compile(fnmatch.translate(rule).replace(".*", "[^/]*"))))

    def ignored(self, path: PathResource) -> bool:
        path = p.abspath(path)
        is_ignored = False
        for negated, check in self._rules:
            if check.match(path) is not None:
                if negated:
                    is_ignored = False
                else:
                    is_ignored = True
        return is_ignored


# class DotIgnore:
#     _rules: t.List[t.Tuple[bool, str, re.Pattern]]
#
#     def __init__(self, *rules: str, root: PathResource = "."):
#         self._rules = []
#
#         root = p.abspath(root)
#         for rule in rules:
#             rule = rule.strip()
#             if not rule or rule.startswith("#"):
#                 continue
#
#             negated = rule.startswith("!")
#             if negated:
#                 rule = rule[1:]
#
#             if rule.startswith("/"):
#                 rule = p.join(root, rule[1:])
#             else:
#                 rule = p.join(root, '**', rule)
#
#             self._rules.append((negated, rule, re.compile(fnmatch.translate(rule))))
#
#     def ignored(self, path: PathResource) -> bool:
#         path = p.abspath(path)
#         is_ignored = False
#         for negated, rule, check in self._rules:
#             if check.match(path) is not None:
#                 if negated:
#                     is_ignored = False
#                 else:
#                     is_ignored = True
#         return is_ignored
