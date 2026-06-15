import unittest

from cheat_editor_manager.ui.dialogs.text_prompt_dialog import normalize_prompt_value


class TextPromptDialogTests(unittest.TestCase):
    def test_normalize_prompt_value_trims_input(self):
        self.assertEqual(normalize_prompt_value("  New Template  "), "New Template")
        self.assertEqual(normalize_prompt_value("   "), "")


if __name__ == "__main__":
    unittest.main()
