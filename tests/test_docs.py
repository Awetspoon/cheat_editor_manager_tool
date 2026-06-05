from pathlib import Path
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class DocumentationTests(unittest.TestCase):
    def test_readme_documents_current_ui_and_expansion_points(self):
        readme = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")

        self.assertIn("## Main UI Sections", readme)
        self.assertIn("## Future Expansion Points", readme)
        self.assertIn("docs/README.md", readme)

    def test_docs_index_labels_archived_explanation(self):
        docs_readme = (PROJECT_ROOT / "docs" / "README.md").read_text(encoding="utf-8")

        self.assertIn("Current Docs", docs_readme)
        self.assertIn("Archived Docs", docs_readme)
        self.assertIn("Cheat_File_Creator_MASTER_EXPLANATION_v1_3_2.txt", docs_readme)

    def test_archived_explanation_has_clear_warning(self):
        archived_doc = (
            PROJECT_ROOT / "docs" / "Cheat_File_Creator_MASTER_EXPLANATION_v1_3_2.txt"
        ).read_text(encoding="utf-8")

        self.assertTrue(archived_doc.startswith("ARCHIVED DOCUMENT - NOT CURRENT PRODUCT DOCUMENTATION"))

    def test_main_documentation_links_point_to_existing_files(self):
        for relative_path in [
            "docs/README.md",
            "docs/REDESIGN_PLAN.md",
            "assets/README.md",
            "CLEANUP_PHASE_LOG.md",
        ]:
            with self.subTest(relative_path=relative_path):
                self.assertTrue((PROJECT_ROOT / relative_path).exists())
