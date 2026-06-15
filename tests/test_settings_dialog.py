from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from cheat_editor_manager.ui.dialogs.settings_dialog import _apply_settings_and_close


class FakeSettingsController:
    def __init__(self):
        self.save_to_prefs = Mock()


class SettingsDialogSaveTests(unittest.TestCase):
    def test_apply_settings_saves_and_refreshes_main_app_state(self):
        app = SimpleNamespace(
            prefs={"mode": "light"},
            apply_theme=Mock(),
            _sync_core_dropdown=Mock(),
            refresh_profiles_dropdown=Mock(),
            refresh_profile_info=Mock(),
            update_export_preview=Mock(),
            status=SimpleNamespace(set=Mock()),
        )
        window = SimpleNamespace(destroy=Mock())
        controller = FakeSettingsController()
        shell = SimpleNamespace(controllers={"appearance": controller})

        with patch("cheat_editor_manager.ui.dialogs.settings_dialog.save_prefs") as save:
            _apply_settings_and_close(app, window, shell)

        controller.save_to_prefs.assert_called_once()
        save.assert_called_once_with(app.prefs)
        app.apply_theme.assert_called_once()
        app._sync_core_dropdown.assert_called_once()
        app.refresh_profiles_dropdown.assert_called_once()
        app.refresh_profile_info.assert_called_once()
        app.update_export_preview.assert_called_once()
        app.status.set.assert_called_once_with("Settings saved.")
        window.destroy.assert_called_once()


if __name__ == "__main__":
    unittest.main()
