import unittest

from cheat_editor_manager.ui.dialogs.settings_profiles_page import (
    _compact_table_text,
    _normalize_extensions,
    _profile_table_values,
    _trim_helper_notes,
    _uses_reserved_builtin_layout,
)


class SettingsProfilesPageHelperTests(unittest.TestCase):
    def test_normalize_extensions_adds_dots_and_keeps_default(self):
        self.assertEqual(_normalize_extensions("txt, .cht, pnach"), [".txt", ".cht", ".pnach"])
        self.assertEqual(_normalize_extensions(""), [".txt"])

    def test_reserved_builtin_layout_detects_console_names_and_tokens(self):
        self.assertTrue(
            _uses_reserved_builtin_layout("Switch custom", "MAME", "cheat.txt")
        )
        self.assertTrue(_uses_reserved_builtin_layout("Arcade", "<TID>", "cheat.txt"))
        self.assertFalse(
            _uses_reserved_builtin_layout("Arcade", "MAME", "<Game>.cht")
        )

    def test_trim_helper_notes_strips_and_caps_to_limit(self):
        self.assertEqual(_trim_helper_notes("  short note  ", 20), "short note")
        self.assertEqual(_trim_helper_notes("abcdef", 4), "abcd")

    def test_compact_table_text_keeps_profile_rows_short(self):
        self.assertEqual(_compact_table_text(""), "(No helper note)")
        self.assertEqual(_compact_table_text("a   tidy   note"), "a tidy note")
        self.assertEqual(len(_compact_table_text("x" * 100)), 64)

    def test_profile_table_values_match_visible_columns(self):
        values = _profile_table_values(
            "MAME",
            {
                "subdir": "MAME/cheat",
                "filename_hint": "<Game>",
                "extensions": [".xml"],
                "notes": "Arcade helper note",
            },
        )

        self.assertEqual(
            values,
            ("MAME", "MAME/cheat", "<Game>", ".xml", "Arcade helper note"),
        )


if __name__ == "__main__":
    unittest.main()
