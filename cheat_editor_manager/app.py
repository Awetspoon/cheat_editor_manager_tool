from __future__ import annotations

import ctypes
import sys
import tkinter as tk
import tkinter.font as tkfont
from pathlib import Path
from typing import Optional

try:
    from tkinterdnd2 import DND_FILES, TkinterDnD  # type: ignore
    _HAS_DND = True
except Exception:
    TkinterDnD = None  # type: ignore
    DND_FILES = None  # type: ignore
    _HAS_DND = False

from .app_actions import ExportFileActionsMixin
from .app_actions import RetroarchCoreActionsMixin
from .constants import (
    APP_NAME,
    APP_VERSION,
)
from .storage import (
    ensure_demo_templates,
    load_prefs,
    save_prefs,
)
from .resources import asset_path
from .resources import tk_file_path
from .ui.context_menu import build_context_menu
from .ui.context_menu import run_context_action
from .ui.context_menu import show_context_menu
from .ui.style import FONT_MARK_FALLBACK
from .ui.theme import apply_theme as apply_theme_to_app
from .ui.theme import build_styles as build_styles_for_app
from .ui.widgets import Scrollable, ToolTip


from .bootstrap import configure_tcl_environment
from .profiles import (
    get_profile_info as get_profile_info_for_prefs,
    get_profile_values as get_profile_values_for_prefs,
    is_atmosphere_profile,
    primary_extension,
    profile_id_field_label,
    profile_id_hint,
    profile_template_path,
    uses_id_layout,
)
from .services import theme_service
from .ui.dialogs.help_links_dialog import open_help_links as open_help_links_dialog
from .ui.dialogs.retroarch_cores_dialog import (
    manage_retroarch_cores as manage_retroarch_cores_dialog,
)
from .ui.dialogs.settings_dialog import open_settings as open_settings_dialog
from .ui.dialogs.templates_dialog import open_templates as open_templates_dialog
from .ui.panels.action_bar import build_action_bar
from .ui.panels.editor_panel import build_editor_panel
from .ui.panels.editor_panel import clear_editor as clear_editor_text
from .ui.panels.editor_panel import format_bold as format_editor_bold
from .ui.panels.editor_panel import format_heading as format_editor_heading
from .ui.panels.editor_panel import redo as redo_editor_action
from .ui.panels.editor_panel import toggle_wrap as toggle_editor_wrap
from .ui.panels.editor_panel import undo as undo_editor_action
from .ui.panels.header_panel import build_header
from .ui.panels.helper_panel import build_helper_panel
from .ui.panels.helper_panel import refresh_profile_info as refresh_helper_profile_info
from .ui.panels.helper_panel import refresh_target_cards as refresh_helper_target_cards
from .ui.panels.helper_panel import show_atmosphere_layout as show_helper_atmosphere_layout
from .ui.panels.helper_panel import show_core_layout as show_helper_core_layout
from .ui.panels.helper_panel import show_generic_layout as show_helper_generic_layout
from .ui.panels.helper_panel import show_switch_layout as show_helper_switch_layout
from .ui.panels.helper_panel import show_titleid_layout as show_helper_titleid_layout
from .ui.panels.profile_panel import build_profile_controls
from .ui.panels.profile_panel import change_export_root
from .ui.panels.profile_panel import open_export_root as open_export_root_for_app
from .ui.panels.profile_panel import refresh_profiles_dropdown as refresh_profiles_dropdown_for_app
from .ui.panels.profile_panel import reset_export_root as reset_export_root_for_app
from .ui.panels.workspace_panel import build_workspace

class App(RetroarchCoreActionsMixin, ExportFileActionsMixin):
    DEFAULT_WINDOW_WIDTH = 1280
    DEFAULT_WINDOW_HEIGHT = 820

    def __init__(self):
        configure_tcl_environment()
        ensure_demo_templates()
        self._startup_warnings: list[str] = []
        self.prefs = load_prefs()
        self._audit_retroarch_cores()
        self._set_windows_app_id()
        self.root = (TkinterDnD.Tk() if _HAS_DND else tk.Tk())
        self.root.title(f"{APP_NAME} - {APP_VERSION}")
        self._apply_startup_geometry()
        self._brand_images = {}
        self._native_hicon = None

        build_context_menu(self)

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self._build_styles()
        self._load_brand_assets()

        build_header(self)

        self.body = Scrollable(self.root)
        self.body.pack(fill="both", expand=True)

        build_workspace(self)

        build_profile_controls(self)

        build_editor_panel(self, has_dnd=_HAS_DND, dnd_files=DND_FILES)

        build_helper_panel(self)

        build_action_bar(self)

        self._apply_startup_warnings()
        self.apply_theme()
        self.refresh_profile_info()

    def _default_window_size(self) -> tuple[int, int]:
        return self.DEFAULT_WINDOW_WIDTH, self.DEFAULT_WINDOW_HEIGHT

    def _center_geometry(self, width: int, height: int) -> str:
        try:
            self.root.update_idletasks()
            screen_w = max(width, self.root.winfo_screenwidth())
            screen_h = max(height, self.root.winfo_screenheight())
        except Exception:
            return f"{width}x{height}"
        x = max(0, (screen_w - width) // 2)
        y = max(0, (screen_h - height) // 2 - 18)
        return f"{width}x{height}+{x}+{y}"

    def _apply_startup_geometry(self) -> None:
        default_w, default_h = self._default_window_size()
        self.root.geometry(self._center_geometry(default_w, default_h))

    @staticmethod
    def _set_windows_app_id() -> None:
        if not sys.platform.startswith("win"):
            return
        try:
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
                "Awetspoon.CheatEditorManagerTool"
            )
        except Exception:
            pass

    def _set_native_window_icon(self, icon_path: Optional[Path]) -> None:
        if not sys.platform.startswith("win"):
            return
        try:
            self.root.update_idletasks()
            hwnd = int(self.root.winfo_id())
        except Exception:
            return
        if hwnd <= 0:
            return

        candidate_paths: list[Path] = []
        if icon_path is not None and icon_path.exists():
            candidate_paths.append(icon_path)
        if getattr(sys, "frozen", False):
            exe_path = Path(sys.executable)
            if exe_path.exists():
                candidate_paths.append(exe_path)

        try:
            user32 = ctypes.windll.user32
            image_icon = 1
            lr_loadfromfile = 0x0010
            wm_seticon = 0x0080
            icon_small = 0
            icon_big = 1

            for candidate in candidate_paths:
                hicon = user32.LoadImageW(
                    None,
                    str(candidate),
                    image_icon,
                    0,
                    0,
                    lr_loadfromfile,
                )
                if not hicon:
                    continue
                user32.SendMessageW(hwnd, wm_seticon, icon_small, hicon)
                user32.SendMessageW(hwnd, wm_seticon, icon_big, hicon)
                self._native_hicon = hicon
                return
        except Exception:
            pass

    def _load_brand_assets(self):
        assets = {
            "window_icon": asset_path("app-icon.ico"),
            "icon_photo": asset_path("icon-256.png"),
            "header_mark": asset_path("mark-48.png"),
        }
        for key, path in assets.items():
            if not path.exists():
                continue
            if key == "window_icon":
                try:
                    self.root.iconbitmap(tk_file_path(path))
                except Exception:
                    try:
                        self.root.iconbitmap(default=tk_file_path(path))
                    except Exception:
                        pass
                continue
            try:
                self._brand_images[key] = tk.PhotoImage(file=tk_file_path(path))
            except Exception:
                pass
        self._set_native_window_icon(assets.get("window_icon"))
        if "icon_photo" not in self._brand_images:
            fallback_png = asset_path("app-icon.png")
            if fallback_png.exists():
                try:
                    self._brand_images["icon_photo"] = tk.PhotoImage(
                        file=tk_file_path(fallback_png)
                    )
                except Exception:
                    pass
        icon_photo = self._brand_images.get("icon_photo")
        if icon_photo is not None:
            try:
                self.root.iconphoto(True, icon_photo)
            except Exception:
                pass

    def _apply_brand_images(self):
        header_mark = self._brand_images.get("header_mark")
        if header_mark is not None:
            self.header_mark.configure(image=header_mark, text="")
        else:
            self.header_mark.configure(
                image="",
                text="CEM",
                fg="#fff6e8",
                font=FONT_MARK_FALLBACK,
                width=4,
                height=2,
            )

    def _tt(self, widget, text: str):
        # Keep a reference so tooltips are not garbage-collected.
        if not hasattr(self, "_tooltips"):
            self._tooltips = []
        self._tooltips.append(ToolTip(widget, text))

    def _record_startup_warning(self, message: str) -> None:
        self._startup_warnings.append(message)

    def _apply_startup_warnings(self) -> None:
        if self._startup_warnings:
            self.status.set(f"[WARN] {self._startup_warnings[-1]}")

    def _set_helper_display(self, txt: str) -> None:
        """Update the Helper display without making it look editable."""
        self.helper_text.set((txt or "").strip())
        self._on_helper_configure()

    def _on_helper_configure(self, event=None):
        try:
            width = getattr(event, "width", 0) or self.helper.winfo_width()
            if getattr(self, "_helper_layout_mode", "") == "sidebar":
                wrap = max(220, width - 48)
                self._helper_display.configure(wraplength=wrap)
                self._path_preview_label.configure(wraplength=wrap)
                for label in (
                    self._atmo_hint,
                    self._atmo_path_note,
                    self._switch_layout_hint,
                    self._switch_layout_note_label,
                    self._switch_layout_template_label,
                    self._titleid_hint,
                    self._titleid_note_label,
                    self._titleid_template_label,
                    self._retro_layout_hint,
                    self._retro_layout_note_label,
                    self._retro_layout_template_label,
                    self._generic_layout_hint,
                    self._generic_layout_note_label,
                    self._generic_layout_template_label,
                ):
                    label.configure(wraplength=wrap)
                return
            guidance_width = self._helper_card.winfo_width()
            if guidance_width <= 1:
                guidance_width = int(width * 0.38)
            layout_width = max(
                self._atmo_layout.winfo_width(),
                self._switch_layout.winfo_width(),
                self._titleid_layout.winfo_width(),
                self._retro_layout.winfo_width(),
                self._generic_layout.winfo_width(),
                int(width * 0.58),
            )
            guidance_wrap = max(220, guidance_width - 32)
            layout_wrap = max(320, layout_width - 48)
            preview_wrap = max(320, width - 48)
            self._helper_display.configure(wraplength=guidance_wrap)
            self._path_preview_label.configure(wraplength=preview_wrap)
            self._atmo_hint.configure(wraplength=layout_wrap)
            self._atmo_path_note.configure(wraplength=layout_wrap)
            self._switch_layout_hint.configure(wraplength=layout_wrap)
            self._switch_layout_note_label.configure(wraplength=layout_wrap)
            self._switch_layout_template_label.configure(wraplength=layout_wrap)
            self._titleid_hint.configure(wraplength=layout_wrap)
            self._titleid_note_label.configure(wraplength=layout_wrap)
            self._titleid_template_label.configure(wraplength=layout_wrap)
            self._retro_layout_hint.configure(wraplength=layout_wrap)
            self._retro_layout_note_label.configure(wraplength=layout_wrap)
            self._retro_layout_template_label.configure(wraplength=layout_wrap)
            self._generic_layout_hint.configure(wraplength=layout_wrap)
            self._generic_layout_note_label.configure(wraplength=layout_wrap)
            self._generic_layout_template_label.configure(wraplength=layout_wrap)
        except Exception:
            pass

    def _estimate_helper_visible_chars(self) -> int:
        """Approximate how many characters fit in the Helper display area."""
        try:
            w = max(1, self._helper_display.winfo_width())
            h = max(1, self._helper_display.winfo_height())
            f = tkfont.Font(font=self._helper_display.cget("font"))
            avg_char = max(6, f.measure("0"))
            line_h = max(10, f.metrics("linespace"))
            # leave a little padding
            chars_per_line = max(1, int((w - 12) / avg_char))
            lines_visible = max(1, int((h - 6) / line_h))
            return int(chars_per_line * lines_visible)
        except Exception:
            # safe fallback that matches a small helper box
            return 240

    def _build_styles(self):
        return build_styles_for_app(self)

    def get_profile_values(self):
        return get_profile_values_for_prefs(self.prefs)

    def get_profile_info(self, profile_name: str):
        return get_profile_info_for_prefs(self.prefs, profile_name)

    def refresh_profiles_dropdown(self):
        return refresh_profiles_dropdown_for_app(self)

    def effective_colors(self) -> dict:
        return theme_service.effective_colors(self.prefs)

    @staticmethod
    def _normalize_hex_color(value: str, fallback: str = "#000000") -> str:
        return theme_service.normalize_hex_color(value, fallback)

    @classmethod
    def _relative_luminance(cls, color: str) -> float:
        return theme_service.relative_luminance(color)

    @classmethod
    def _contrast_ratio(cls, fg: str, bg: str) -> float:
        return theme_service.contrast_ratio(fg, bg)

    @classmethod
    def _blend_colors(cls, start: str, end: str, amount: float) -> str:
        return theme_service.blend_colors(start, end, amount)

    @classmethod
    def _ensure_text_contrast(
        cls,
        bg: str,
        *,
        preferred: Optional[str] = None,
        light: str = "#fff8eb",
        dark: str = "#231b15",
        minimum: float = 4.5,
    ) -> str:
        return theme_service.ensure_text_contrast(
            bg,
            preferred=preferred,
            light=light,
            dark=dark,
            minimum=minimum,
        )

    @classmethod
    def _selection_palette(
        cls, accent: str, preferred_text: str = "#ffffff"
    ) -> tuple[str, str]:
        return theme_service.selection_palette(accent, preferred_text)

    @classmethod
    def _button_palette(
        cls,
        bg: str,
        surface_bg: str,
        preferred_text: str,
        *,
        minimum: float = 4.5,
        disabled_minimum: float = 3.0,
    ) -> dict:
        return theme_service.button_palette(
            bg,
            surface_bg,
            preferred_text,
            minimum=minimum,
            disabled_minimum=disabled_minimum,
        )

    @classmethod
    def _sanitize_theme_colors(cls, colors: dict, defaults: dict) -> dict:
        return theme_service.sanitize_theme_colors(colors, defaults)

    @staticmethod
    def _readable_text_color(bg: str) -> str:
        return theme_service.readable_text_color(bg)

    def toggle_mode(self):
        self.prefs["mode"] = "dark" if self.prefs.get("mode") == "light" else "light"
        save_prefs(self.prefs)
        self.apply_theme()

    def apply_theme(self):
        return apply_theme_to_app(self)

    def _show_tid_bid(self, show: bool):
        return show_helper_switch_layout(self, show)

    def _show_titleid_layout(self, show: bool):
        return show_helper_titleid_layout(self, show)

    def _show_core(self, show: bool):
        return show_helper_core_layout(self, show)

    def _show_generic_layout(self, show: bool):
        return show_helper_generic_layout(self, show)

    def _show_atmosphere_layout(self, show: bool):
        return show_helper_atmosphere_layout(self, show)

    def _is_atmosphere_profile(self, prof: str, info: Optional[dict] = None) -> bool:
        return is_atmosphere_profile(self.prefs, prof, info)

    def _primary_extension(self, info: dict) -> str:
        return primary_extension(info)

    def _uses_id_layout(self, info: dict) -> bool:
        return uses_id_layout(info)

    def _profile_id_field_label(self, info: dict) -> str:
        return profile_id_field_label(info)

    def _profile_id_hint(self, info: dict) -> str:
        return profile_id_hint(info)

    def _profile_template_path(self, prof: str, info: dict) -> str:
        return profile_template_path(self.prefs, prof, info, self.core_var.get())

    def _refresh_target_cards(self, prof: str, info: dict) -> None:
        return refresh_helper_target_cards(self, prof, info)

    def refresh_profile_info(self):
        return refresh_helper_profile_info(self)

    def fmt_heading(self):
        return format_editor_heading(self)

    def fmt_bold(self):
        return format_editor_bold(self)

    def do_undo(self, *_):
        return undo_editor_action(self, *_)

    def do_redo(self, *_):
        return redo_editor_action(self, *_)

    def clear_editor(self):
        return clear_editor_text(self)

    def toggle_wrap(self):
        return toggle_editor_wrap(self)

    def change_root(self):
        return change_export_root(self)

    def open_export_root(self):
        return open_export_root_for_app(self)

    def reset_export_root(self):
        return reset_export_root_for_app(self)

    def manage_retroarch_cores(self):
        return manage_retroarch_cores_dialog(self)

    def open_help_links(self):
        return open_help_links_dialog(self)

    def open_templates(self):
        return open_templates_dialog(self)

    def open_settings(self):
        return open_settings_dialog(self)

    def _show_ctx_menu(self, event):
        return show_context_menu(self, event)

    def _ctx_action(self, action: str):
        return run_context_action(self, action)

    def on_close(self):
        """Persist prefs and close the app."""
        try:
            save_prefs(self.prefs)
        finally:
            try:
                self.root.destroy()
            except Exception:
                pass

    def run(self):
        self.root.mainloop()
