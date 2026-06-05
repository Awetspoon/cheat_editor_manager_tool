import unittest

from cheat_editor_manager.services import export_service


class FakeExportApp:
    def __init__(self):
        self.profiles = {
            "Custom": {"extensions": ["txt", ".cht", ""]},
            "PCSX2": {"extensions": [".pnach"]},
        }

    def get_profile_info(self, profile_name):
        return self.profiles.get(profile_name, {})

    def get_profile_values(self):
        return list(self.profiles)

    def _get_all_known_extensions(self):
        return export_service.get_all_known_extensions(self)


class ExportServiceTests(unittest.TestCase):
    def test_extension_options_normalize_profile_and_all_known_extensions(self):
        app = FakeExportApp()

        profile_exts, all_exts = export_service.extension_options_for_profile(
            app, "Custom"
        )

        self.assertEqual(profile_exts, [".txt", ".cht"])
        self.assertEqual(all_exts, [".txt", ".cht", ".pnach"])


if __name__ == "__main__":
    unittest.main()
