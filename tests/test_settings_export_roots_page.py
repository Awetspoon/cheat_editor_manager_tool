import unittest

from cheat_editor_manager.ui.dialogs.settings_export_roots_page import (
    ATMOSPHERE_PROFILE,
    _clear_profile_override,
    _override_profile_names,
    _profile_override,
    _set_profile_override,
)


class SettingsExportRootsPageHelperTests(unittest.TestCase):
    def test_profile_override_helpers_set_trim_and_clear_values(self):
        prefs = {"emulator_paths": {"Existing": "C:/Existing"}}

        _set_profile_override(prefs, "PCSX2", "  C:/Games/PCSX2  ")
        self.assertEqual(_profile_override(prefs, "PCSX2"), "C:/Games/PCSX2")

        _set_profile_override(prefs, "PCSX2", "   ")
        self.assertEqual(_profile_override(prefs, "PCSX2"), "")

        _clear_profile_override(prefs, "Existing")
        self.assertEqual(_profile_override(prefs, "Existing"), "")

    def test_override_profiles_exclude_atmosphere_safeguard(self):
        self.assertNotIn(ATMOSPHERE_PROFILE, _override_profile_names())


if __name__ == "__main__":
    unittest.main()
