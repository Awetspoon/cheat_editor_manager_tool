import unittest

from cheat_editor_manager.ui.dialogs.settings_appearance_page import (
    _sync_custom_controls,
    _valid_preview_colour,
)


class FakeMode:
    def __init__(self, value):
        self.value = value

    def get(self):
        return self.value


class FakeWidget:
    def __init__(self):
        self.state = None

    def configure(self, *, state):
        self.state = state


class FakeSection:
    def __init__(self):
        self.visible = None

    def pack(self, **_options):
        self.visible = True

    def pack_forget(self):
        self.visible = False


class SettingsAppearancePageHelperTests(unittest.TestCase):
    def test_valid_preview_colour_accepts_hex_colours_only(self):
        self.assertTrue(_valid_preview_colour("#aabbcc"))
        self.assertFalse(_valid_preview_colour("red"))
        self.assertFalse(_valid_preview_colour("#abc"))

    def test_custom_colour_section_only_shows_in_custom_mode(self):
        widget = FakeWidget()
        section = FakeSection()

        _sync_custom_controls(
            FakeMode("light"),
            [widget],
            custom_section=section,
        )

        self.assertEqual(widget.state, "disabled")
        self.assertFalse(section.visible)

        _sync_custom_controls(
            FakeMode("custom"),
            [widget],
            custom_section=section,
        )

        self.assertEqual(widget.state, "normal")
        self.assertTrue(section.visible)


if __name__ == "__main__":
    unittest.main()
