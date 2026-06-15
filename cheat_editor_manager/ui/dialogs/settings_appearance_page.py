from __future__ import annotations

from dataclasses import dataclass
import re
import tkinter as tk
from tkinter import colorchooser, ttk

from ...constants import DEFAULT_BUTTON_COLORS, DEFAULT_THEME_DARK, DEFAULT_THEME_LIGHT
from ...ui.style import (
    CONTROL_GAP,
    DIALOG_CONTENT_PAD_X,
    DIALOG_WIDE_WRAP,
    FONT_PANEL_TITLE,
    PAD_TIGHT,
    PANEL_GAP,
)
from ...ui.widgets import Scrollable
from .dialog_utils import (
    build_dialog_page_header,
    build_dialog_section,
    refresh_dialog_theme,
)


THEME_FIELDS = [
    ("bg", "Window background"),
    ("panel", "Panel background"),
    ("panel2", "Secondary panel"),
    ("text", "Main text"),
    ("muted", "Muted text"),
    ("entry", "Entry/dropdown background"),
    ("border", "Borders"),
    ("editor_bg", "Editor background"),
    ("editor_fg", "Editor text"),
]

BUTTON_COLOR_FIELDS = [
    ("header", "Top header (app title bar)"),
    ("primary", "Primary action (Quick Export)"),
    ("secondary", "Standard buttons (Load / Convert / Settings)"),
    ("toolbar", "Toolbar buttons (Heading / Bold / Undo / Redo)"),
    ("danger", "Destructive buttons (Clear / Delete)"),
]

HELPER_FONTS = ["Consolas", "Courier New", "Segoe UI", "Arial", "Calibri", "Tahoma"]
TAB_PAD = PAD_TIGHT
CONTENT_PAD = DIALOG_CONTENT_PAD_X
TEXT_WRAP = DIALOG_WIDE_WRAP
FIELD_ENTRY_WIDTH = 18


@dataclass
class SettingsAppearancePage:
    app: object
    window: tk.Toplevel
    root_scrollable: Scrollable | None
    profile_page: object
    scrollable: Scrollable
    mode_var: tk.StringVar
    font_var: tk.IntVar
    helper_font_var: tk.StringVar
    color_vars: dict[str, tk.StringVar]
    button_color_vars: dict[str, tk.StringVar]
    dialog_surfaces: tuple = ()
    extra_theme_targets: tuple = ()

    def save_to_prefs(self) -> None:
        self.app.prefs["custom_theme_enabled"] = self.mode_var.get() == "custom"
        if self.mode_var.get() in ("dark", "light"):
            self.app.prefs["mode"] = self.mode_var.get()
        self.app.prefs["editor_font_size"] = int(self.font_var.get())
        self.app.prefs["helper_font_family"] = (
            self.helper_font_var.get().strip() or "Consolas"
        )
        self.app.prefs["custom_theme"] = self.collect_theme_preview_values()
        self.app.prefs["button_colors"] = self.collect_button_preview_values()

    def collect_theme_preview_values(self) -> dict:
        base = dict(
            DEFAULT_THEME_DARK
            if self.app.prefs.get("mode") == "dark"
            else DEFAULT_THEME_LIGHT
        )
        base.update(self.app.prefs.get("custom_theme", {}) or {})
        for key, value in self.color_vars.items():
            raw = value.get().strip()
            if _valid_preview_colour(raw):
                base[key] = raw
        return base

    def collect_button_preview_values(self) -> dict:
        base = dict(DEFAULT_BUTTON_COLORS)
        base.update(self.app.prefs.get("button_colors", {}) or {})
        for key, value in self.button_color_vars.items():
            raw = value.get().strip()
            if _valid_preview_colour(raw):
                base[key] = raw
        return base

    def apply_preview(self, *_):
        try:
            self.save_to_prefs()
            self.app.apply_theme()
            colors = self.app.effective_colors()
            bg = colors["bg"]
            if self.root_scrollable is not None:
                self.root_scrollable.set_canvas_bg(bg)
            for target in (self.profile_page, *self.extra_theme_targets):
                if hasattr(target, "apply_theme"):
                    target.apply_theme(self.app)
            self.scrollable.set_canvas_bg(bg)
            try:
                self.window.configure(bg=bg)
            except Exception:
                pass
            refresh_dialog_theme(self.app, *self.dialog_surfaces)
        except Exception:
            pass

    def reset_default_colours(self) -> None:
        base_theme = dict(
            DEFAULT_THEME_DARK
            if self.app.prefs.get("mode") == "dark"
            else DEFAULT_THEME_LIGHT
        )
        for key, value in self.color_vars.items():
            value.set(str(base_theme.get(key, "") or ""))
        for key, value in self.button_color_vars.items():
            value.set(str(DEFAULT_BUTTON_COLORS.get(key, "") or ""))
        self.mode_var.set("custom")


def build_appearance_page(
    app,
    page: ttk.Frame,
    window: tk.Toplevel,
    root_scrollable: Scrollable | None,
    profile_page,
    dialog_surfaces: tuple = (),
) -> SettingsAppearancePage:
    app_sf = Scrollable(page)
    app_sf.pack(fill="both", expand=True, padx=TAB_PAD, pady=TAB_PAD)
    app_sf.set_canvas_bg(app.effective_colors()["bg"])

    build_dialog_page_header(
        app_sf.inner,
        "Appearance",
        "Set the app mode, editor text size, helper font, and optional custom colours.",
        wraplength=TEXT_WRAP,
    )

    mode_card = build_dialog_section(app_sf.inner, "Mode and text")
    mode_var = tk.StringVar(
        value=_current_mode(app.prefs)
    )
    _build_mode_row(mode_card, mode_var)

    font_var = _build_editor_font_row(mode_card, app.prefs)
    helper_font_var = _build_helper_font_row(mode_card, app.prefs)

    ttk.Label(
        mode_card,
        text="Custom colours only apply when Mode is set to Custom.",
        wraplength=TEXT_WRAP,
    ).pack(anchor="w", padx=CONTENT_PAD, pady=(0, CONTENT_PAD))

    colours = build_dialog_section(app_sf.inner, "Custom colour editor")
    ttk.Label(
        colours,
        text="Shown only when Mode is set to Custom.",
        wraplength=TEXT_WRAP,
    ).pack(anchor="w", padx=CONTENT_PAD, pady=(0, PANEL_GAP))
    color_vars, theme_entries = _build_colour_grid(
        colours,
        "Theme",
        THEME_FIELDS,
        _current_theme_values(app.prefs),
    )

    button_color_vars, button_entries = _build_colour_grid(
        colours,
        "Buttons",
        BUTTON_COLOR_FIELDS,
        _current_button_values(app.prefs),
    )

    appearance_page = SettingsAppearancePage(
        app=app,
        window=window,
        root_scrollable=root_scrollable,
        profile_page=profile_page,
        scrollable=app_sf,
        mode_var=mode_var,
        font_var=font_var,
        helper_font_var=helper_font_var,
        color_vars=color_vars,
        button_color_vars=button_color_vars,
        dialog_surfaces=dialog_surfaces,
    )

    control_widgets = theme_entries + button_entries
    _wire_appearance_traces(
        app,
        appearance_page,
        mode_var=mode_var,
        font_var=font_var,
        helper_font_var=helper_font_var,
        color_vars=color_vars,
        button_color_vars=button_color_vars,
        custom_section=colours,
        control_widgets=control_widgets,
    )
    _build_reset_row(colours, appearance_page)

    return appearance_page


def _current_mode(prefs: dict) -> str:
    current_mode = (
        "custom"
        if prefs.get("custom_theme_enabled", False)
        else str(prefs.get("mode", "dark") or "dark")
    )
    return current_mode if current_mode in ("dark", "light", "custom") else "dark"


def _current_theme_values(prefs: dict) -> dict:
    base_theme = DEFAULT_THEME_DARK if prefs.get("mode") == "dark" else DEFAULT_THEME_LIGHT
    current_theme = dict(base_theme)
    saved_custom = dict(prefs.get("custom_theme", {}) or {})
    if (
        prefs.get("custom_theme_enabled", False)
        and prefs.get("mode") == "light"
        and saved_custom == dict(DEFAULT_THEME_DARK)
    ):
        saved_custom = {}
    current_theme.update(saved_custom)
    return current_theme


def _current_button_values(prefs: dict) -> dict:
    current_buttons = dict(DEFAULT_BUTTON_COLORS)
    current_buttons.update(prefs.get("button_colors", {}))
    return current_buttons


def _build_mode_row(parent, mode_var: tk.StringVar) -> None:
    mode_row = ttk.Frame(parent)
    mode_row.pack(fill="x", padx=CONTENT_PAD, pady=(0, PANEL_GAP))
    ttk.Label(mode_row, text="Mode:").pack(side="left")
    for label, value in (("Dark", "dark"), ("Light", "light"), ("Custom", "custom")):
        ttk.Radiobutton(
            mode_row,
            text=label,
            value=value,
            variable=mode_var,
        ).pack(side="left", padx=(12, 0))


def _build_editor_font_row(parent, prefs: dict) -> tk.IntVar:
    row = ttk.Frame(parent)
    row.pack(fill="x", padx=CONTENT_PAD, pady=(0, PANEL_GAP))
    ttk.Label(row, text="Editor font size:").pack(side="left")
    font_var = tk.IntVar(value=int(prefs.get("editor_font_size", 11) or 11))
    ttk.Spinbox(row, from_=8, to=24, textvariable=font_var, width=6).pack(
        side="left", padx=(CONTROL_GAP, 0)
    )
    ttk.Label(row, text="updates instantly").pack(
        side="left", padx=(CONTROL_GAP, 0)
    )
    return font_var


def _build_helper_font_row(parent, prefs: dict) -> tk.StringVar:
    helper_font_row = ttk.Frame(parent)
    helper_font_row.pack(fill="x", padx=CONTENT_PAD, pady=(0, PANEL_GAP))
    ttk.Label(
        helper_font_row,
        text="Helper font:",
    ).pack(side="left")
    helper_font_var = tk.StringVar(
        value=str(prefs.get("helper_font_family") or "Consolas")
    )
    ttk.Combobox(
        helper_font_row,
        textvariable=helper_font_var,
        values=HELPER_FONTS,
        state="readonly",
        width=20,
    ).pack(side="left", padx=(CONTROL_GAP, 0))
    return helper_font_var


def _build_colour_grid(
    parent, title: str, fields: list[tuple[str, str]], current_values: dict
) -> tuple[dict[str, tk.StringVar], list]:
    value_vars: dict[str, tk.StringVar] = {}
    entries = []
    grid = ttk.Frame(parent)
    grid.pack(fill="x", padx=CONTENT_PAD, pady=(0, PANEL_GAP))
    grid.columnconfigure(2, weight=1)
    grid.columnconfigure(6, weight=1)
    ttk.Label(grid, text=title, font=FONT_PANEL_TITLE).grid(
        row=0, column=0, sticky="w", columnspan=3, pady=(0, CONTROL_GAP)
    )

    split_at = (len(fields) + 1) // 2
    for row_index, (key, label) in enumerate(fields):
        column_offset = 0 if row_index < split_at else 4
        display_row = (row_index % split_at) + 1
        ttk.Label(grid, text=label).grid(
            row=display_row, column=column_offset, sticky="w", pady=4
        )
        value = tk.StringVar(value=str(current_values.get(key, "")))
        value_vars[key] = value
        swatch = tk.Label(
            grid,
            width=3,
            text="",
            relief="solid",
            bd=1,
            cursor="hand2",
        )
        swatch.grid(
            row=display_row,
            column=column_offset + 1,
            sticky="ew",
            padx=(PANEL_GAP, 0),
            pady=4,
        )
        entry = ttk.Entry(grid, textvariable=value, width=FIELD_ENTRY_WIDTH)
        entry.grid(
            row=display_row,
            column=column_offset + 2,
            sticky="ew",
            padx=(CONTROL_GAP, PANEL_GAP if column_offset == 0 else 0),
            pady=4,
        )
        swatch.bind(
            "<Button-1>",
            lambda _event, field_key=key, variable=value: _pick_colour(
                field_key, variable
            ),
        )
        _update_colour_swatch(swatch, value)
        try:
            value.trace_add(
                "write",
                lambda *_args, target=swatch, variable=value: _update_colour_swatch(
                    target, variable
                ),
            )
        except Exception:
            pass
        entries.append(entry)
    return value_vars, entries


def _update_colour_swatch(swatch: tk.Label, variable: tk.StringVar) -> None:
    raw = variable.get().strip()
    if _valid_preview_colour(raw):
        swatch.configure(bg=raw, text="")
        return
    try:
        swatch.configure(bg=swatch.winfo_toplevel().cget("bg"), text="?")
    except Exception:
        swatch.configure(text="?")


def _pick_colour(field_key: str, variable: tk.StringVar) -> None:
    colour = colorchooser.askcolor(title=f"Choose {field_key}")
    if colour and colour[1]:
        variable.set(colour[1])


def _wire_appearance_traces(
    app,
    appearance_tab: SettingsAppearancePage,
    *,
    mode_var: tk.StringVar,
    font_var: tk.IntVar,
    helper_font_var: tk.StringVar,
    color_vars: dict[str, tk.StringVar],
    button_color_vars: dict[str, tk.StringVar],
    custom_section,
    control_widgets: list,
) -> None:
    def on_mode_change(*_) -> None:
        if mode_var.get() == "custom":
            _replace_stale_dark_custom_values(app.prefs, color_vars)
        _sync_custom_controls(
            mode_var,
            control_widgets,
            custom_section=custom_section,
        )

    try:
        mode_var.trace_add("write", on_mode_change)
        mode_var.trace_add("write", appearance_tab.apply_preview)
        font_var.trace_add("write", appearance_tab.apply_preview)
        helper_font_var.trace_add("write", appearance_tab.apply_preview)
        for value in color_vars.values():
            value.trace_add("write", appearance_tab.apply_preview)
        for value in button_color_vars.values():
            value.trace_add("write", appearance_tab.apply_preview)
    except Exception:
        pass

    _sync_custom_controls(
        mode_var,
        control_widgets,
        custom_section=custom_section,
    )


def _replace_stale_dark_custom_values(
    prefs: dict, color_vars: dict[str, tk.StringVar]
) -> None:
    try:
        if prefs.get("mode") != "light":
            return
        current_values = {key: value.get().strip() for key, value in color_vars.items()}
        if current_values and current_values == dict(DEFAULT_THEME_DARK):
            for key, value in DEFAULT_THEME_LIGHT.items():
                if key in color_vars:
                    color_vars[key].set(str(value))
    except Exception:
        pass


def _sync_custom_controls(
    mode_var: tk.StringVar, widgets: list, *, custom_section=None
) -> None:
    state = "normal" if mode_var.get() == "custom" else "disabled"
    if custom_section is not None:
        if mode_var.get() == "custom":
            try:
                custom_section.pack(
                    fill="x",
                    expand=False,
                    padx=CONTENT_PAD,
                    pady=(0, PANEL_GAP),
                )
            except Exception:
                pass
        else:
            try:
                custom_section.pack_forget()
            except Exception:
                pass
    for widget in widgets:
        try:
            widget.configure(state=state)
        except Exception:
            pass


def _build_reset_row(parent, appearance_tab: SettingsAppearancePage) -> None:
    reset_row = ttk.Frame(parent)
    reset_row.pack(fill="x", padx=CONTENT_PAD, pady=(0, CONTENT_PAD))
    ttk.Button(
        reset_row,
        text="Reset default colours",
        command=appearance_tab.reset_default_colours,
    ).pack(side="left")
    ttk.Label(
        reset_row,
        text="Resets Custom colours back to safe defaults.",
    ).pack(side="left", padx=(PANEL_GAP, 0))


def _valid_preview_colour(raw: str) -> bool:
    return bool(re.fullmatch(r"#[0-9a-fA-F]{6}", (raw or "").strip()))
