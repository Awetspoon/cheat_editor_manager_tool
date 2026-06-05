import unittest

from cheat_editor_manager.ui.dialogs.extension_dialog import (
    _extension_hint,
    _normalize_extension_choice,
)


class ExtensionDialogHelperTests(unittest.TestCase):
    def test_custom_extension_gets_dot_and_lowercase(self):
        self.assertEqual(_normalize_extension_choice("PNACH", ".txt"), ".pnach")

    def test_selected_extension_is_used_when_custom_is_empty(self):
        self.assertEqual(_normalize_extension_choice("", ".CHT"), ".cht")

    def test_blank_values_fall_back_to_text_extension(self):
        self.assertEqual(_normalize_extension_choice("  ", ""), ".txt")

    def test_extension_hint_matches_custom_state(self):
        self.assertIn("profile extension", _extension_hint(False))
        self.assertIn("Type the file extension", _extension_hint(True))


if __name__ == "__main__":
    unittest.main()
