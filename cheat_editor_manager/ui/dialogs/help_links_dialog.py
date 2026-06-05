from __future__ import annotations

import tkinter as tk
import webbrowser
from typing import Optional

from tkinter import messagebox, ttk

from ...services import help_link_service
from ...storage import save_prefs
from .dialog_utils import (
    bind_dialog_shortcuts,
    build_dialog_footer,
    build_dialog_header,
    build_dialog_list_with_sidebar,
    configure_dialog_window,
    pack_sidebar_button,
)


LINK_DIALOG_GEOMETRY = "500x265"


def open_help_links(app):
    self = app
    win = tk.Toplevel(self.root)
    configure_dialog_window(self, win, "Help Links", "760x520")

    build_dialog_header(
        self,
        win,
        "Help Links",
        "Quick shortcuts to cheat references and documentation.",
    )

    lb, btns = build_dialog_list_with_sidebar(self, win)

    def selected_index() -> Optional[int]:
        sel = lb.curselection()
        return int(sel[0]) if sel else None

    def refresh(index: Optional[int] = None):
        lb.delete(0, tk.END)
        for item in help_link_service.normalize_links(self.prefs.get("help_links", [])):
            lb.insert(tk.END, help_link_service.display_name(item))
        if index is not None and 0 <= index < lb.size():
            lb.selection_set(index)
            lb.see(index)

    def prompt_link(existing: Optional[dict] = None) -> Optional[dict]:
        dlg = tk.Toplevel(win)
        title = "Edit Link" if existing else "Add Link"
        configure_dialog_window(
            self,
            dlg,
            title,
            LINK_DIALOG_GEOMETRY,
            parent=win,
            resizable=False,
        )
        build_dialog_header(
            self,
            dlg,
            title,
            "Save a clean name and web address for the Help Links list.",
        )
        frm = ttk.Frame(dlg)
        frm.pack(fill="both", expand=True, padx=12, pady=(0, 10))
        frm.columnconfigure(1, weight=1)

        name_var = tk.StringVar(value=(existing or {}).get("name", ""))
        url_var = tk.StringVar(value=(existing or {}).get("url", ""))

        ttk.Label(frm, text="Name").grid(row=0, column=0, sticky="w", pady=(0, 6))
        name_entry = ttk.Entry(frm, textvariable=name_var, width=46)
        name_entry.grid(
            row=0, column=1, sticky="ew", pady=(0, 6)
        )
        ttk.Label(frm, text="URL").grid(row=1, column=0, sticky="w", pady=(0, 10))
        ttk.Entry(frm, textvariable=url_var, width=46).grid(
            row=1, column=1, sticky="ew", pady=(0, 10)
        )

        out = {"value": None}

        def ok():
            name = name_var.get().strip()
            url = url_var.get().strip()
            if not name or not url:
                messagebox.showerror(
                    "Help Links",
                    "Both name and URL are required.",
                    parent=dlg,
                )
                return
            out["value"] = {"name": name, "url": url}
            dlg.destroy()

        footer = build_dialog_footer(self, dlg, pady=(0, 12))
        ttk.Button(footer, text="Cancel", command=dlg.destroy).pack(
            side="right", padx=(8, 12), pady=10
        )
        ttk.Button(footer, text="Save", command=ok).pack(side="right", pady=10)
        bind_dialog_shortcuts(dlg, confirm=ok, cancel=dlg.destroy)
        name_entry.focus_set()
        dlg.wait_window()
        return out["value"]

    def open_link():
        idx = selected_index()
        if idx is None:
            return
        links = help_link_service.normalize_links(self.prefs.get("help_links"))
        if idx >= len(links):
            return
        url = links[idx].get("url", "")
        if url:
            webbrowser.open(url)

    def add_link():
        item = prompt_link()
        if not item:
            return
        links = help_link_service.add_link(self.prefs.get("help_links"), item)
        self.prefs["help_links"] = links
        save_prefs(self.prefs)
        refresh(len(links) - 1)

    def edit_link():
        idx = selected_index()
        if idx is None:
            return
        links = help_link_service.normalize_links(self.prefs.get("help_links"))
        if idx >= len(links):
            return
        item = prompt_link(links[idx])
        if not item:
            return
        links = help_link_service.replace_link(links, idx, item)
        self.prefs["help_links"] = links
        save_prefs(self.prefs)
        refresh(idx)

    def delete_link():
        idx = selected_index()
        if idx is None:
            return
        links = help_link_service.normalize_links(self.prefs.get("help_links"))
        if idx >= len(links):
            return
        name = help_link_service.display_name(links[idx])
        if not messagebox.askyesno("Delete Link", f"Delete '{name}'?", parent=win):
            return
        links = help_link_service.delete_link(links, idx)
        self.prefs["help_links"] = links
        save_prefs(self.prefs)
        refresh(max(idx - 1, 0))

    def move(delta: int):
        idx = selected_index()
        if idx is None:
            return
        links, new_idx = help_link_service.move_link(
            self.prefs.get("help_links"), idx, delta
        )
        if new_idx == idx:
            return
        self.prefs["help_links"] = links
        save_prefs(self.prefs)
        refresh(new_idx)

    def reset_links():
        if not messagebox.askyesno(
            "Reset Links", "Restore the default help links?", parent=win
        ):
            return
        self.prefs["help_links"] = help_link_service.default_links()
        save_prefs(self.prefs)
        refresh(0)

    pack_sidebar_button(btns, text="Open", command=open_link)
    pack_sidebar_button(btns, text="Add...", command=add_link)
    pack_sidebar_button(btns, text="Edit...", command=edit_link)
    pack_sidebar_button(btns, text="Delete", command=delete_link)
    pack_sidebar_button(
        btns,
        text="Move Up",
        command=lambda: move(-1),
        pady=(18, 6),
    )
    pack_sidebar_button(btns, text="Move Down", command=lambda: move(1))
    pack_sidebar_button(btns, text="Reset", command=reset_links, pady=(18, 6))
    pack_sidebar_button(btns, text="Close", command=win.destroy, pady=(18, 0))

    refresh(0)
