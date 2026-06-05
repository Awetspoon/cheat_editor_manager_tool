import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import cheat_editor_manager.storage as storage
from cheat_editor_manager.storage import template_store


class StorageTests(unittest.TestCase):
    def test_save_prefs_creates_parent_and_writes_atomically(self):
        with TemporaryDirectory() as tmp:
            prefs_path = Path(tmp) / "nested" / "prefs.json"
            original = storage.PREFS_FILE
            try:
                storage.PREFS_FILE = prefs_path
                storage.save_prefs({"mode": "light", "retroarch_core": "mGBA"})
                self.assertTrue(prefs_path.exists())
                self.assertFalse(prefs_path.with_suffix(".json.tmp").exists())
                saved = prefs_path.read_text(encoding="utf-8")
                self.assertIn('"mode": "light"', saved)
                self.assertIn('"retroarch_core": "mGBA"', saved)
            finally:
                storage.PREFS_FILE = original

    def test_load_prefs_removes_stale_window_memory_keys(self):
        with TemporaryDirectory() as tmp:
            prefs_path = Path(tmp) / "prefs.json"
            prefs_path.write_text(
                (
                    '{'
                    '"mode": "dark",'
                    '"window_remember": true,'
                    '"window_geometry": "900x700",'
                    '"window_asked_once": true'
                    '}'
                ),
                encoding="utf-8",
            )
            original = storage.PREFS_FILE
            try:
                storage.PREFS_FILE = prefs_path
                prefs = storage.load_prefs()
                self.assertEqual(prefs["mode"], "dark")
                self.assertNotIn("window_remember", prefs)
                self.assertNotIn("window_geometry", prefs)
                self.assertNotIn("window_asked_once", prefs)
            finally:
                storage.PREFS_FILE = original

    def test_load_prefs_removes_old_profile_sort_key(self):
        with TemporaryDirectory() as tmp:
            prefs_path = Path(tmp) / "prefs.json"
            prefs_path.write_text(
                '{"mode": "light", "profile_sort": "az"}',
                encoding="utf-8",
            )
            original = storage.PREFS_FILE
            try:
                storage.PREFS_FILE = prefs_path
                prefs = storage.load_prefs()
                self.assertEqual(prefs["mode"], "light")
                self.assertNotIn("profile_sort", prefs)
            finally:
                storage.PREFS_FILE = original

    def test_load_prefs_normalizes_retroarch_preferences(self):
        with TemporaryDirectory() as tmp:
            prefs_path = Path(tmp) / "prefs.json"
            prefs_path.write_text(
                (
                    "{"
                    '"retroarch_cores": ["mGBA", "mGBA", "Default (no subfolder)"],'
                    '"retroarch_core": "Missing"'
                    "}"
                ),
                encoding="utf-8",
            )
            original = storage.PREFS_FILE
            try:
                storage.PREFS_FILE = prefs_path
                prefs = storage.load_prefs()
                self.assertEqual(
                    prefs["retroarch_cores"],
                    ["Default (no subfolder)", "mGBA"],
                )
                self.assertEqual(prefs["retroarch_core"], "Default (no subfolder)")
            finally:
                storage.PREFS_FILE = original

    def test_load_prefs_removes_custom_profile_export_root(self):
        with TemporaryDirectory() as tmp:
            prefs_path = Path(tmp) / "prefs.json"
            prefs_path.write_text(
                (
                    "{"
                    '"custom_profiles": {'
                    '"Arcade": {'
                    '"subdir": "MAME",'
                    '"export_root": "C:/Old/Override"'
                    "}"
                    "}"
                    "}"
                ),
                encoding="utf-8",
            )
            original = storage.PREFS_FILE
            try:
                storage.PREFS_FILE = prefs_path
                prefs = storage.load_prefs()
                self.assertEqual(prefs["custom_profiles"]["Arcade"]["subdir"], "MAME")
                self.assertNotIn("export_root", prefs["custom_profiles"]["Arcade"])
            finally:
                storage.PREFS_FILE = original

    def test_template_store_reads_and_lists_sanitized_names(self):
        with TemporaryDirectory() as tmp:
            original = template_store.TEMPLATES_DIR
            try:
                template_store.TEMPLATES_DIR = Path(tmp) / "templates"
                template_store.write_template(
                    "Bad/Profile",
                    "Simple: One?",
                    "[Cheat]\n00000000 00000000\n",
                )

                self.assertEqual(
                    template_store.read_template("Bad/Profile", "Simple: One?"),
                    "[Cheat]\n00000000 00000000\n",
                )
                self.assertEqual(
                    template_store.list_templates("Bad/Profile"),
                    ["Blank", "Simple One"],
                )
            finally:
                template_store.TEMPLATES_DIR = original

    def test_template_store_uses_fallback_for_invalid_names(self):
        with TemporaryDirectory() as tmp:
            original = template_store.TEMPLATES_DIR
            try:
                template_store.TEMPLATES_DIR = Path(tmp) / "templates"
                template_store.write_template("???", "<<<", "content")

                self.assertEqual(template_store.read_template("???", "<<<"), "content")
                self.assertTrue(
                    (template_store.TEMPLATES_DIR / "Unknown Profile" / "Untitled.txt").exists()
                )
            finally:
                template_store.TEMPLATES_DIR = original


if __name__ == "__main__":
    unittest.main()
