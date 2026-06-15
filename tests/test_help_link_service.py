from __future__ import annotations

import unittest

from cheat_editor_manager.services import help_link_service


class HelpLinkServiceTests(unittest.TestCase):
    def test_normalize_links_trims_values_and_drops_empty_entries(self):
        links = [
            {"name": " Docs ", "url": " https://example.com "},
            {"name": "GameHacking", "url": "gamehacking.org"},
            {"name": "", "url": ""},
            {"url": "https://fallback.example"},
        ]

        self.assertEqual(
            help_link_service.normalize_links(links),
            [
                {"name": "Docs", "url": "https://example.com"},
                {"name": "GameHacking", "url": "https://gamehacking.org"},
                {"name": "", "url": "https://fallback.example"},
            ],
        )

    def test_display_name_prefers_name_then_url(self):
        self.assertEqual(
            help_link_service.display_name(
                {"name": "GameHacking", "url": "https://gamehacking.org"}
            ),
            "GameHacking",
        )
        self.assertEqual(
            help_link_service.display_name({"name": "", "url": "https://docs.test"}),
            "https://docs.test",
        )

    def test_add_replace_and_delete_return_new_clean_lists(self):
        original = [{"name": "One", "url": "https://one.test"}]

        added = help_link_service.add_link(
            original, {"name": " Two ", "url": " https://two.test "}
        )
        replaced = help_link_service.replace_link(
            added, 0, {"name": "Updated", "url": "https://updated.test"}
        )
        deleted = help_link_service.delete_link(replaced, 1)

        self.assertEqual(original, [{"name": "One", "url": "https://one.test"}])
        self.assertEqual(
            deleted, [{"name": "Updated", "url": "https://updated.test"}]
        )

    def test_duplicate_url_index_finds_matching_saved_source(self):
        links = [
            {"name": "One", "url": "https://one.test"},
            {"name": "Two", "url": "two.test"},
        ]

        self.assertEqual(
            help_link_service.duplicate_url_index(links, "https://two.test"),
            1,
        )
        self.assertIsNone(
            help_link_service.duplicate_url_index(
                links,
                "https://two.test",
                ignore_index=1,
            )
        )

    def test_default_links_returns_a_copy(self):
        first = help_link_service.default_links()
        second = help_link_service.default_links()
        first.pop()

        self.assertNotEqual(len(first), len(second))
        self.assertTrue(second)

    def test_merge_default_links_keeps_custom_links_and_adds_missing_defaults(self):
        custom_link = {"name": "Custom", "url": "https://custom.example"}
        first_default = help_link_service.default_links()[0]

        merged = help_link_service.merge_default_links([custom_link, first_default])

        self.assertEqual(merged[0], custom_link)
        self.assertEqual(merged.count(first_default), 1)
        self.assertGreater(len(merged), 2)


if __name__ == "__main__":
    unittest.main()
