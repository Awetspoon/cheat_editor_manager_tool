import unittest

from cheat_editor_manager.constants import DEFAULT_HELP_LINKS, DEFAULT_PREFS
from cheat_editor_manager.profiles import (
    PROFILE_GROUP_CFW,
    PROFILE_GROUP_OTHER,
    PROFILE_GROUP_PC,
    get_profile_info,
    get_profile_values,
    profile_target_group,
    profile_template_path,
)


class ProfileHelperTests(unittest.TestCase):
    def test_profile_helpers_return_expected_defaults(self):
        values = get_profile_values(DEFAULT_PREFS)
        self.assertIn("Atmosphere (Switch) (CFW)", values)
        info = get_profile_info(DEFAULT_PREFS, "Atmosphere (Switch) (CFW)")
        path = profile_template_path(DEFAULT_PREFS, "Atmosphere (Switch) (CFW)", info)
        self.assertIn("atmosphere/contents", path.lower())

    def test_profile_values_group_cfw_before_pc_without_fake_dividers(self):
        values = get_profile_values(DEFAULT_PREFS)

        self.assertLess(
            values.index("Nintendo 3DS (CFW) (Luma)"),
            values.index("Yuzu (Switch) - PC"),
        )
        self.assertEqual(
            profile_target_group("Atmosphere (Switch) (CFW)"),
            PROFILE_GROUP_CFW,
        )
        self.assertEqual(profile_target_group("PCSX2 (PS2) - PC"), PROFILE_GROUP_PC)
        self.assertEqual(profile_target_group("My Custom Target"), PROFILE_GROUP_OTHER)

    def test_default_help_link_names_are_clean_text(self):
        names = " ".join(item["name"] for item in DEFAULT_HELP_LINKS)
        self.assertNotIn("\u00c3", names)
        self.assertNotIn("\u00e2", names)
