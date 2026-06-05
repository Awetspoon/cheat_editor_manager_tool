from __future__ import annotations

import unittest
from unittest.mock import patch

from cheat_editor_manager.app_actions import RetroarchCoreActionsMixin


class DummyRetroarchApp(RetroarchCoreActionsMixin):
    def __init__(self, prefs: dict):
        self.prefs = prefs
        self.startup_warnings: list[str] = []

    def _record_startup_warning(self, message: str) -> None:
        self.startup_warnings.append(message)


class RetroarchCoreActionTests(unittest.TestCase):
    def test_audit_does_not_save_when_preferences_are_already_clean(self):
        app = DummyRetroarchApp(
            {
                "retroarch_cores": ["Default (no subfolder)", "mGBA"],
                "retroarch_core": "mGBA",
            }
        )

        with patch("cheat_editor_manager.app_actions.save_prefs") as save_mock:
            app._audit_retroarch_cores()

        save_mock.assert_not_called()
        self.assertEqual(app.startup_warnings, [])

    def test_audit_records_warning_when_required_save_fails(self):
        app = DummyRetroarchApp(
            {
                "retroarch_cores": ["mGBA", "mGBA"],
                "retroarch_core": "Missing",
            }
        )

        with patch(
            "cheat_editor_manager.app_actions.save_prefs",
            side_effect=PermissionError("blocked"),
        ):
            app._audit_retroarch_cores()

        self.assertEqual(app.prefs["retroarch_core"], "Default (no subfolder)")
        self.assertEqual(
            app.prefs["retroarch_cores"], ["Default (no subfolder)", "mGBA"]
        )
        self.assertEqual(len(app.startup_warnings), 1)
        self.assertIn("could not be saved", app.startup_warnings[0])


if __name__ == "__main__":
    unittest.main()
