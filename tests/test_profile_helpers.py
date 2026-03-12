import unittest

from cheat_editor_manager.constants import DEFAULT_PREFS
from cheat_editor_manager.profiles import get_profile_info, get_profile_values, profile_template_path


class ProfileHelperTests(unittest.TestCase):
    def test_profile_helpers_return_expected_defaults(self):
        values = get_profile_values(DEFAULT_PREFS)
        self.assertIn("Atmosphere (Switch) (CFW)", values)
        info = get_profile_info(DEFAULT_PREFS, "Atmosphere (Switch) (CFW)")
        path = profile_template_path(DEFAULT_PREFS, "Atmosphere (Switch) (CFW)", info)
        self.assertIn("atmosphere/contents", path.lower())
