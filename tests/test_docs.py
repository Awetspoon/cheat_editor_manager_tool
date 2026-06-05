from pathlib import Path
import re
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class DocumentationTests(unittest.TestCase):
    def test_readme_documents_current_ui_and_expansion_points(self):
        readme = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")

        self.assertIn("## Main UI Sections", readme)
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
            self.assertNotIn(removed_reference, readme)

    def test_main_documentation_links_point_to_existing_files(self):
        readme = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")
        links = re.findall(r"\[[^\]]+\]\(([^)]+)\)", readme)

        for target in links:
            if target.startswith(("http://", "https://", "#")):
                continue
            with self.subTest(target=target):
                self.assertTrue((PROJECT_ROOT / target).exists())


if __name__ == "__main__":
    unittest.main()
