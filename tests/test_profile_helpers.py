import unittest

from cheat_editor_manager.constants import DEFAULT_HELP_LINKS, DEFAULT_PREFS
from cheat_editor_manager.profiles import (
    PROFILE_GROUP_CFW,
    PROFILE_GROUP_OTHER,
    PROFILE_GROUP_PC,
    get_profile_groups,
    get_profiles_for_group,
    get_profile_info,
    get_profile_values,
    profile_display_group,
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

    def test_profile_groups_feed_two_step_target_selector(self):
        prefs = {
            **DEFAULT_PREFS,
            "custom_profiles": {
                "MAME Emulator": {"subdir": "MAME", "extensions": [".xml"]}
            },
        }

        self.assertEqual(
            get_profile_groups(prefs),
            [PROFILE_GROUP_CFW, PROFILE_GROUP_PC, PROFILE_GROUP_OTHER],
        )
        self.assertIn(
            "Atmosphere (Switch) (CFW)",
            get_profiles_for_group(prefs, PROFILE_GROUP_CFW),
        )
        self.assertIn("PCSX2 (PS2) - PC", get_profiles_for_group(prefs, PROFILE_GROUP_PC))
        self.assertEqual(
            get_profiles_for_group(prefs, PROFILE_GROUP_OTHER),
            ["MAME Emulator"],
        )
        self.assertEqual(
            profile_display_group(prefs, "MAME Emulator"),
            PROFILE_GROUP_OTHER,
        )
        self.assertNotIn(
            "MAME Emulator",
            get_profiles_for_group(prefs, PROFILE_GROUP_PC),
        )

    def test_default_help_link_names_are_clean_text(self):
        names = " ".join(item["name"] for item in DEFAULT_HELP_LINKS)
        self.assertNotIn("\u00c3", names)
        self.assertNotIn("\u00e2", names)
