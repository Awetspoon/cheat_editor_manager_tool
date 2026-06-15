import unittest
from unittest.mock import Mock, patch

from cheat_editor_manager.services import export_service


class FakeVar:
    def __init__(self, value=""):
        self.value = value

    def get(self):
        return self.value

    def set(self, value):
        self.value = value


class FakeEditor:
    def __init__(self, text=""):
        self.text = text

    def get(self, *_):
        return self.text


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


class FakeQuickExportApp:
    def __init__(self, out_dir):
        self.profile_var = FakeVar("Custom")
        self.editor = FakeEditor("[Cheat]\n00000000 00000000")
        self.status = FakeVar()
        self.out_dir = out_dir

    def _validate_export_inputs(self, _profile):
        return None

    def build_export_plan(self, _profile):
        return {
            "out_dir": self.out_dir,
            "files": [],
        }

    def get_profile_info(self, _profile):
        return {}


class ExportServiceTests(unittest.TestCase):
    def test_extension_options_normalize_profile_and_all_known_extensions(self):
        app = FakeExportApp()

        profile_exts, all_exts = export_service.extension_options_for_profile(
            app, "Custom"
        )

        self.assertEqual(profile_exts, [".txt", ".cht"])
        self.assertEqual(all_exts, [".txt", ".cht", ".pnach"])

    def test_quick_export_reports_export_folder_creation_failure(self):
        out_dir = Mock()
        out_dir.mkdir.side_effect = PermissionError("blocked")
        app = FakeQuickExportApp(out_dir)

        with patch(
            "cheat_editor_manager.services.export_service.messagebox.showerror"
        ) as showerror:
            export_service.quick_export(app)

        showerror.assert_called_once()
        self.assertEqual(showerror.call_args.args[0], "Quick Export")
        self.assertIn("Could not create export folder", showerror.call_args.args[1])
        self.assertIn("blocked", showerror.call_args.args[1])
        self.assertEqual(app.status.get(), "")


if __name__ == "__main__":
    unittest.main()
