import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
UI_ROOT = PROJECT_ROOT / "cheat_editor_manager" / "ui"
FORBIDDEN_RUNTIME_UI_MARKERS = (
    "coming soon",
    "lorem ipsum",
    "todo",
    "fixme",
    "not implemented",
    "stub",
)


class UiCleanupTests(unittest.TestCase):
    def test_runtime_ui_source_has_no_fake_feature_markers(self):
        for path in UI_ROOT.rglob("*.py"):
            source = path.read_text(encoding="utf-8").casefold()
            for marker in FORBIDDEN_RUNTIME_UI_MARKERS:
                self.assertNotIn(marker, source, f"{marker!r} found in {path}")


if __name__ == "__main__":
    unittest.main()
