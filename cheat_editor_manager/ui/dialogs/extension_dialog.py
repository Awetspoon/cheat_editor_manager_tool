from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from ...ui.style import CONTROL_GAP, FONT_SECTION, PANEL_GAP
from .dialog_utils import bind_dialog_shortcuts, configure_dialog_window


EXTENSION_DIALOG_GEOMETRY = "430x305"
EXTENSION_DIALOG_WRAP = 380


def pick_extension_for_save(
    app,
    profile_name: str,
    profile_extensions: list[str],
    all_extensions: list[str],
) -> str | None:
    """Ask the user which extension Convert & Save should use."""
    dlg = tk.Toplevel(app.root)
    configure_dialog_window(
        app,
        dlg,
        "Choose file extension",
        EXTENSION_DIALOG_GEOMETRY,
        resizable=False,
    )

    profile_extensions = profile_extensions or [".txt"]
    all_extensions = all_extensions or list(profile_extensions)
    use_all_var = tk.BooleanVar(value=False)
    custom_enabled_var = tk.BooleanVar(value=False)
    ext_var = tk.StringVar(value=profile_extensions[0])
    custom_var = tk.StringVar(value="")
    out: dict[str, str | None] = {"ext": None}

    body = ttk.Frame(dlg)
    body.pack(fill="both", expand=True, padx=16, pady=14)

    ttk.Label(body, text="Choose File Extension", font=FONT_SECTION).pack(anchor="w")
    ttk.Label(
        body,
        text=f"Profile: {profile_name}",
        wraplength=EXTENSION_DIALOG_WRAP,
    ).pack(anchor="w", pady=(2, PANEL_GAP))

    picker_row = ttk.Frame(body)
    picker_row.pack(fill="x", pady=(0, CONTROL_GAP))
    ttk.Label(picker_row, text="Extension").pack(side="left")
    extension_combo = ttk.Combobox(
        picker_row,
        textvariable=ext_var,
        state="readonly",
        values=profile_extensions,
        width=14,
    )
    extension_combo.pack(side="left", padx=(CONTROL_GAP, 0))

    ttk.Checkbutton(
        body,
        text="Show all known extensions",
        variable=use_all_var,
    ).pack(anchor="w", pady=(0, CONTROL_GAP))

    custom_toggle = ttk.Checkbutton(
        body,
        text="Use custom extension",
        variable=custom_enabled_var,
    )
    custom_toggle.pack(anchor="w", pady=(0, 4))

    custom_row = ttk.Frame(body)
    custom_row.pack(fill="x", pady=(0, CONTROL_GAP))
    ttk.Label(custom_row, text="Custom").pack(side="left")
    custom_entry = ttk.Entry(custom_row, textvariable=custom_var, width=14)
    custom_entry.pack(side="left", padx=(CONTROL_GAP, 0))
    ttk.Label(custom_row, text="Example: .txt").pack(side="left", padx=(CONTROL_GAP, 0))

    hint_var = tk.StringVar(value=_extension_hint(False))
    ttk.Label(body, textvariable=hint_var, wraplength=EXTENSION_DIALOG_WRAP).pack(
        anchor="w", pady=(0, PANEL_GAP)
    )

    button_row = ttk.Frame(body)
    button_row.pack(fill="x", side="bottom", pady=(CONTROL_GAP, 0))

    def sync_extension_list(*_) -> None:
        values = all_extensions if use_all_var.get() else profile_extensions
        extension_combo.configure(values=values)
        if ext_var.get() not in values:
            ext_var.set(values[0] if values else ".txt")

    def sync_custom_state(*_) -> None:
        custom_enabled = custom_enabled_var.get()
        custom_entry.configure(state="normal" if custom_enabled else "disabled")
        hint_var.set(_extension_hint(custom_enabled))
        if custom_enabled:
            custom_entry.focus_set()

    def ok() -> None:
        custom_value = custom_var.get() if custom_enabled_var.get() else ""
        out["ext"] = _normalize_extension_choice(custom_value, ext_var.get())
        dlg.destroy()

    def cancel() -> None:
        out["ext"] = None
        dlg.destroy()

    use_all_var.trace_add("write", sync_extension_list)
    custom_enabled_var.trace_add("write", sync_custom_state)
    sync_extension_list()
    sync_custom_state()

    ttk.Button(button_row, text="Cancel", command=cancel).pack(
        side="right", padx=(CONTROL_GAP, 0)
    )
    ttk.Button(button_row, text="Continue", command=ok).pack(side="right")
    bind_dialog_shortcuts(dlg, confirm=ok, cancel=cancel)
    extension_combo.focus_set()

    dlg.wait_window()
    return out["ext"]


def _extension_hint(custom_enabled: bool) -> str:
    if custom_enabled:
        return "Type the file extension to use, for example .txt or .cht."
    return "Use the profile extension unless you need a custom file type."


def _normalize_extension_choice(custom_extension: str, selected_extension: str) -> str:
    raw_extension = custom_extension.strip() or selected_extension.strip() or ".txt"
    if not raw_extension.startswith("."):
        raw_extension = "." + raw_extension
    return raw_extension.lower()
