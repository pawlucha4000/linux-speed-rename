import os
import re
import shutil
import subprocess
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from mehrfach_umbenennen import i18n  # noqa: E402

POT = os.path.join(i18n.LOCALE_DIR, "messages.pot")


def pot_ids():
    with open(POT, encoding="utf-8") as f:
        return {m.replace('\\"', '"') for m in re.findall(r'^msgid "(.*)"$', f.read(), re.M) if m}


class LanguageChoiceTest(unittest.TestCase):
    def test_system_language_is_used(self):
        self.assertEqual(i18n.pick_language({"LANG": "de_AT.UTF-8"}), "de")
        self.assertEqual(i18n.pick_language({"LANGUAGE": "fr_CA:fr", "LANG": "fr_CA.UTF-8"}), "fr")
        self.assertEqual(i18n.pick_language({"LANG": "pt_BR.UTF-8"}), "pt")

    def test_language_list_order(self):
        self.assertEqual(i18n.pick_language({"LANGUAGE": "ja:nl:de", "LANG": "ja_JP.UTF-8"}), "nl")

    def test_fallback_is_english(self):
        self.assertEqual(i18n.pick_language({"LANG": "ja_JP.UTF-8"}), "en")
        self.assertEqual(i18n.pick_language({"LANG": "C"}), "en")
        self.assertEqual(i18n.pick_language({}), "en")

    def test_forced_language(self):
        self.assertEqual(i18n.pick_language({"MEHRFACH_UMBENENNEN_LANG": "it", "LANG": "de_DE.UTF-8"}), "it")


class CatalogTest(unittest.TestCase):
    def test_every_language_is_complete(self):
        ids = pot_ids()
        for code in i18n.available_languages():
            if code == "en":
                continue
            with self.subTest(lang=code):
                cat = i18n.load_po(os.path.join(i18n.LOCALE_DIR, code + ".po"))
                self.assertEqual(ids - set(cat), set(), f"{code}.po fehlt / missing")

    def test_placeholders_kept(self):
        for code in i18n.available_languages():
            if code == "en":
                continue
            cat = i18n.load_po(os.path.join(i18n.LOCALE_DIR, code + ".po"))
            for mid, mstr in cat.items():
                with self.subTest(lang=code, msgid=mid):
                    self.assertEqual(sorted(re.findall(r"\{\w+\}", mid)), sorted(re.findall(r"\{\w+\}", mstr)))

    def test_every_language_has_help(self):
        for code in i18n.available_languages():
            with self.subTest(lang=code):
                self.assertTrue(os.path.isfile(os.path.join(i18n.HELP_DIR, code + ".txt")))

    def test_help_markup_is_valid(self):
        try:
            import gi
            gi.require_version("Pango", "1.0")
            from gi.repository import Pango
        except (ImportError, ValueError):
            self.skipTest("Pango not available")
        for name in os.listdir(i18n.HELP_DIR):
            with self.subTest(file=name):
                with open(os.path.join(i18n.HELP_DIR, name), encoding="utf-8") as f:
                    Pango.parse_markup(f.read(), -1, "\0")

    @unittest.skipUnless(shutil.which("msgfmt"), "msgfmt not installed")
    def test_po_files_valid_for_msgfmt(self):
        for code in i18n.available_languages():
            if code == "en":
                continue
            path = os.path.join(i18n.LOCALE_DIR, code + ".po")
            r = subprocess.run(["msgfmt", "-c", "-o", os.devnull, path], capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr)


if __name__ == "__main__":
    unittest.main()
