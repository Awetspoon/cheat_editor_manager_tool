from __future__ import annotations

import os
import tkinter as tk
from typing import Optional

from tkinter import messagebox, ttk

from ...services.template_service import build_helper_snippet
from ...storage import (
    ensure_demo_templates,
    list_templates,
    profile_templates_dir,
    read_template,
    save_prefs,
    write_template,
)
from ...ui.style import CONTROL_GAP, PANEL_GAP, PANEL_INNER_PAD_X
from ...ui.widgets import (
    AutoScrollbar,
    ask_text,
    configure_listbox_theme,
    configure_text_theme,
)
from .dialog_utils import (
    build_dialog_footer,
    build_dialog_header,
    build_dialog_scroll_body,
    configure_dialog_window,
)


CONTENT_PAD = PANEL_INNER_PAD_X
BUTTON_GAP = CONTROL_GAP


def open_templates(app):
    self = app
    prof = self.profile_var.get()
    if not prof:
        messagebox.showerror("Templates", "Select a profile before opening templates.")
        return

    win = tk.Toplevel(self.root)
    configure_dialog_window(self, win, f"Templates - {prof}", "860x620")

    sf = build_dialog_scroll_body(self, win)
    build_dialog_header(self, sf.inner, "Templates", f"Profile: {prof}")

    body = ttk.Frame(sf.inner)
    body.pack(fill="both", expand=True, padx=CONTENT_PAD, pady=(0, PANEL_GAP))
    body.columnconfigure(1, weight=1)
    body.rowconfigure(0, weight=1)

    list_frame = ttk.Frame(body)
    list_frame.grid(row=0, column=0, sticky="nsw")
    listbox = tk.Listbox(list_frame, height=14, width=34, activestyle="none")
    configure_listbox_theme(listbox, self)
    listbox.pack(side="left", fill="y")
    list_vsb = AutoScrollbar(list_frame, orient="vertical", command=listbox.yview)
    listbox.configure(yscrollcommand=list_vsb.set)
    list_vsb.pack(side="left", fill="y")

    preview_frame = ttk.Frame(body)
    preview_frame.grid(row=0, column=1, sticky="nsew", padx=(CONTENT_PAD, 0))
    preview_frame.columnconfigure(0, weight=1)
    preview_frame.rowconfigure(1, weight=1)
    ttk.Label(preview_frame, text="Template preview:").grid(
        row=0, column=0, sticky="w", pady=(0, 6)
    )
    preview = tk.Text(preview_frame, wrap="word", height=18)
    configure_text_theme(preview, self, editor=True)
    preview.grid(row=1, column=0, sticky="nsew")
    p_vsb = AutoScrollbar(preview_frame, orient="vertical", command=preview.yview)
    preview.configure(yscrollcommand=p_vsb.set)
    p_vsb.grid(row=1, column=1, sticky="ns")
    preview.configure(state="disabled")

    selected = tk.StringVar(value="Blank")

    def selected_name() -> str:
        sel = listbox.curselection()
        if sel:
            return listbox.get(sel[0])
        return selected.get() or "Blank"

    def load_preview():
        name = selected_name()
        selected.set(name)
        preview.configure(state="normal")
        preview.delete("1.0", tk.END)
        preview.insert("1.0", read_template(prof, name))
        preview.configure(state="disabled")

    def refresh(selected_name_override: Optional[str] = None):
        names = list_templates(prof)
        listbox.delete(0, tk.END)
        for name in names:
            listbox.insert(tk.END, name)

        default_name = (self.prefs.get("templates_default", {}) or {}).get(prof, "Blank")
        target = selected_name_override or selected.get() or default_name or "Blank"
        if target not in names:
            target = default_name if default_name in names else names[0]
        selected.set(target)
        idx = names.index(target)
        listbox.selection_clear(0, tk.END)
        listbox.selection_set(idx)
        listbox.see(idx)
        load_preview()

    def on_select(_event=None):
        load_preview()

    listbox.bind("<<ListboxSelect>>", on_select)

    def do_insert():
        self.editor.insert(tk.INSERT, read_template(prof, selected_name()))
        win.destroy()

    def do_load_replace():
        if messagebox.askyesno(
            "Replace editor text",
            "Replace the current editor text with this template?",
            parent=win,
        ):
            self.editor.delete("1.0", tk.END)
            self.editor.insert("1.0", read_template(prof, selected_name()))
            win.destroy()

    def do_save_current():
        name = ask_text(win, "Save template", "Template name:")
        if not name:
            return
        write_template(prof, name, self.editor.get("1.0", tk.END))
        refresh(name)

    def do_set_default():
        self.prefs.setdefault("templates_default", {})[prof] = selected_name()
        save_prefs(self.prefs)
        self.status.set(f"Default template set: {selected_name()}")
        win.destroy()

    def do_open_folder():
        folder = profile_templates_dir(prof)
        try:
            os.startfile(folder)  # type: ignore[attr-defined]
        except Exception:
            messagebox.showinfo("Templates folder", str(folder), parent=win)

    def do_reset_files():
        if not messagebox.askyesno(
            "Reset templates",
            "Delete saved template files for this profile and restore the demo template?",
            parent=win,
        ):
            return
        folder = profile_templates_dir(prof)
        for fp in folder.glob("*.txt"):
            try:
                fp.unlink()
            except Exception:
                pass
        ensure_demo_templates()
        refresh("Blank")
        self.status.set("Templates reset.")

    def do_insert_helper():
        self.editor.insert(tk.INSERT, build_helper_snippet(self.get_profile_info(prof)))
        win.destroy()

    _build_template_action_footer(
        self,
        sf.inner,
        insert_template=do_insert,
        load_replace=do_load_replace,
        close=win.destroy,
    )
    ttk.Label(
        sf.inner,
        text=(
            "Insert keeps your existing text. "
            "Load & replace starts the editor from the template."
        ),
    ).pack(anchor="w", padx=CONTENT_PAD, pady=(0, BUTTON_GAP))

    adv_var = tk.BooleanVar(value=False)
    adv_panel = _build_advanced_template_panel(
        sf.inner,
        adv_var,
        save_current=do_save_current,
        set_default=do_set_default,
        open_folder=do_open_folder,
        reset_files=do_reset_files,
        insert_helper=do_insert_helper,
    )

    def sync_adv(*_):
        if adv_var.get():
            adv_panel.pack(fill="x", padx=CONTENT_PAD, pady=(0, CONTENT_PAD))
        else:
            adv_panel.pack_forget()

    adv_var.trace_add("write", sync_adv)
    sync_adv()
    refresh()


def _build_template_action_footer(
    app,
    parent,
    *,
    insert_template,
    load_replace,
    close,
) -> None:
    footer = build_dialog_footer(app, parent, pady=(0, BUTTON_GAP))
    ttk.Label(footer, text="Apply template to editor:").pack(side="left")
    ttk.Button(footer, text="Insert", command=insert_template).pack(
        side="left", padx=(PANEL_GAP, 0), pady=PANEL_GAP
    )
    ttk.Button(footer, text="Load & replace", command=load_replace).pack(
        side="left", padx=(BUTTON_GAP, 0), pady=PANEL_GAP
    )
    ttk.Button(footer, text="Close", command=close).pack(
        side="right", padx=CONTENT_PAD, pady=PANEL_GAP
    )


def _build_advanced_template_panel(
    parent,
    advanced_visible: tk.BooleanVar,
    *,
    save_current,
    set_default,
    open_folder,
    reset_files,
    insert_helper,
) -> ttk.LabelFrame:
    ttk.Checkbutton(
        parent,
        text="Show advanced options",
        variable=advanced_visible,
    ).pack(anchor="w", padx=CONTENT_PAD, pady=(0, 6))

    panel = ttk.LabelFrame(parent, text="Advanced (template management)")
    for column in range(3):
        panel.columnconfigure(column, weight=1, uniform="advanced_template_actions")
    _grid_advanced_button(panel, "Save editor as template", save_current, 0, 0)
    _grid_advanced_button(panel, "Set as default", set_default, 0, 1)
    _grid_advanced_button(panel, "Open template folder", open_folder, 0, 2)
    _grid_advanced_button(
        panel,
        "Reset templates",
        reset_files,
        1,
        0,
        style="Danger.TButton",
    )
    _grid_advanced_button(panel, "Insert helper snippet", insert_helper, 1, 1)
    ttk.Label(
        panel,
        text="Advanced is optional. Most users only need Insert / Load.",
    ).grid(
        row=2,
        column=0,
        columnspan=3,
        sticky="w",
        padx=PANEL_GAP,
        pady=(0, PANEL_GAP),
    )
    return panel


def _grid_advanced_button(
    parent,
    text: str,
    command,
    row: int,
    column: int,
    *,
    style: str | None = None,
) -> None:
    options = {"text": text, "command": command}
    if style is not None:
        options["style"] = style
    ttk.Button(parent, **options).grid(
        row=row,
        column=column,
        sticky="ew",
        padx=(PANEL_GAP if column == 0 else BUTTON_GAP, PANEL_GAP),
        pady=(PANEL_GAP if row == 0 else 0, BUTTON_GAP),
    )

