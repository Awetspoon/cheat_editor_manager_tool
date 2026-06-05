import unittest
import inspect

from cheat_editor_manager.app import App
from cheat_editor_manager.resources import asset_path


class AssetTests(unittest.TestCase):
    def test_runtime_assets_exist(self):
        for name in ("app-icon.ico", "app-icon.png", "icon-256.png", "mark-48.png"):
            self.assertTrue(asset_path(name).exists(), name)

    def test_readme_screenshot_exists(self):
        self.assertTrue(asset_path("app-fullscreen.png").exists())

    def test_temporary_preview_assets_are_not_kept_as_runtime_assets(self):
        assets_dir = asset_path("app-icon.ico").parent
        for name in (
            "exe-icon-preview.png",
            "runtime-window-icon.png",
            "source-icon-preview.png",
        ):
            self.assertFalse((assets_dir / name).exists(), name)

    def test_internal_redesign_concept_is_not_kept_as_runtime_asset(self):
        project_root = asset_path("app-icon.ico").parent.parent
        self.assertFalse((project_root / "docs" / "redesign-concept.png").exists())
        self.assertFalse((project_root / "assets" / "redesign-concept.png").exists())

    def test_runtime_header_uses_one_compact_mark(self):
        load_source = inspect.getsource(App._load_brand_assets)
        apply_source = inspect.getsource(App._apply_brand_images)
        combined_source = load_source + apply_source

        self.assertIn("mark-48.png", combined_source)
        for forbidden_name in (
            "wordmark-360.png",
            "logo-header.png",
            "watermark-ui.png",
            "watermark.png",
            "watermark-brand.png",
        ):
            self.assertNotIn(forbidden_name, combined_source)


if __name__ == "__main__":
    unittest.main()

