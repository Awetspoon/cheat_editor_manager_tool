import os
from pathlib import Path
from tempfile import TemporaryDirectory
import tkinter as tk
from tkinter import ttk
import unittest
from unittest.mock import patch

from cheat_editor_manager.app import App
from cheat_editor_manager.ui.widgets import AutoScrollbar


def _find_child(widget, widget_type):
    if isinstance(widget, widget_type):
        return widget
    for child in widget.winfo_children():
        found = _find_child(child, widget_type)
        if found is not None:
            return found
    return None


def _find_listbox_with_items(widget, expected_items):
    if isinstance(widget, tk.Listbox):
        items = [widget.get(index) for index in range(widget.size())]
        if items == expected_items:
            return widget
    for child in widget.winfo_children():
        found = _find_listbox_with_items(child, expected_items)
        if found is not None:
            return found
    return None


class UiWorkflowSmokeTests(unittest.TestCase):
    def setUp(self):
        if os.environ.get("CHEAT_EDITOR_MANAGER_SKIP_GUI_SMOKE") == "1":
            self.skipTest("GUI workflow smoke tests disabled by environment")
        self.app = App()
        self.app.root.update_idletasks()
        self.app.root.update()

    def tearDown(self):
        preview_after = getattr(self.app, "_preview_after", None)
        if preview_after:
            try:
                self.app.root.after_cancel(preview_after)
            except Exception:
                pass
        try:
            self.app.root.destroy()
        except Exception:
            pass

    def test_load_file_uses_file_picker_when_no_path_is_supplied(self):
        with patch(
            "cheat_editor_manager.services.file_load_service.filedialog.askopenfilename",
            return_value="",
        ) as askopenfilename:
            self.app.load_file()

        askopenfilename.assert_called_once()

    def test_editor_accepts_text_and_profile_refresh_updates_preview(self):
        self.app.profile_var.set("PCSX2 (PS2) - PC")
        self.app.tid_var.set("1A2B3C4D")
        self.app.editor.delete("1.0", "end")
        self.app.editor.insert("1.0", "patch=1,EE,00112233,extended,00000001")

        self.app.refresh_profile_info()
        self.app.update_export_preview()

        self.assertIn("00112233", self.app.editor.get("1.0", "end"))
        self.assertIn("PCSX2", self.app.helper_text.get())
        self.assertIn("1A2B3C4D", self.app.path_preview.get())

    def test_main_window_uses_three_zone_workspace_layout(self):
        self.assertTrue(hasattr(self.app, "left_sidebar"))
        self.assertTrue(hasattr(self.app, "editor_workspace"))
        self.assertTrue(hasattr(self.app, "right_sidebar"))
        self.assertIs(self.app.profile_panel.master, self.app.left_sidebar)
        self.assertIs(self.app.editor_panel.master, self.app.editor_workspace)
        self.assertIs(self.app.helper.master, self.app.right_sidebar)
        self.assertFalse(hasattr(self.app, "profile_sort_btn"))
        self.assertFalse(hasattr(self.app, "open_profile_sort_menu"))
        self.assertLessEqual(
            int(float(self.app.info_label.cget("wraplength"))),
            self.app.info_label.winfo_width(),
        )

    def test_editor_scrollbars_only_show_when_content_overflows(self):
        scrollbars = [
            child
            for child in self.app.editor_frame.winfo_children()
            if isinstance(child, AutoScrollbar)
        ]
        scrollbar_by_orientation = {
            str(scrollbar.cget("orient")): scrollbar for scrollbar in scrollbars
        }

        self.assertFalse(scrollbar_by_orientation["vertical"].winfo_ismapped())
        self.assertFalse(scrollbar_by_orientation["horizontal"].winfo_ismapped())

        self.app.editor.insert("1.0", "\n".join(f"line {index}" for index in range(200)))
        self.app.root.update_idletasks()
        self.app.root.update()

        self.assertTrue(scrollbar_by_orientation["vertical"].winfo_ismapped())
        self.assertFalse(scrollbar_by_orientation["horizontal"].winfo_ismapped())

        self.app.editor.configure(wrap="none")
        self.app.editor.insert("1.0", "x" * 1000)
        self.app.root.update_idletasks()
        self.app.root.update()

        self.assertTrue(scrollbar_by_orientation["horizontal"].winfo_ismapped())

    def test_quick_export_validates_required_fields_before_writing(self):
        self.app.profile_var.set("Atmosphere (Switch) (CFW)")
        self.app.tid_var.set("")
        self.app.bid_var.set("")
        self.app.editor.delete("1.0", "end")
        self.app.editor.insert("1.0", "[Infinite HP]\n04000000 00000000 00000001")

        with patch(
            "cheat_editor_manager.services.export_service.messagebox.showerror"
        ) as showerror:
            self.app.quick_export()

        showerror.assert_called_once()
        self.assertIn("TitleID", showerror.call_args.args[1])

    def test_convert_save_uses_save_dialog_and_writes_selected_file(self):
        self.app.profile_var.set("Atmosphere (Switch) (CFW)")
        self.app.editor.delete("1.0", "end")
        self.app.editor.insert("1.0", "[Infinite HP]\n04000000 00000000 00000001")

        with TemporaryDirectory() as temp_dir:
            save_path = Path(temp_dir) / "cheat.txt"
            with patch.object(self.app, "_pick_extension_for_save", return_value=".txt"):
                with patch(
                    "cheat_editor_manager.services.export_service.filedialog.asksaveasfilename",
                    return_value=str(save_path),
                ) as asksaveasfilename:
                    self.app.convert_save()

            asksaveasfilename.assert_called_once()
            self.assertIn("Infinite HP", save_path.read_text(encoding="utf-8"))
            self.assertIn("Saved:", self.app.status.get())

    def test_settings_dialog_contains_expected_sections(self):
        self.app.open_settings()
        self.app.root.update_idletasks()
        self.app.root.update()

        settings_windows = [
            child
            for child in self.app.root.winfo_children()
            if isinstance(child, tk.Toplevel) and child.winfo_exists()
        ]
        self.assertTrue(settings_windows)

        settings_window = settings_windows[-1]
        self.assertIsNone(_find_child(settings_window, ttk.Notebook))
        nav = _find_listbox_with_items(
            settings_window,
            ["Profiles", "Appearance", "Export Roots"],
        )
        self.assertIsNotNone(nav)
        settings_window.destroy()


if __name__ == "__main__":
    unittest.main()
