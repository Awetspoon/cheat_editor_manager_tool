import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from cheat_editor_manager.constants import DEFAULT_PROFILES, DEFAULT_RETROARCH_CORES
from cheat_editor_manager.profiles import PROFILE_GROUP_CFW, PROFILE_GROUP_PC
from cheat_editor_manager.services.file_load_service import load_file_into_app


class FakeVar:
    def __init__(self, value=""):
        self.value = value

    def get(self):
        return self.value

    def set(self, value):
        self.value = value


class FakeEditor:
    def __init__(self):
        self.text = ""

    def delete(self, _start, _end):
        self.text = ""

    def insert(self, _index, text):
        self.text = text


class FakeCombobox:
    def __init__(self):
        self.value = ""

    def set(self, value):
        self.value = value


class FakeApp:
    def __init__(self):
        self.editor = FakeEditor()
        self.status = FakeVar()
        self.tid_var = FakeVar()
        self.bid_var = FakeVar()
        self.profile_var = FakeVar()
        self.profile_group_var = FakeVar()
        self.core_var = FakeVar()
        self.profile_cb = FakeCombobox()
        self.prefs = {"retroarch_cores": list(DEFAULT_RETROARCH_CORES)}
        self.core_visible = False
        self.refresh_count = 0

    def get_profile_values(self):
        return list(DEFAULT_PROFILES)

    def get_profile_info(self, profile_name):
        return DEFAULT_PROFILES.get(profile_name, {"kind": "generic"})

    def _show_core(self, show):
        self.core_visible = show

    def refresh_profile_info(self):
        self.refresh_count += 1


class FileLoadServiceTests(unittest.TestCase):
    def write_file(self, root: Path, relative_path: str, text: str) -> Path:
        path = root / Path(relative_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def test_loads_atmosphere_layout_and_detects_switch_ids(self):
        with TemporaryDirectory() as tmp:
            path = self.write_file(
                Path(tmp),
                "atmosphere/contents/0100AABBCCDDEEFF/cheats/AABBCCDDEEFF0011.txt",
                "[Infinite HP]\n04000000 00000000 00000063\n",
            )
            app = FakeApp()

            load_file_into_app(app, str(path))

            self.assertIn("Infinite HP", app.editor.text)
            self.assertEqual(app.tid_var.get(), "0100AABBCCDDEEFF")
            self.assertEqual(app.bid_var.get(), "AABBCCDDEEFF0011")
            self.assertEqual(app.profile_var.get(), "Atmosphere (Switch) (CFW)")
            self.assertEqual(app.profile_group_var.get(), PROFILE_GROUP_CFW)
            self.assertEqual(app.profile_cb.value, "Atmosphere (Switch) (CFW)")
            self.assertEqual(app.refresh_count, 1)

    def test_loads_retroarch_core_folder_without_mutating_core_list(self):
        with TemporaryDirectory() as tmp:
            path = self.write_file(
                Path(tmp),
                "RetroArch/cheats/mGBA/Example Game.cht",
                "cheat0_desc = Infinite HP\n",
            )
            app = FakeApp()
            original_cores = list(app.prefs["retroarch_cores"])

            load_file_into_app(app, str(path))

            self.assertEqual(app.profile_var.get(), "RetroArch (Multi-platform)")
            self.assertEqual(app.profile_group_var.get(), PROFILE_GROUP_PC)
            self.assertEqual(app.core_var.get(), "mGBA")
            self.assertTrue(app.core_visible)
            self.assertEqual(app.prefs["retroarch_cores"], original_cores)
            self.assertIn("Detected RetroArch core: mGBA", app.status.get())

    def test_loads_citra_retroarch_save_layout(self):
        with TemporaryDirectory() as tmp:
            path = self.write_file(
                Path(tmp),
                "RetroArch/saves/Citra/cheats/000400000FF40A00.txt",
                "*citra_enabled\n[Infinite HP]\n",
            )
            app = FakeApp()

            load_file_into_app(app, str(path))

            self.assertEqual(app.tid_var.get(), "000400000FF40A00")
            self.assertEqual(app.profile_var.get(), "Citra (3DS) - PC")
            self.assertEqual(app.profile_group_var.get(), PROFILE_GROUP_PC)
            self.assertEqual(app.profile_cb.value, "Citra (3DS) - PC")

    def test_loads_pcsx2_pnach_and_normalizes_crc(self):
        with TemporaryDirectory() as tmp:
            path = self.write_file(
                Path(tmp),
                "PCSX2/Cheats/1a2b3c4d.pnach",
                "patch=1,EE,00000000,word,00000001\n",
            )
            app = FakeApp()

            load_file_into_app(app, str(path))

            self.assertEqual(app.profile_var.get(), "PCSX2 (PS2) - PC")
            self.assertEqual(app.profile_group_var.get(), PROFILE_GROUP_PC)
            self.assertEqual(app.tid_var.get(), "1A2B3C4D")


if __name__ == "__main__":
    unittest.main()
