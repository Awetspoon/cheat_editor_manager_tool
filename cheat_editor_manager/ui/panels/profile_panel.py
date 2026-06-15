from __future__ import annotations

import os
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from ...constants import APP_DIR
from ...profiles import (
    PROFILE_GROUP_CFW,
    get_profile_groups,
    get_profiles_for_group,
    profile_display_group,
)
from ...storage import save_prefs
from ..style import (
    CONTROL_GAP,
    FONT_PANEL_TITLE,
    PANEL_GAP,
    PANEL_INNER_PAD_X,
    PANEL_INNER_PAD_Y,
    PANEL_OUTER_PAD_X,
    TEXT_INSET_X,
    TEXT_INSET_Y,
)


PANEL_PAD_X = PANEL_INNER_PAD_X
PANEL_PAD_TOP = PANEL_INNER_PAD_Y
GROUP_GAP = CONTROL_GAP
BUTTON_GAP = CONTROL_GAP


def build_profile_controls(app) -> None:
    values = app.get_profile_values()
    app.profile_var = tk.StringVar(value=values[0] if values else "")
    app.profile_group_var = tk.StringVar(
        value=profile_display_group(app.prefs, values[0]) if values else PROFILE_GROUP_CFW
    )
    app.export_var = tk.StringVar(value=app.prefs.get("export_root", str(APP_DIR)))
    app.info_var = tk.StringVar(
        value=(
            "Quick Export builds the target folder. Convert & Save is for manual saves."
        )
    )

    _build_profile_panel(app)
    _build_target_group(app, values)
    _build_export_group(app)
    _build_profile_footer(app)

    app.profile_panel.bind(
        "<Configure>", lambda event: _refresh_profile_control_wrap(app, event), add="+"
    )


def _build_profile_panel(app) -> None:
    app._profile_controls_layout = (
        "sidebar" if hasattr(app, "left_sidebar") else "stacked"
    )
    parent = getattr(app, "left_sidebar", app.body.inner)
    app.profile_panel = tk.Frame(parent, bd=0, highlightthickness=1)
    if app._profile_controls_layout == "sidebar":
        app.profile_panel.pack(fill="x", padx=0, pady=(0, PANEL_GAP))
        app.profile_panel.columnconfigure(0, weight=1)
    else:
        app.profile_panel.pack(
            fill="x", padx=PANEL_OUTER_PAD_X, pady=(PANEL_GAP, CONTROL_GAP)
        )
        app.profile_panel.columnconfigure(0, weight=1, uniform="profile_controls")
        app.profile_panel.columnconfigure(1, weight=2, uniform="profile_controls")


def _control_group(
    parent: tk.Frame,
    *,
    row: int,
    column: int,
    padx: tuple[int, int],
    title: str,
    hint: str,
) -> tuple[tk.Frame, tk.Label, tk.Label]:
    group = tk.Frame(parent, bd=0, highlightthickness=0)
    group.grid(
        row=row,
        column=column,
        sticky="nsew",
        padx=padx,
        pady=(PANEL_PAD_TOP, GROUP_GAP),
    )
    group.columnconfigure(0, weight=1)

    title_label = tk.Label(group, text=title, font=FONT_PANEL_TITLE, anchor="w")
    title_label.grid(row=0, column=0, sticky="w")

    hint_label = tk.Label(group, text=hint, anchor="w")
    hint_label.grid(row=1, column=0, sticky="w", pady=(1, 5))
    return group, title_label, hint_label


def _build_target_group(app, values: list[str]) -> None:
    sidebar_layout = app._profile_controls_layout == "sidebar"
    (
        app.profile_target_group,
        app.profile_target_title,
        app.profile_target_hint,
    ) = _control_group(
        app.profile_panel,
        row=0,
        column=0,
        padx=(PANEL_PAD_X, PANEL_PAD_X if sidebar_layout else GROUP_GAP),
        title="Target",
        hint="Choose group, then target",
    )

    app.profile_combo_wrap = tk.Frame(
        app.profile_target_group, bd=0, highlightthickness=0
    )
    app.profile_combo_wrap.grid(row=2, column=0, sticky="ew")
    app.profile_combo_wrap.columnconfigure(0, weight=1)

    app.profile_group_label = tk.Label(
        app.profile_combo_wrap, text="Group", anchor="w"
    )
    app.profile_group_label.grid(row=0, column=0, sticky="w")
    app.profile_group_cb = ttk.Combobox(
        app.profile_combo_wrap,
        textvariable=app.profile_group_var,
        values=get_profile_groups(app.prefs),
        state="readonly",
        width=34,
        style="Profile.TCombobox",
    )
    app.profile_group_cb.grid(row=1, column=0, sticky="ew", pady=(3, CONTROL_GAP))
    app.profile_group_cb.bind(
        "<<ComboboxSelected>>", lambda _e: _on_profile_group_selected(app)
    )

    app.profile_select_label = tk.Label(
        app.profile_combo_wrap, text="Target profile", anchor="w"
    )
    app.profile_select_label.grid(row=2, column=0, sticky="w")
    app.profile_cb = ttk.Combobox(
        app.profile_combo_wrap,
        textvariable=app.profile_var,
        values=get_profiles_for_group(app.prefs, app.profile_group_var.get()),
        state="readonly",
        width=34,
        style="Profile.TCombobox",
    )
    app.profile_cb.grid(row=3, column=0, sticky="ew", pady=(3, 0))
    app.profile_cb.bind("<<ComboboxSelected>>", lambda _e: _on_profile_selected(app))
    refresh_profiles_dropdown(app)


def _build_export_group(app) -> None:
    sidebar_layout = app._profile_controls_layout == "sidebar"
    (
        app.profile_export_group,
        app.profile_export_title,
        app.profile_export_hint,
    ) = _control_group(
        app.profile_panel,
        row=1 if sidebar_layout else 0,
        column=0 if sidebar_layout else 1,
        padx=(PANEL_PAD_X if sidebar_layout else GROUP_GAP, PANEL_PAD_X),
        title="Export Root",
        hint="Destination folder",
    )

    app.profile_export_row = tk.Frame(
        app.profile_export_group, bd=0, highlightthickness=0
    )
    app.profile_export_row.grid(row=2, column=0, sticky="ew")
    app.profile_export_row.columnconfigure(0, weight=1)
    app.export_entry = ttk.Entry(
        app.profile_export_row, textvariable=app.export_var, width=54
    )
    app.export_entry.grid(row=0, column=0, sticky="ew")

    app.profile_export_actions = tk.Frame(
        app.profile_export_row, bd=0, highlightthickness=0
    )
    if sidebar_layout:
        app.profile_export_actions.grid(row=1, column=0, sticky="ew", pady=(BUTTON_GAP, 0))
    else:
        app.profile_export_actions.grid(
            row=0, column=1, sticky="e", padx=(BUTTON_GAP, 0)
        )

    _action_button(
        app,
        text="Open Folder",
        command=app.open_export_root,
        tooltip="Opens the Export Root folder in your file explorer.",
    )
    _action_button(app, text="Change...", command=app.change_root)
    _action_button(
        app,
        text="Reset Default",
        command=app.reset_export_root,
        tooltip="Resets Export Root back to the default location.",
    )


def _action_button(app, *, text: str, command, tooltip: str | None = None) -> ttk.Button:
    has_previous_button = bool(app.profile_export_actions.winfo_children())
    button = ttk.Button(app.profile_export_actions, text=text, command=command)
    if app._profile_controls_layout == "sidebar":
        button.pack(fill="x", pady=(BUTTON_GAP if has_previous_button else 0, 0))
    else:
        button.pack(side="left", padx=(BUTTON_GAP if has_previous_button else 0, 0))
    if tooltip:
        app._tt(button, tooltip)
    return button


def _build_profile_footer(app) -> None:
    app.profile_footer = tk.Frame(app.profile_panel, bd=0, highlightthickness=0)
    sidebar_layout = app._profile_controls_layout == "sidebar"
    app.profile_footer.grid(
        row=2 if sidebar_layout else 1,
        column=0,
        columnspan=1 if sidebar_layout else 2,
        sticky="ew",
        padx=PANEL_PAD_X,
        pady=(0, PANEL_GAP),
    )
    app.info_label = tk.Label(
        app.profile_footer,
        textvariable=app.info_var,
        anchor="w",
        justify="left",
        padx=TEXT_INSET_X,
        pady=TEXT_INSET_Y,
        highlightthickness=1,
    )
    app.info_label.pack(fill="x", expand=True)
    app.info_label.bind(
        "<Configure>",
        lambda event: _refresh_profile_control_wrap(app, event),
        add="+",
    )


def _refresh_profile_control_wrap(app, event=None) -> None:
    try:
        width = getattr(event, "width", 0) or app.info_label.winfo_width()
        app.info_label.configure(wraplength=max(120, width - (TEXT_INSET_X * 2)))
    except Exception:
        pass


def refresh_profiles_dropdown(app) -> None:
    try:
        values = app.get_profile_values()
        if not values:
            app.profile_cb["values"] = []
            return

        selected_profile = app.profile_var.get()
        if selected_profile not in values:
            selected_profile = values[0]
            app.profile_var.set(selected_profile)

        selected_group = profile_display_group(app.prefs, selected_profile)
        groups = get_profile_groups(app.prefs)
        if hasattr(app, "profile_group_cb"):
            app.profile_group_cb["values"] = groups
        if hasattr(app, "profile_group_var") and (
            app.profile_group_var.get() not in groups
            or app.profile_group_var.get() != selected_group
        ):
            app.profile_group_var.set(selected_group)

        group_profiles = get_profiles_for_group(app.prefs, selected_group)
        app.profile_cb["values"] = group_profiles
        if hasattr(app.profile_cb, "set"):
            app.profile_cb.set(selected_profile)
    except Exception:
        pass


def _on_profile_group_selected(app) -> None:
    values = get_profiles_for_group(app.prefs, app.profile_group_var.get())
    try:
        app.profile_cb["values"] = values
    except Exception:
        pass
    if values and app.profile_var.get() not in values:
        app.profile_var.set(values[0])
        try:
            app.profile_cb.set(values[0])
        except Exception:
            pass
    app.refresh_profile_info()


def _on_profile_selected(app) -> None:
    profile_name = app.profile_var.get()
    group = profile_display_group(app.prefs, profile_name)
    if hasattr(app, "profile_group_var") and app.profile_group_var.get() != group:
        app.profile_group_var.set(group)
    app.refresh_profile_info()


def change_export_root(app) -> None:
    selected_path = filedialog.askdirectory()
    if not selected_path:
        return
    app.export_var.set(selected_path)
    app.prefs["export_root"] = selected_path
    save_prefs(app.prefs)
    app.status.set(f"Export root set: {selected_path}")


def open_export_root(app) -> None:
    path = Path(app.export_var.get() or app.prefs.get("export_root", str(APP_DIR)))
    try:
        os.startfile(path)  # type: ignore[attr-defined]
    except Exception:
        messagebox.showinfo("Export Root", str(path))


def reset_export_root(app) -> None:
    app.export_var.set(str(APP_DIR))
    app.prefs["export_root"] = str(APP_DIR)
    save_prefs(app.prefs)
    app.status.set("Export root reset to default.")
