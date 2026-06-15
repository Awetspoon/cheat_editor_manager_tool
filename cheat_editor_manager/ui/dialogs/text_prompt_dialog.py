from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Optional

from ...ui.style import CONTROL_GAP, PANEL_GAP, PANEL_INNER_PAD_X
from .dialog_utils import (
    bind_dialog_shortcuts,
    build_dialog_footer,
    build_dialog_header,
    configure_dialog_window,
)


TEXT_PROMPT_GEOMETRY = "500x215"


def ask_text_dialog(
    app,
    parent: tk.Toplevel,
    title: str,
    label: str,
    *,
    initial_value: str = "",
) -> Optional[str]:
    """Show a small themed text prompt and return the trimmed value."""
    window = tk.Toplevel(parent)
    configure_dialog_window(
        app,
        window,
        title,
        TEXT_PROMPT_GEOMETRY,
        parent=parent,
        resizable=False,
    )
    build_dialog_header(app, window, title, label)

    body = ttk.Frame(window)
    body.pack(
        fill="both",
        expand=True,
        padx=PANEL_INNER_PAD_X,
        pady=(0, PANEL_GAP),
    )
    body.columnconfigure(0, weight=1)

    value_var = tk.StringVar(value=initial_value)
    entry = ttk.Entry(body, textvariable=value_var)
    entry.grid(row=0, column=0, sticky="ew")

    output: dict[str, Optional[str]] = {"value": None}

    def confirm() -> None:
        output["value"] = normalize_prompt_value(value_var.get())
        window.destroy()

    def cancel() -> None:
        output["value"] = None
        window.destroy()

    footer = build_dialog_footer(app, window, pady=(0, PANEL_INNER_PAD_X))
    ttk.Button(footer, text="Cancel", command=cancel).pack(
        side="right",
        padx=(CONTROL_GAP, PANEL_INNER_PAD_X),
        pady=PANEL_GAP,
    )
    ttk.Button(footer, text="Save", command=confirm).pack(
        side="right",
        pady=PANEL_GAP,
    )

    bind_dialog_shortcuts(window, confirm=confirm, cancel=cancel)
    entry.focus_set()
    if initial_value:
        entry.selection_range(0, tk.END)
    window.wait_window()
    return output["value"]


def normalize_prompt_value(value: str) -> str:
    return str(value or "").strip()
