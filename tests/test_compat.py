import importlib
import os
import re
import subprocess
import sys
import unittest
from unittest import mock

import cmakelang_compat as compat


class ScannerTests(unittest.TestCase):
    def test_priority_backrefs_callbacks_flags_and_remainder(self):
        seen = []

        def capture(scanner, text):
            seen.append(scanner.match.group(1))
            return text.upper()

        scanner = compat._Scanner([
            (r"(a+)\1", capture),
            (r"a+", "fallback"),
            (r"\s+", None),
            (r"x.y", lambda scanner, text: text),
        ], re.DOTALL)
        self.assertEqual(scanner.scan("aaaa x\ny!"), (["AAAA", "x\ny"], "!"))
        self.assertEqual(seen, ["aa"])

    def test_zero_length_stops_without_action_or_fallback(self):
        scanner = compat._Scanner([(r"a*", lambda s, t: self.fail()),
                                   (r"b", "b")])
        self.assertEqual(scanner.scan("b"), ([], "b"))

    def test_proxy_delegates_without_changing_stdlib(self):
        proxy = compat._ReProxy()
        self.assertIs(proxy.compile, re.compile)
        self.assertIsNot(proxy.Scanner, re.Scanner)
        self.assertIs(sys.modules["re"], re)


class InstallationTests(unittest.TestCase):
    def test_lazy_startup_and_idempotence_in_fresh_process(self):
        code = ("import sys, cmakelang_compat as c; "
                "c.install(); c.install(); "
                "assert 'cmakelang' not in sys.modules; "
                "assert sum(bool(getattr(f, '_cmakelang_compat_finder', False)) "
                "for f in sys.meta_path) <= 1")
        subprocess.run([sys.executable, "-c", code], check=True, env=os.environ.copy())

    def test_version_guard_and_already_loaded(self):
        class Parent:
            __version__ = "0.6.12"

        class Lex:
            re = re

        module = Lex()
        with mock.patch.dict(sys.modules, {"cmakelang": Parent(), "cmakelang.lex": module}):
            compat.install()
            self.assertIs(module.re, re)
            Parent.__version__ = "0.6.13"
            compat.install()
            if sys.version_info >= (3, 15):
                self.assertIsNot(module.re, re)
                current = module.re
                compat.install()
                self.assertIs(module.re, current)
            else:
                self.assertIs(module.re, re)

    def test_finder_preserves_existing_priority(self):
        sentinel = object()
        with mock.patch.object(sys, "meta_path", [sentinel, importlib.machinery.PathFinder]):
            compat.install()
            self.assertIs(sys.meta_path[0], sentinel)
            self.assertIs(sys.meta_path[-1], importlib.machinery.PathFinder)

    def test_successful_probe_leaves_loaded_module_and_finders_unchanged(self):
        class Parent:
            __version__ = "0.6.13"

        class Lex:
            re = re

        module = Lex()
        sentinel = object()
        finders = [sentinel, importlib.machinery.PathFinder]
        with (mock.patch.object(sys, "version_info", (3, 15)),
              mock.patch.object(sys, "meta_path", finders),
              mock.patch.object(re, "Scanner", return_value=object()) as probe,
              mock.patch.dict(sys.modules, {"cmakelang": Parent(), "cmakelang.lex": module})):
            compat.install()
            probe.assert_called_once()
            self.assertEqual(finders, [sentinel, importlib.machinery.PathFinder])
            self.assertIs(module.re, re)

    def test_affected_runtime_exact_idempotence_and_finder_priority(self):
        class Parent:
            __version__ = "0.6.13"

        class Lex:
            re = re

        module = Lex()
        sentinel = object()
        finders = [sentinel, importlib.machinery.PathFinder]
        with (mock.patch.object(sys, "version_info", (3, 15)),
              mock.patch.object(sys, "meta_path", finders),
              mock.patch.object(re, "Scanner", side_effect=ValueError),
              mock.patch.dict(sys.modules, {"cmakelang": Parent(), "cmakelang.lex": module})):
            compat.install()
            proxy = module.re
            compat.install()
            self.assertIs(module.re, proxy)
            self.assertIsNot(proxy, re)
            self.assertEqual(len(finders), 3)
            self.assertIs(finders[0], sentinel)
            self.assertIsInstance(finders[1], compat._Finder)
            self.assertIs(finders[2], importlib.machinery.PathFinder)


@unittest.skipUnless(sys.version_info >= (3, 15), "requires affected Python")
class LexerTests(unittest.TestCase):
    def test_import_reload_and_lexer_fixtures(self):
        compat.install()
        try:
            import cmakelang.lex as lex
        except ImportError as exc:
            self.skipTest(str(exc))
        self.assertIsNot(lex.re, re)
        self.assertIs(lex.re.compile, re.compile)
        text = ('\ufeffmacro(custom arg)\r\n'
                '  custom([=[bracket\ntext]=] "quoted \\\"unicode Ω")\r\n'
                '  #[==[comment\ncontent]==]\r\n'
                '  # cmake-format: off\r\n'
                '  custom( x )\r\n'
                '  # cmake-format: on\r\nendmacro()\r\n')
        tokens = lex.tokenize(text)
        self.assertEqual("".join(t.spelling for t in tokens), text)
        names = {t.type.name for t in tokens}
        self.assertTrue({"BYTEORDER_MARK", "BRACKET_ARGUMENT", "BRACKET_COMMENT",
                         "QUOTED_LITERAL", "FORMAT_OFF", "FORMAT_ON"} <= names)
        self.assertEqual(lex.parse_bracket_argument("[=[bracket\ntext]=]"),
                         ("[=[", "bracket\ntext", "]=]"))
        self.assertEqual(lex.parse_bracket_comment("#[=[hi]=]"), ("#[=[", "hi", "]=]"))
        importlib.reload(lex)
        self.assertIsNot(lex.re, re)
        self.assertEqual("".join(t.spelling for t in lex.tokenize(text)), text)


if __name__ == "__main__":
    unittest.main()
