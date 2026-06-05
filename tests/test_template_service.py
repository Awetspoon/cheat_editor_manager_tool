from __future__ import annotations

import unittest

from cheat_editor_manager.services.template_service import build_helper_snippet


class TemplateServiceTests(unittest.TestCase):
    def test_switch_helper_snippet_mentions_title_and_build_ids(self):
        snippet = build_helper_snippet({"kind": "switch"})

        self.assertIn("TitleID", snippet)
        self.assertIn("BuildID", snippet)
        self.assertIn("<TID>", snippet)
        self.assertIn("<BID>", snippet)

    def test_citra_titleid_snippet_includes_required_marker(self):
        snippet = build_helper_snippet(
            {"kind": "titleid", "id_label": "TitleID", "citra_enabled": True}
        )

        self.assertIn("TitleID", snippet)
        self.assertIn("*citra_enabled", snippet)

    def test_retroarch_snippet_mentions_core_folder(self):
        snippet = build_helper_snippet({"kind": "retroarch"})

        self.assertIn("RetroArch", snippet)
        self.assertIn("<Core Name>", snippet)


if __name__ == "__main__":
    unittest.main()
