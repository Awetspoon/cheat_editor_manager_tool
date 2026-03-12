import unittest

from cheat_editor_manager import APP_NAME, APP_VERSION, configure_tcl_environment
from cheat_editor_manager.app import App
from cheat_editor_manager.services import theme_service


class AppSmokeTests(unittest.TestCase):
    def test_imports_and_theme_helpers_are_available(self):
        self.assertTrue(APP_NAME)
        self.assertTrue(APP_VERSION)
        configure_tcl_environment()
        self.assertGreater(App._contrast_ratio("#ffffff", "#000000"), 10)
        self.assertEqual(theme_service.normalize_hex_color("#ABCDEF"), "#abcdef")
