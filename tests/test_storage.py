import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from cheat_editor_manager import storage


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


if __name__ == "__main__":
    unittest.main()
