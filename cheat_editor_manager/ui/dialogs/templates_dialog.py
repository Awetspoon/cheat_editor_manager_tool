from __future__ import annotations

import tkinter as tk
from typing import Optional

from tkinter import messagebox, ttk

from ...storage import delete_template, list_templates, read_template, write_template
from ...ui.style import CONTROL_GAP, PANEL_GAP, PANEL_INNER_PAD_X
from ...ui.widgets import (
    AutoScrollbar,
    configure_listbox_theme,
    configure_text_theme,
)
from .dialog_utils import (
    bind_dialog_shortcuts,
    build_dialog_footer,
    build_dialog_header,
    configure_dialog_window,
)


TEMPLATES_DIALOG_GEOMETRY = "720x500"
ADD_TEMPLATE_DIALOG_GEOMETRY = "680x460"
CONTENT_PAD = PANEL_INNER_PAD_X
BUTTON_GAP = CONTROL_GAP
TEMPLATE_LIST_WIDTH = 26
TEMPLATE_LIST_ROWS = 10
TEMPLATE_PREVIEW_ROWS = 11


def open_templates(app):
    self = app

    win = tk.Toplevel(self.root)
    configure_dialog_window(self, win, "Templates", TEMPLATES_DIALOG_GEOMETRY)
    try:
        win.minsize(660, 430)
    except Exception:
        pass

    build_dialog_header(
        self,
        win,
        "Templates",
        "Reusable saved cheat text. Templates are not tied to the selected target.",
    )

    content = ttk.Frame(win)
    content.pack(fill="both", expand=True, padx=CONTENT_PAD, pady=(0, PANEL_GAP))
    content.columnconfigure(0, weight=1)
    content.rowconfigure(0, weight=1)

    body = ttk.Frame(content)
    body.grid(row=0, column=0, sticky="nsew")
    body.columnconfigure(1, weight=1)
    body.rowconfigure(0, weight=1)

    list_frame = ttk.Frame(body)
    list_frame.grid(row=0, column=0, sticky="nsw")
    ttk.Label(list_frame, text="Saved templates").pack(anchor="w", pady=(0, 6))
    listbox_frame = ttk.Frame(list_frame)
    listbox_frame.pack(fill="both", expand=True)
    listbox = tk.Listbox(
        listbox_frame,
        height=TEMPLATE_LIST_ROWS,
        width=TEMPLATE_LIST_WIDTH,
        activestyle="none",
        exportselection=False,
    )
    configure_listbox_theme(listbox, self)
    listbox.pack(side="left", fill="both", expand=True)
    list_vsb = AutoScrollbar(listbox_frame, orient="vertical", command=listbox.yview)
    listbox.configure(yscrollcommand=list_vsb.set)
    list_vsb.pack(side="left", fill="y")

    preview_frame = ttk.Frame(body)
    preview_frame.grid(row=0, column=1, sticky="nsew", padx=(CONTENT_PAD, 0))
    preview_frame.columnconfigure(0, weight=1)
    preview_frame.rowconfigure(1, weight=1)
    ttk.Label(preview_frame, text="Preview").grid(
        row=0, column=0, sticky="w", pady=(0, 6)
    )
    preview = tk.Text(preview_frame, wrap="word", height=TEMPLATE_PREVIEW_ROWS)
    configure_text_theme(preview, self, editor=True)
    preview.grid(row=1, column=0, sticky="nsew")
    p_vsb = AutoScrollbar(preview_frame, orient="vertical", command=preview.yview)
    preview.configure(yscrollcommand=p_vsb.set)
    p_vsb.grid(row=1, column=1, sticky="ns")
    preview.configure(state="disabled")

    selected = tk.StringVar(value="Blank")
    delete_button: ttk.Button | None = None

    def selected_name() -> str:
        sel = listbox.curselection()
        if sel:
            return listbox.get(sel[0])
        return selected.get() or "Blank"

    def sync_delete_button() -> None:
        if delete_button is None:
            return
        state = "disabled" if selected_name() == "Blank" else "normal"
        delete_button.configure(state=state)

    def load_preview():
        name = selected_name()
        selected.set(name)
        preview.configure(state="normal")
        preview.delete("1.0", tk.END)
        preview.insert("1.0", read_template(name))
        preview.configure(state="disabled")
        sync_delete_button()

    def refresh(selected_name_override: Optional[str] = None):
        names = list_templates()
        listbox.delete(0, tk.END)
        for name in names:
            listbox.insert(tk.END, name)

        target = selected_name_override or selected.get() or "Blank"
        if target not in names:
            target = names[0]
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
        self.editor.insert(tk.INSERT, read_template(selected_name()))
        self.status.set(f"Template inserted: {selected_name()}")
        win.destroy()

    def do_load_replace():
        if messagebox.askyesno(
            "Replace editor text",
            "Replace the current editor text with this template?",
            parent=win,
        ):
            self.editor.delete("1.0", tk.END)
            self.editor.insert("1.0", read_template(selected_name()))
            self.status.set(f"Template loaded: {selected_name()}")
            win.destroy()

    def do_add_template():
        result = _open_add_template_dialog(
            self,
            win,
            initial_text=self.editor.get("1.0", "end-1c"),
            template_names=list_templates(),
        )
        if result is None:
            return
        name, content = result
        write_template(name, content)
        self.status.set(f"Template saved: {name}")
        refresh(name)

    def do_delete_template():
        name = selected_name()
        if name.strip().casefold() == "blank":
            sync_delete_button()
            return
        if not messagebox.askyesno(
            "Delete template",
            f"Delete the saved template '{name}'?",
            parent=win,
        ):
            return
        if delete_template(name):
            self.status.set(f"Template deleted: {name}")
        else:
            messagebox.showinfo(
                "Templates",
                f"The saved template '{name}' was not found.",
                parent=win,
            )
        refresh("Blank")

    delete_button = _build_template_action_footer(
        self,
        win,
        insert_template=do_insert,
        load_replace=do_load_replace,
        add_template=do_add_template,
        delete_template_action=do_delete_template,
        close=win.destroy,
    )
    refresh()


def _build_template_action_footer(
    app,
    parent,
    *,
    insert_template,
    load_replace,
    add_template,
    delete_template_action,
    close,
) -> ttk.Button:
    footer = build_dialog_footer(app, parent, pady=(0, CONTENT_PAD))
    ttk.Button(footer, text="Use Template", command=insert_template).pack(
        side="left", padx=(CONTENT_PAD, 0), pady=PANEL_GAP
    )
    ttk.Button(footer, text="Replace Editor", command=load_replace).pack(
        side="left", padx=(BUTTON_GAP, 0), pady=PANEL_GAP
    )
    ttk.Button(footer, text="Add Template", command=add_template).pack(
        side="left", padx=(BUTTON_GAP, 0), pady=PANEL_GAP
    )
    delete_button = ttk.Button(
        footer,
        text="Delete Template",
        command=delete_template_action,
        style="Danger.TButton",
    )
    delete_button.pack(side="left", padx=(BUTTON_GAP, 0), pady=PANEL_GAP)
    ttk.Button(footer, text="Close", command=close).pack(
        side="right", padx=CONTENT_PAD, pady=PANEL_GAP
    )
    return delete_button


def _open_add_template_dialog(
    app,
    parent: tk.Toplevel,
    *,
    initial_text: str,
    template_names: list[str],
) -> Optional[tuple[str, str]]:
    window = tk.Toplevel(parent)
    configure_dialog_window(
        app,
        window,
        "Add Template",
        ADD_TEMPLATE_DIALOG_GEOMETRY,
        parent=parent,
    )
    try:
        window.minsize(620, 420)
    except Exception:
        pass

    build_dialog_header(
        app,
        window,
        "Add Template",
        "Save reusable text that can be inserted into any target.",
    )

    body = ttk.Frame(window)
    body.pack(fill="both", expand=True, padx=CONTENT_PAD, pady=(0, PANEL_GAP))
    body.columnconfigure(0, weight=1)
    body.rowconfigure(3, weight=1)

    ttk.Label(body, text="Template name").grid(row=0, column=0, sticky="w")
    name_var = tk.StringVar()
    name_entry = ttk.Entry(body, textvariable=name_var)
    name_entry.grid(row=1, column=0, sticky="ew", pady=(CONTROL_GAP, PANEL_GAP))

    ttk.Label(body, text="Template text").grid(row=2, column=0, sticky="w")
    text_frame = ttk.Frame(body)
    text_frame.grid(row=3, column=0, sticky="nsew", pady=(CONTROL_GAP, 0))
    text_frame.columnconfigure(0, weight=1)
    text_frame.rowconfigure(0, weight=1)

    template_text = tk.Text(text_frame, wrap="word", height=12, undo=True)
    configure_text_theme(template_text, app, editor=True)
    template_text.grid(row=0, column=0, sticky="nsew")
    text_vsb = AutoScrollbar(text_frame, orient="vertical", command=template_text.yview)
    template_text.configure(yscrollcommand=text_vsb.set)
    text_vsb.grid(row=0, column=1, sticky="ns")
    template_text.insert("1.0", initial_text)

    existing_by_case = {
        item.strip().casefold(): item
        for item in template_names
        if item and item.strip().casefold() != "blank"
    }
    output: dict[str, Optional[tuple[str, str]]] = {"value": None}

    def save() -> None:
        name = name_var.get().strip()
        if not name:
            messagebox.showerror(
                "Templates",
                "Enter a template name before saving.",
                parent=window,
            )
            name_entry.focus_set()
            return
        if name.casefold() == "blank":
            messagebox.showerror(
                "Templates",
                "Blank is built in. Please choose a different template name.",
                parent=window,
            )
            name_entry.focus_set()
            name_entry.selection_range(0, tk.END)
            return

        existing = existing_by_case.get(name.casefold())
        if existing and not messagebox.askyesno(
            "Replace template",
            f"Replace the saved template '{existing}'?",
            parent=window,
        ):
            return

        output["value"] = (
            existing or name,
            template_text.get("1.0", "end-1c"),
        )
        window.destroy()

    def cancel() -> None:
        output["value"] = None
        window.destroy()

    footer = build_dialog_footer(app, window, pady=(0, CONTENT_PAD))
    ttk.Button(footer, text="Cancel", command=cancel).pack(
        side="right",
        padx=(BUTTON_GAP, CONTENT_PAD),
        pady=PANEL_GAP,
    )
    ttk.Button(footer, text="Save Template", command=save).pack(
        side="right",
        pady=PANEL_GAP,
    )

    bind_dialog_shortcuts(window, cancel=cancel)
    window.bind("<Control-s>", lambda _event: save(), add="+")
    window.bind("<Control-S>", lambda _event: save(), add="+")
    name_entry.focus_set()
    window.wait_window()
    return output["value"]
