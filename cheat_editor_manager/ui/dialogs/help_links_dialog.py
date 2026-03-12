from __future__ import annotations

import os
import re
import tkinter as tk
import tkinter.font as tkfont
import webbrowser
from pathlib import Path
from typing import Optional

from tkinter import colorchooser, filedialog, messagebox, ttk

from ...constants import APP_DIR, DEFAULT_RETROARCH_CORES
from ...export_logic import build_export_plan as build_export_plan_for_state, clean_hex as _clean_hex, extract_switch_metadata, normalize_bids, normalize_profile_id, prepare_export_text, profile_id_label, split_bids, validate_export_inputs
from ...resources import asset_path
from ...storage import ensure_demo_templates, list_templates, load_prefs, profile_templates_dir, read_template, save_prefs, write_template
from ...widgets import ToolTip, ask_text


def open_help_links(app):
    self = app
    win = tk.Toplevel(self.root)
    win.title("Help Links")
    win.geometry("760x520")
    win.transient(self.root)
    win.grab_set()

    ttk.Label(
        win,
        text="Help links are quick shortcuts to cheat references and docs.",
        wraplength=700,
    ).pack(anchor="w", padx=12, pady=(12, 8))

    body = ttk.Frame(win)
    body.pack(fill="both", expand=True, padx=12, pady=(0, 12))
    body.columnconfigure(0, weight=1)
    body.rowconfigure(0, weight=1)

    list_frame = ttk.Frame(body)
    list_frame.grid(row=0, column=0, sticky="nsew")
    list_frame.columnconfigure(0, weight=1)
    list_frame.rowconfigure(0, weight=1)

    lb = tk.Listbox(list_frame, activestyle="none", height=14)
    vsb = ttk.Scrollbar(list_frame, orient="vertical", command=lb.yview)
    lb.configure(yscrollcommand=vsb.set)
    lb.grid(row=0, column=0, sticky="nsew")
    vsb.grid(row=0, column=1, sticky="ns")

    btns = ttk.Frame(body)
    btns.grid(row=0, column=1, sticky="ns", padx=(10, 0))

    def selected_index() -> Optional[int]:
        sel = lb.curselection()
        return int(sel[0]) if sel else None

    def refresh(index: Optional[int] = None):
        lb.delete(0, tk.END)
        for item in self.prefs.get("help_links", []):
            lb.insert(tk.END, item.get("name") or item.get("url") or "Link")
        if index is not None and 0 <= index < lb.size():
            lb.selection_set(index)
            lb.see(index)

    def prompt_link(existing: Optional[dict] = None) -> Optional[dict]:
        dlg = tk.Toplevel(win)
        dlg.title("Edit Link" if existing else "Add Link")
        dlg.transient(win)
        dlg.grab_set()
        dlg.resizable(False, False)
        frm = ttk.Frame(dlg)
        frm.pack(fill="both", expand=True, padx=12, pady=12)
        frm.columnconfigure(1, weight=1)

        name_var = tk.StringVar(value=(existing or {}).get("name", ""))
        url_var = tk.StringVar(value=(existing or {}).get("url", ""))

        ttk.Label(frm, text="Name:").grid(row=0, column=0, sticky="w", pady=(0, 6))
        ttk.Entry(frm, textvariable=name_var, width=46).grid(row=0, column=1, sticky="ew", pady=(0, 6))
        ttk.Label(frm, text="URL:").grid(row=1, column=0, sticky="w", pady=(0, 10))
        ttk.Entry(frm, textvariable=url_var, width=46).grid(row=1, column=1, sticky="ew", pady=(0, 10))

        out = {"value": None}

        def ok():
            name = name_var.get().strip()
            url = url_var.get().strip()
            if not name or not url:
                messagebox.showerror("Help Links", "Both name and URL are required.", parent=dlg)
                return
            out["value"] = {"name": name, "url": url}
            dlg.destroy()

        row = ttk.Frame(frm)
        row.grid(row=2, column=1, sticky="e")
        ttk.Button(row, text="Cancel", command=dlg.destroy).pack(side="right", padx=(8, 0))
        ttk.Button(row, text="Save", command=ok).pack(side="right")
        dlg.wait_window()
        return out["value"]

    def open_link():
        idx = selected_index()
        if idx is None:
            return
        url = (self.prefs.get("help_links") or [])[idx].get("url", "")
        if url:
            webbrowser.open(url)

    def add_link():
        item = prompt_link()
        if not item:
            return
        links = list(self.prefs.get("help_links") or [])
        links.append(item)
        self.prefs["help_links"] = links
        save_prefs(self.prefs)
        refresh(len(links) - 1)

    def edit_link():
        idx = selected_index()
        if idx is None:
            return
        links = list(self.prefs.get("help_links") or [])
        item = prompt_link(links[idx])
        if not item:
            return
        links[idx] = item
        self.prefs["help_links"] = links
        save_prefs(self.prefs)
        refresh(idx)

    def delete_link():
        idx = selected_index()
        if idx is None:
            return
        links = list(self.prefs.get("help_links") or [])
        name = links[idx].get("name") or links[idx].get("url") or "this link"
        if not messagebox.askyesno("Delete Link", f"Delete '{name}'?", parent=win):
            return
        links.pop(idx)
        self.prefs["help_links"] = links
        save_prefs(self.prefs)
        refresh(max(idx - 1, 0))

    def move(delta: int):
        idx = selected_index()
        if idx is None:
            return
        links = list(self.prefs.get("help_links") or [])
        new_idx = idx + delta
        if new_idx < 0 or new_idx >= len(links):
            return
        links[idx], links[new_idx] = links[new_idx], links[idx]
        self.prefs["help_links"] = links
        save_prefs(self.prefs)
        refresh(new_idx)

    def reset_links():
        if not messagebox.askyesno("Reset Links", "Restore the default help links?", parent=win):
            return
        self.prefs["help_links"] = list(DEFAULT_PREFS.get("help_links", []))
        save_prefs(self.prefs)
        refresh(0)

    ttk.Button(btns, text="Open", command=open_link).pack(fill="x", pady=(0, 6))
    ttk.Button(btns, text="Add...", command=add_link).pack(fill="x", pady=(0, 6))
    ttk.Button(btns, text="Edit...", command=edit_link).pack(fill="x", pady=(0, 6))
    ttk.Button(btns, text="Delete", command=delete_link).pack(fill="x", pady=(0, 6))
    ttk.Button(btns, text="Move Up", command=lambda: move(-1)).pack(fill="x", pady=(18, 6))
    ttk.Button(btns, text="Move Down", command=lambda: move(1)).pack(fill="x", pady=(0, 6))
    ttk.Button(btns, text="Reset", command=reset_links).pack(fill="x", pady=(18, 6))
    ttk.Button(btns, text="Close", command=win.destroy).pack(fill="x", pady=(18, 0))

    refresh(0)
