"""Check automatic startup against an installed wheel in a fresh process."""

import re
import sys

assert "cmakelang" not in sys.modules, "formatter imported eagerly at startup"
original_scanner = re.Scanner
if sys.version_info >= (3, 15):
    assert "cmakelang_compat" in sys.modules, "startup file did not run"
    assert sum(bool(getattr(finder, "_cmakelang_compat_finder", False))
               for finder in sys.meta_path) == 1

import cmakelang.lex as lex

assert re.Scanner is original_scanner, "stdlib Scanner was replaced"
if sys.version_info >= (3, 15):
    assert lex.re is not re, "lexer compatibility proxy missing"
    assert lex.re.compile is re.compile
else:
    assert lex.re is re, "unaffected lexer was patched"

text = 'project(example)\nset(value [=[hello Ω]=])\n'
assert "".join(token.spelling for token in lex.tokenize(text)) == text
print("Installed-wheel startup and lexer check passed")
