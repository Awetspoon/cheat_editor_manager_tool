import os
from pathlib import Path
from tempfile import TemporaryDirectory
import tkinter as tk
from tkinter import ttk
import unittest
from unittest.mock import patch

from cheat_editor_manager.profiles import PROFILE_GROUP_CFW, PROFILE_GROUP_PC
from cheat_editor_manager.ui.widgets import AutoScrollbar
from tests.gui_test_utils import create_test_app, destroy_root


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


def _collect_widgets(widget, widget_type):
    found = []
    if isinstance(widget, widget_type):
        found.append(widget)
    for child in widget.winfo_children():
        found.extend(_collect_widgets(child, widget_type))
    return found


def _find_widget_with_text(widget, widget_type, text):
    for candidate in _collect_widgets(widget, widget_type):
        try:
            if candidate.cget("text") == text:
                return candidate
        except Exception:
            pass
    return None


class UiWorkflowSmokeTests(unittest.TestCase):
    def setUp(self):
        if os.environ.get("CHEAT_EDITOR_MANAGER_SKIP_GUI_SMOKE") == "1":
            self.skipTest("GUI workflow smoke tests disabled by environment")
        self.app = create_test_app()

    def tearDown(self):
        preview_after = getattr(self.app, "_preview_after", None)
        if preview_after:
            try:
                self.app.root.after_cancel(preview_after)
            except Exception:
                pass
        destroy_root(getattr(self.app, "root", None))

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

    def test_profile_selector_splits_group_and_target_without_fake_rows(self):
        self.assertTrue(hasattr(self.app, "profile_group_cb"))
        self.assertTrue(hasattr(self.app, "profile_cb"))

        groups = list(self.app.profile_group_cb.cget("values"))
        self.assertIn(PROFILE_GROUP_CFW, groups)
        self.assertIn(PROFILE_GROUP_PC, groups)
        self.assertEqual(self.app.profile_group_var.get(), PROFILE_GROUP_CFW)

        cfw_targets = list(self.app.profile_cb.cget("values"))
        self.assertIn("Atmosphere (Switch) (CFW)", cfw_targets)
        self.assertNotIn("PCSX2 (PS2) - PC", cfw_targets)

        self.app.profile_group_var.set(PROFILE_GROUP_PC)
        self.app.profile_group_cb.event_generate("<<ComboboxSelected>>")
        self.app.root.update_idletasks()
        self.app.root.update()

        pc_targets = list(self.app.profile_cb.cget("values"))
        self.assertIn("PCSX2 (PS2) - PC", pc_targets)
        self.assertNotIn("Atmosphere (Switch) (CFW)", pc_targets)
        self.assertIn(self.app.profile_var.get(), pc_targets)

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

    def test_help_links_dialog_uses_clean_source_table(self):
        self.app.open_help_links()
        self.app.root.update_idletasks()
        self.app.root.update()

        help_windows = [
            child
            for child in self.app.root.winfo_children()
            if isinstance(child, tk.Toplevel)
            and child.winfo_exists()
            and child.title() == "Help Links"
        ]
        self.assertTrue(help_windows)

        help_window = help_windows[-1]
        table = _find_child(help_window, ttk.Treeview)
        self.assertIsNotNone(table)
        self.assertEqual(table.heading("name")["text"], "Name")
        self.assertEqual(table.heading("url")["text"], "Website")

        buttons_by_text = {
            button.cget("text"): button
            for button in _collect_widgets(help_window, ttk.Button)
            if button.cget("text")
        }
        for text in ("Open Link", "Add Link", "Edit", "Delete", "Close"):
            with self.subTest(button=text):
                self.assertIn(text, buttons_by_text)
                self.assertTrue(buttons_by_text[text].cget("command"))

        for removed_text in ("Move Up", "Move Down", "Reset"):
            self.assertNotIn(removed_text, buttons_by_text)

        help_window.destroy()

    def test_templates_dialog_is_compact_and_buttons_are_wired(self):
        self.app.profile_var.set("Atmosphere (Switch) (CFW)")
        self.app.open_templates()
        self.app.root.update_idletasks()
        self.app.root.update()

        template_windows = [
            child
            for child in self.app.root.winfo_children()
            if isinstance(child, tk.Toplevel)
            and child.winfo_exists()
            and child.title() == "Templates"
        ]
        self.assertTrue(template_windows)

        template_window = template_windows[-1]
        labels = [
            label.cget("text")
            for label in _collect_widgets(template_window, tk.Label)
            if label.cget("text")
        ]
        self.assertFalse(
            any("Atmosphere" in label or "Profile:" in label for label in labels)
        )
        self.assertLessEqual(template_window.winfo_width(), 760)
        self.assertLessEqual(template_window.winfo_height(), 540)

        main_buttons = {
            "Use Template",
            "Replace Editor",
            "Add Template",
            "Delete Template",
            "Close",
        }
        buttons_by_text = {
            button.cget("text"): button
            for button in _collect_widgets(template_window, ttk.Button)
            if button.cget("text")
        }
        for text in main_buttons:
            with self.subTest(button=text):
                self.assertIn(text, buttons_by_text)
                self.assertTrue(buttons_by_text[text].cget("command"))

        self.assertEqual(str(buttons_by_text["Delete Template"].cget("state")), "disabled")

        for hidden_text in (
            "Save as template",
            "Set as default",
            "Insert helper",
            "Open folder",
            "Reset templates",
            "Manage...",
        ):
            self.assertNotIn(hidden_text, buttons_by_text)

        nested_windows = [
            child
            for child in template_window.winfo_children()
            if isinstance(child, tk.Toplevel)
            and child.winfo_exists()
        ]
        self.assertFalse(nested_windows)

        template_window.destroy()

    def test_add_template_dialog_saves_edited_text(self):
        self.app.profile_var.set("Atmosphere (Switch) (CFW)")
        self.app.editor.delete("1.0", "end")
        self.app.editor.insert("1.0", "original editor text")

        with patch(
            "cheat_editor_manager.ui.dialogs.templates_dialog.list_templates",
            return_value=["Blank"],
        ), patch(
            "cheat_editor_manager.ui.dialogs.templates_dialog.read_template",
            return_value="",
        ), patch(
            "cheat_editor_manager.ui.dialogs.templates_dialog.write_template"
        ) as write_template:
            self.app.open_templates()
            self.app.root.update_idletasks()
            self.app.root.update()

            template_window = [
                child
                for child in self.app.root.winfo_children()
                if isinstance(child, tk.Toplevel)
                and child.winfo_exists()
                and child.title() == "Templates"
            ][-1]
            add_button = _find_widget_with_text(
                template_window,
                ttk.Button,
                "Add Template",
            )
            self.assertIsNotNone(add_button)

            errors = []

            def complete_add_dialog():
                try:
                    add_windows = [
                        child
                        for child in template_window.winfo_children()
                        if isinstance(child, tk.Toplevel)
                        and child.winfo_exists()
                        and child.title() == "Add Template"
                    ]
                    self.assertTrue(add_windows)

                    add_window = add_windows[-1]
                    name_entry = _find_child(add_window, ttk.Entry)
                    template_text = _find_child(add_window, tk.Text)
                    save_button = _find_widget_with_text(
                        add_window,
                        ttk.Button,
                        "Save Template",
                    )

                    self.assertIsNotNone(name_entry)
                    self.assertIsNotNone(template_text)
                    self.assertIsNotNone(save_button)
                    self.assertEqual(
                        template_text.get("1.0", "end-1c"),
                        "original editor text",
                    )

                    name_entry.insert(0, "Saved Text")
                    template_text.delete("1.0", "end")
                    template_text.insert("1.0", "edited template text")
                    save_button.invoke()
                except Exception as exc:
                    errors.append(exc)

            self.app.root.after(50, complete_add_dialog)
            add_button.invoke()
            if errors:
                raise errors[0]

            write_template.assert_called_once_with(
                "Saved Text",
                "edited template text",
            )
            template_window.destroy()


if __name__ == "__main__":
    unittest.main()
