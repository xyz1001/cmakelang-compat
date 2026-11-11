"""Opt-in startup compatibility for the cmakelang 0.6.13 lexer.

Python 3.15 loads the accompanying .start file at normal site startup.
No formatter modules are imported until the application imports them.
"""

import importlib.machinery
import re
import sys


class _Scanner:
    """Scanner for the ordered regular-expression rules used by cmakelang."""

    def __init__(self, lexicon, flags=0):
        self._rules = [(re.compile(pattern, flags), action)
                       for pattern, action in lexicon]
        self.match = None

    def scan(self, text):
        result = []
        position = 0
        while position < len(text):
            for pattern, action in self._rules:
                match = pattern.match(text, position)
                if match is not None:
                    break
            else:
                break
            end = match.end()
            if end == position:
                break
            self.match = match
            value = action(self, match.group()) if callable(action) else action
            if value is not None:
                result.append(value)
            position = end
        return result, text[position:]


class _ReProxy:
    Scanner = _Scanner

    def __getattr__(self, name):
        return getattr(re, name)


def _patch(module):
    parent = sys.modules.get("cmakelang")
    if (getattr(parent, "__version__", None) == "0.6.13"
            and getattr(module, "re", None) is re):
        module.re = _ReProxy()


class _Loader:
    def __init__(self, loader):
        self._loader = loader

    def create_module(self, spec):
        create = getattr(self._loader, "create_module", None)
        return create(spec) if create else None

    def exec_module(self, module):
        self._loader.exec_module(module)
        _patch(module)

    def __getattr__(self, name):
        return getattr(self._loader, name)


class _Finder:
    _cmakelang_compat_finder = True

    def find_spec(self, fullname, path=None, target=None):
        if fullname != "cmakelang.lex":
            return None
        spec = importlib.machinery.PathFinder.find_spec(fullname, path, target)
        if spec is not None and spec.loader is not None:
            spec.loader = _Loader(spec.loader)
        return spec


def install():
    """Install the narrow import hook only on affected Python runtimes."""
    if sys.version_info < (3, 15):
        return
    try:
        re.Scanner([(r"(x)", None)])
    except ValueError:
        pass
    else:
        return

    module = sys.modules.get("cmakelang.lex")
    if module is not None:
        _patch(module)
    if any(getattr(finder, "_cmakelang_compat_finder", False)
           for finder in sys.meta_path):
        return
    # Earlier custom finders keep their existing precedence over PathFinder.
    try:
        index = sys.meta_path.index(importlib.machinery.PathFinder)
    except ValueError:
        return
    sys.meta_path.insert(index, _Finder())
