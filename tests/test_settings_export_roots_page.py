import unittest

from cheat_editor_manager.ui.dialogs.settings_export_roots_page import (
    ATMOSPHERE_PROFILE,
    _override_profile_names,
    _set_effective_from_override,
)


class SettingsExportRootsPageHelperTests(unittest.TestCase):
    def test_effective_root_uses_override_when_present(self):
        class Var:
            def __init__(self):
                self.value = ""

            def set(self, value):
                self.value = value

        detail_vars = {"effective": Var(), "note": Var()}

        _set_effective_from_override(
            detail_vars,
            inherited_root="C:/Exports",
            override="C:/PCSX2",
        )

        self.assertEqual(detail_vars["effective"].value, "C:/PCSX2")
        self.assertIn("override path", detail_vars["note"].value)

        _set_effective_from_override(
            detail_vars,
            inherited_root="C:/Exports",
            override="",
        )

        self.assertEqual(detail_vars["effective"].value, "C:/Exports")
        self.assertIn("default Export Root", detail_vars["note"].value)

    def test_override_profiles_exclude_atmosphere_safeguard(self):
        self.assertNotIn(ATMOSPHERE_PROFILE, _override_profile_names())


if __name__ == "__main__":
    unittest.main()
