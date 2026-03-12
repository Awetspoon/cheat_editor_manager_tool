import unittest
from pathlib import Path

from cheat_editor_manager.export_logic import (
    build_export_plan,
    clean_hex,
    derive_cheat_name,
    extract_switch_metadata,
    normalize_bids,
    prepare_export_text,
    split_bids,
    validate_export_inputs,
)


class ExportLogicTests(unittest.TestCase):
    def test_clean_hex_and_split_bids(self):
        self.assertEqual(clean_hex(" aa-bb "), "AABB")
        self.assertEqual(split_bids("abc, def\n123"), ["abc", "def", "123"])

    def test_normalize_bids_dedupes_and_filters_invalid_values(self):
        self.assertEqual(
            normalize_bids("AABBCCDDEEFF0011, aabbccddeeff0011, bad, 11223344556677889900AABBCCDDEEFF"),
            ["AABBCCDDEEFF0011", "11223344556677889900AABBCCDDEEFF"],
        )

    def test_extract_switch_metadata_reads_multiple_bids(self):
        meta = extract_switch_metadata(
            """
            TitleID: 0100AABBCCDDEEFF
            BuildIDs: AABBCCDDEEFF0011, 11223344556677889900AABBCCDDEEFF
            BID: AABBCCDDEEFF0011
            """
        )
        self.assertEqual(meta["tid"], "0100AABBCCDDEEFF")
        self.assertEqual(
            meta["bids"],
            ["AABBCCDDEEFF0011", "11223344556677889900AABBCCDDEEFF"],
        )

    def test_extract_switch_metadata_reads_tid_from_packed_header_line(self):
        meta = extract_switch_metadata(
            "TitleID: 0100AABBCCDDEEFF BuildID: AABBCCDDEEFF0011\n[Infinite HP]\n04000000 00000000 00000063\n"
        )
        self.assertEqual(meta["tid"], "0100AABBCCDDEEFF")
        self.assertEqual(meta["bids"], ["AABBCCDDEEFF0011"])

    def test_validate_switch_inputs(self):
        info = {"kind": "switch"}
        self.assertIsNone(validate_export_inputs(info, "0100AABBCCDDEEFF", "AABBCCDDEEFF0011"))
        self.assertIn("TitleID", validate_export_inputs(info, "bad", "AABBCCDDEEFF0011"))
        self.assertIn("BuildID", validate_export_inputs(info, "0100AABBCCDDEEFF", "bad-bid"))

    def test_validate_atmosphere_text_requires_real_cheat_content(self):
        info = {
            "kind": "switch",
            "subdir": "atmosphere/contents/<TID>/cheats",
        }
        self.assertIn(
            "requires cheat text",
            validate_export_inputs(info, "0100AABBCCDDEEFF", "AABBCCDDEEFF0011", editor_text="\n\n# comment\n"),
        )
        self.assertIsNone(
            validate_export_inputs(
                info,
                "0100AABBCCDDEEFF",
                "AABBCCDDEEFF0011",
                editor_text="[Infinite HP]\n04000000 00000000 00000063\n",
            )
        )

    def test_validate_titleid_inputs(self):
        info = {"kind": "titleid"}
        self.assertIsNone(validate_export_inputs(info, "000400000FF40A00", ""))
        self.assertIn("TitleID", validate_export_inputs(info, "bad", ""))

    def test_prepare_export_text_adds_citra_enabled_marker_once(self):
        info = {"kind": "titleid", "citra_enabled": True}
        prepared = prepare_export_text(info, "[Infinite HP]\n*cheat line\n")
        self.assertTrue(prepared.startswith("*citra_enabled\n\n"))
        self.assertEqual(prepared.count("*citra_enabled"), 1)
        already = prepare_export_text(info, "*citra_enabled\n[Infinite HP]\n")
        self.assertEqual(already.count("*citra_enabled"), 1)


    def test_validate_idfile_inputs(self):
        dolphin = {
            "kind": "idfile",
            "id_label": "Game ID:",
            "id_regex": "^[A-Z0-9]{6}$",
            "id_placeholder": "<GameID>",
            "id_uppercase": True,
        }
        pcsx2 = {
            "kind": "idfile",
            "id_label": "CRC:",
            "id_regex": "^[0-9A-F]{8}$",
            "id_placeholder": "<CRC>",
            "id_normalization": "hex",
            "id_error": "This Quick Export requires an 8-character CRC.",
        }
        self.assertIsNone(validate_export_inputs(dolphin, "gzle01", ""))
        self.assertIn("CRC", validate_export_inputs(pcsx2, "bad", ""))

    def test_build_export_plan_sanitizes_user_visible_fragments(self):
        info = {
            "kind": "retroarch",
            "subdir": "RetroArch/cheats/<Core Name>",
            "filename_hint": "<Game>",
            "extensions": [".cht"],
        }
        plan = build_export_plan(
            prof="RetroArch",
            info=info,
            root=Path("C:/Exports"),
            tid="",
            bid_text="",
            core="mGBA/core",
            editor_text="# Sample Cheat\n01234567 89ABCDEF\n",
        )
        self.assertEqual(plan["files"], [Path("C:/Exports/RetroArch/cheats/mGBA_core/Sample Cheat.cht")])

    def test_build_export_plan_supports_multiple_switch_bids(self):
        info = {
            "kind": "switch",
            "subdir": "atmosphere/contents/<TID>/cheats",
            "filename_hint": "<BID>",
            "extensions": [".txt"],
        }
        plan = build_export_plan(
            prof="Atmosphere",
            info=info,
            root=Path("C:/Exports"),
            tid="0100AABBCCDDEEFF",
            bid_text="AABBCCDDEEFF0011,11223344556677889900AABBCCDDEEFF",
            core="",
            editor_text="# Cheat\n",
        )
        self.assertEqual(
            plan["files"],
            [
                Path("C:/Exports/atmosphere/contents/0100AABBCCDDEEFF/cheats/AABBCCDDEEFF0011.txt"),
                Path("C:/Exports/atmosphere/contents/0100AABBCCDDEEFF/cheats/11223344556677889900AABBCCDDEEFF.txt"),
            ],
        )

    def test_build_export_plan_dedupes_duplicate_switch_bids(self):
        info = {
            "kind": "switch",
            "subdir": "atmosphere/contents/<TID>/cheats",
            "filename_hint": "<BID>",
            "extensions": [".txt"],
        }
        plan = build_export_plan(
            prof="Atmosphere",
            info=info,
            root=Path("C:/Exports"),
            tid="0100AABBCCDDEEFF",
            bid_text="AABBCCDDEEFF0011, aabbccddeeff0011",
            core="",
            editor_text="# Cheat\n",
        )
        self.assertEqual(
            plan["files"],
            [Path("C:/Exports/atmosphere/contents/0100AABBCCDDEEFF/cheats/AABBCCDDEEFF0011.txt")],
        )

    def test_build_export_plan_supports_titleid_filename_layout(self):
        info = {
            "kind": "titleid",
            "subdir": "RetroArch/saves/Citra/cheats",
            "filename_hint": "<TitleID>",
            "extensions": [".txt"],
        }
        plan = build_export_plan(
            prof="Citra (3DS) - PC",
            info=info,
            root=Path("C:/Exports"),
            tid="000400000FF40A00",
            bid_text="",
            core="",
            editor_text="[Infinite HP]\n",
        )
        self.assertEqual(plan["files"], [Path("C:/Exports/RetroArch/saves/Citra/cheats/000400000FF40A00.txt")])

    def test_build_export_plan_supports_titleid_fixed_filename_layout(self):
        info = {
            "kind": "titleid",
            "subdir": "luma/plugins/<TitleID>",
            "filename_hint": "<TitleID>",
            "fixed_filename": "cheats.txt",
            "extensions": [".txt"],
        }
        plan = build_export_plan(
            prof="Nintendo 3DS (CFW) (Luma)",
            info=info,
            root=Path("C:/Exports"),
            tid="000400000FF40A00",
            bid_text="",
            core="",
            editor_text="[Infinite HP]\n",
        )
        self.assertEqual(plan["files"], [Path("C:/Exports/luma/plugins/000400000FF40A00/cheats.txt")])


    def test_build_export_plan_supports_dolphin_game_id_layout(self):
        info = {
            "kind": "idfile",
            "subdir": "Dolphin Emulator/GameSettings",
            "filename_hint": "<GameID>",
            "extensions": [".ini"],
            "id_placeholder": "<GameID>",
            "id_uppercase": True,
        }
        plan = build_export_plan(
            prof="Dolphin (GC/Wii) - PC",
            info=info,
            root=Path("C:/Exports"),
            tid="gzle01",
            bid_text="",
            core="",
            editor_text="# Infinite HP\n",
        )
        self.assertEqual(plan["files"], [Path("C:/Exports/Dolphin Emulator/GameSettings/GZLE01.ini")])

    def test_build_export_plan_supports_pcsx2_crc_layout(self):
        info = {
            "kind": "idfile",
            "subdir": "PCSX2/Cheats",
            "filename_hint": "<CRC>",
            "extensions": [".pnach"],
            "id_placeholder": "<CRC>",
            "id_normalization": "hex",
        }
        plan = build_export_plan(
            prof="PCSX2 (PS2) - PC",
            info=info,
            root=Path("C:/Exports"),
            tid="1a2b3c4d",
            bid_text="",
            core="",
            editor_text="# Infinite HP\n",
        )
        self.assertEqual(plan["files"], [Path("C:/Exports/PCSX2/Cheats/1A2B3C4D.pnach")])

    def test_build_export_plan_supports_duckstation_serial_layout(self):
        info = {
            "kind": "idfile",
            "subdir": "DuckStation/cheats",
            "filename_hint": "<SERIAL>",
            "extensions": [".cht"],
            "id_placeholder": "<SERIAL>",
            "id_uppercase": True,
        }
        plan = build_export_plan(
            prof="DuckStation (PS1) - PC",
            info=info,
            root=Path("C:/Exports"),
            tid="slus-01041",
            bid_text="",
            core="",
            editor_text="# Infinite HP\n",
        )
        self.assertEqual(plan["files"], [Path("C:/Exports/DuckStation/cheats/SLUS-01041.cht")])

    def test_build_export_plan_supports_xenia_titleid_layout(self):
        info = {
            "kind": "idfile",
            "subdir": "Xenia/patches",
            "filename_hint": "<TitleID>",
            "extensions": [".patch.toml"],
            "id_placeholder": "<TitleID>",
            "id_normalization": "hex",
        }
        plan = build_export_plan(
            prof="Xenia (Xbox 360) - PC",
            info=info,
            root=Path("C:/Exports"),
            tid="58410a5b",
            bid_text="",
            core="",
            editor_text="# Infinite HP\n",
        )
        self.assertEqual(plan["files"], [Path("C:/Exports/Xenia/patches/58410A5B.patch.toml")])

    def test_build_export_plan_supports_wii_homebrew_layout(self):
        info = {
            "kind": "idfile",
            "subdir": "Wii/codes",
            "filename_hint": "<GameID>",
            "extensions": [".gct"],
            "id_placeholder": "<GameID>",
            "id_uppercase": True,
        }
        plan = build_export_plan(
            prof="Wii (Homebrew)",
            info=info,
            root=Path("C:/Exports"),
            tid="rmge01",
            bid_text="",
            core="",
            editor_text="# Infinite HP\n",
        )
        self.assertEqual(plan["files"], [Path("C:/Exports/Wii/codes/RMGE01.gct")])

    def test_build_export_plan_supports_wii_u_cfw_layout(self):
        info = {
            "kind": "idfile",
            "subdir": "wiiu/codes",
            "filename_hint": "<WiiUTitleID>",
            "extensions": [".txt"],
            "id_placeholder": "<WiiUTitleID>",
            "id_normalization": "hex",
        }
        plan = build_export_plan(
            prof="Wii U (CFW)",
            info=info,
            root=Path("C:/Exports"),
            tid="0005000010101c00",
            bid_text="",
            core="",
            editor_text="# Infinite HP\n",
        )
        self.assertEqual(plan["files"], [Path("C:/Exports/wiiu/codes/0005000010101C00.txt")])

    def test_derive_cheat_name_prefers_heading(self):
        self.assertEqual(derive_cheat_name("# Infinite HP\ncode"), "Infinite HP")


if __name__ == "__main__":
    unittest.main()


