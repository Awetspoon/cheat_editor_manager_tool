from __future__ import annotations

from dataclasses import dataclass
import tkinter as tk

from tkinter import ttk

from ...storage import save_prefs
from ...ui.style import PANEL_GAP, PANEL_INNER_PAD_X
from ...ui.widgets import configure_listbox_theme
from .dialog_utils import (
    build_dialog_footer,
    build_dialog_header,
    configure_dialog_window,
    refresh_dialog_theme,
)
from .settings_appearance_page import build_appearance_page
from .settings_export_roots_page import build_export_roots_page
from .settings_profiles_page import build_profiles_page


SETTINGS_TITLE = "Settings"
SETTINGS_GEOMETRY = "980x640"
SETTINGS_DETAIL = "Clean app preferences for profiles, appearance, and export folders."
SETTINGS_BODY_PAD_X = PANEL_INNER_PAD_X
SETTINGS_NAV_WIDTH = 22


@dataclass
class SettingsShell:
    body: tk.Frame
    nav: tk.Listbox
    content: ttk.Frame
    pages: dict[str, ttk.Frame]
    controllers: dict[str, object]

    def show_page(self, key: str) -> None:
        for page_key, page in self.pages.items():
            if page_key == key:
                page.grid()
            else:
                page.grid_remove()

    def apply_theme(self, app) -> None:
        colors = app.effective_colors()
        try:
            self.body.configure(bg=colors["bg"])
        except Exception:
            pass
        configure_listbox_theme(self.nav, app)
        refresh_dialog_theme(app, self.body)
        for controller in self.controllers.values():
            if hasattr(controller, "apply_theme"):
                controller.apply_theme(app)


def open_settings(app):
    window = tk.Toplevel(app.root)
    configure_dialog_window(app, window, SETTINGS_TITLE, SETTINGS_GEOMETRY)

    header = build_dialog_header(app, window, SETTINGS_TITLE, SETTINGS_DETAIL)
    footer = build_dialog_footer(app, window, side="bottom")
    shell = _build_settings_shell(
        app,
        window,
        dialog_surfaces=(window, header, footer),
    )
    _wire_settings_close(app, window, footer, shell)
    shell.apply_theme(app)


def _build_settings_shell(
    app, window: tk.Toplevel, *, dialog_surfaces: tuple
) -> SettingsShell:
    body = tk.Frame(window, bd=0, highlightthickness=0)
    body.pack(
        fill="both",
        expand=True,
        padx=SETTINGS_BODY_PAD_X,
        pady=(0, PANEL_INNER_PAD_X),
    )
    body.columnconfigure(1, weight=1)
    body.rowconfigure(0, weight=1)

    nav = _build_settings_nav(body)
    content = ttk.Frame(body)
    content.grid(row=0, column=1, sticky="nsew", padx=(PANEL_GAP, 0))
    content.columnconfigure(0, weight=1)
    content.rowconfigure(0, weight=1)

    pages = {
        "profiles": ttk.Frame(content),
        "appearance": ttk.Frame(content),
        "export_roots": ttk.Frame(content),
    }
    for page in pages.values():
        page.grid(row=0, column=0, sticky="nsew")

    profile_page = build_profiles_page(app, pages["profiles"], window)
    export_roots_page = build_export_roots_page(app, pages["export_roots"], window)
    appearance_page = build_appearance_page(
        app,
        pages["appearance"],
        window,
        None,
        profile_page,
        dialog_surfaces=dialog_surfaces,
    )
    controllers = {
        "profiles": profile_page,
        "appearance": appearance_page,
        "export_roots": export_roots_page,
    }
    shell = SettingsShell(
        body=body,
        nav=nav,
        content=content,
        pages=pages,
        controllers=controllers,
    )
    appearance_page.extra_theme_targets = (export_roots_page, shell)

    def on_nav_select(*_) -> None:
        selected = nav.curselection()
        if not selected:
            return
        shell.show_page(_nav_key_for_index(selected[0]))

    nav.bind("<<ListboxSelect>>", on_nav_select)
    nav.selection_set(0)
    shell.show_page("profiles")
    return shell


def _build_settings_nav(parent) -> tk.Listbox:
    nav = tk.Listbox(
        parent,
        activestyle="none",
        exportselection=False,
        height=3,
        width=SETTINGS_NAV_WIDTH,
    )
    nav.grid(row=0, column=0, sticky="nsw")
    for label in ("Profiles", "Appearance", "Export Roots"):
        nav.insert(tk.END, label)
    return nav


def _nav_key_for_index(index: int) -> str:
    keys = ("profiles", "appearance", "export_roots")
    return keys[index] if 0 <= index < len(keys) else "profiles"


def _wire_settings_close(app, window: tk.Toplevel, footer, shell: SettingsShell) -> None:
    def apply_and_close() -> None:
        _apply_settings_and_close(app, window, shell)

    try:
        window.protocol("WM_DELETE_WINDOW", apply_and_close)
    except Exception:
        pass

    ttk.Button(footer, text="Close", command=apply_and_close).pack(
        side="right", padx=PANEL_INNER_PAD_X, pady=PANEL_GAP
    )


def _apply_settings_and_close(app, window: tk.Toplevel, shell: SettingsShell) -> None:
    for controller in shell.controllers.values():
        if hasattr(controller, "save_to_prefs"):
            controller.save_to_prefs()
    save_prefs(app.prefs)
    app.apply_theme()
    _call_app_callback(app, "_sync_core_dropdown")
    _call_app_callback(app, "refresh_profiles_dropdown")
    _call_app_callback(app, "refresh_profile_info")
    _call_app_callback(app, "update_export_preview")
    app.status.set("Settings saved.")
    window.destroy()


def _call_app_callback(app, name: str) -> None:
    callback = getattr(app, name, None)
    if not callable(callback):
        return
    try:
        callback()
    except Exception:
        pass
