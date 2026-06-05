from __future__ import annotations

import unittest

from cheat_editor_manager.services import retroarch_core_service


class RetroarchCoreServiceTests(unittest.TestCase):
    def test_normalize_core_name_smooths_spacing_and_separators(self):
        self.assertEqual(
            retroarch_core_service.normalize_core_name("Beetle-PSX_HW"),
            "beetle psx hw",
        )

    def test_ensure_core_preferences_dedupes_and_resets_missing_current(self):
        prefs = {
            "retroarch_cores": [
                " mGBA ",
                "",
                "mgba",
                "Default (no subfolder)",
                "Snes9x",
            ],
            "retroarch_core": "MissingCore",
        }

        cores, current = retroarch_core_service.ensure_core_preferences(prefs)

        self.assertEqual(
            cores,
            ["Default (no subfolder)", "mGBA", "Snes9x"],
        )
        self.assertEqual(current, "Default (no subfolder)")
        self.assertEqual(prefs["retroarch_core"], "Default (no subfolder)")

    def test_rename_core_updates_current_core_when_selected(self):
        prefs = {
            "retroarch_cores": ["Default (no subfolder)", "mGBA"],
            "retroarch_core": "mGBA",
        }

        cores, current = retroarch_core_service.rename_core(prefs, "mGBA", "SameBoy")

        self.assertEqual(cores, ["Default (no subfolder)", "SameBoy"])
        self.assertEqual(current, "SameBoy")

    def test_remove_current_core_resets_to_default(self):
        prefs = {
            "retroarch_cores": ["Default (no subfolder)", "mGBA", "Snes9x"],
            "retroarch_core": "mGBA",
        }

        cores, current = retroarch_core_service.remove_core(prefs, "mGBA")

        self.assertEqual(cores, ["Default (no subfolder)", "Snes9x"])
        self.assertEqual(current, "Default (no subfolder)")


if __name__ == "__main__":
    unittest.main()
