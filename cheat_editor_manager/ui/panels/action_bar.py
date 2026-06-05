from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from ..style import CONTROL_GAP, PANEL_OUTER_PAD_X, STATUS_INSET_Y


DEFAULT_STATUS = "[READY] Waiting for input"
ACTION_ROW_PAD_X = PANEL_OUTER_PAD_X
ACTION_ROW_PAD_Y = CONTROL_GAP
ACTION_BUTTON_GAP = CONTROL_GAP


def build_action_bar(app) -> None:
    _build_footer_shell(app)
    _build_status_strip(app)
    _build_action_row(app)


def _build_footer_shell(app) -> None:
    app.footer = tk.Frame(app.root, bd=0, highlightthickness=1)
    app.footer.pack(side="bottom", fill="x")
    app.footer.columnconfigure(0, weight=1)


def _build_status_strip(app) -> None:
    app.status = tk.StringVar(value=DEFAULT_STATUS)
    app.status_frame = tk.Frame(app.footer, bd=0, highlightthickness=0)
    app.status_frame.grid(row=0, column=0, sticky="ew")
    app.status_label = tk.Label(
        app.status_frame,
        textvariable=app.status,
        anchor="w",
        padx=ACTION_ROW_PAD_X,
        pady=STATUS_INSET_Y,
    )
    app.status_label.pack(fill="x")


def _build_action_row(app) -> None:
    app.bottom_bar = tk.Frame(app.footer, bd=0, highlightthickness=0)
    app.bottom_bar.grid(row=1, column=0, sticky="ew")
    app.action_row = tk.Frame(app.bottom_bar, bd=0, highlightthickness=0)
    app.action_row.pack(
        fill="x",
        padx=ACTION_ROW_PAD_X,
        pady=(ACTION_ROW_PAD_Y, ACTION_ROW_PAD_Y),
    )

    app.load_button = _action_button(
        app,
        text="Load File...",
        command=app.load_file,
        tooltip=(
            "Load an existing cheat file into the editor "
            "(auto-detects profile fields where possible)."
        ),
    )
    app.quick_export_button = _action_button(
        app,
        text="Quick Export",
        command=app.quick_export,
        style="Primary.TButton",
        tooltip=(
            "Quick Export: builds the correct folder structure automatically "
            "for the selected profile."
        ),
    )
    app.convert_button = _action_button(
        app,
        text="Convert & Save...",
        command=app.convert_save,
        tooltip=(
            "Convert & Save: save the editor text anywhere with any "
            "filename/extension."
        ),
    )


def _action_button(
    app,
    *,
    text: str,
    command,
    tooltip: str,
    style: str | None = None,
) -> ttk.Button:
    has_previous_button = bool(app.action_row.winfo_children())
    button_options = {"text": text, "command": command}
    if style:
        button_options["style"] = style
    button = ttk.Button(app.action_row, **button_options)
    button.pack(side="left", padx=(ACTION_BUTTON_GAP if has_previous_button else 0, 0))
    app._tt(button, tooltip)
    return button
