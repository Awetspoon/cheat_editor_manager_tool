from pathlib import Path
import re
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class DocumentationTests(unittest.TestCase):
    def test_readme_documents_current_ui_and_expansion_points(self):
        readme = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")

        self.assertIn("## Main UI Sections", readme)
        self.assertIn("## Purpose And Scope", readme)
        self.assertIn("## Finished App Requirements", readme)
        self.assertIn("## User Flow", readme)
        self.assertIn("## Screen Map", readme)
        self.assertIn("## Feature List", readme)
        self.assertIn("## Future Expansion Points", readme)
        self.assertIn("assets/README.md", readme)

    def test_readme_does_not_link_removed_internal_cleanup_files(self):
        readme = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")

        for removed_reference in (
            "docs/README.md",
            "docs/REDESIGN_PLAN.md",
            "docs/redesign-concept.png",
            "CLEANUP_PHASE_LOG.md",
            "scripts/check_dev_environment.py",
        ):
            with self.subTest(removed_reference=removed_reference):
                self.assertNotIn(removed_reference, readme)

    def test_main_documentation_links_point_to_existing_files(self):
        readme = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")
        linked_paths = re.findall(r"\[[^\]]+\]\((?!https?://|#)([^)]+)\)", readme)

        for relative_path in linked_paths:
            if relative_path.startswith("mailto:"):
                continue
            with self.subTest(relative_path=relative_path):
                self.assertTrue((PROJECT_ROOT / relative_path).exists())
