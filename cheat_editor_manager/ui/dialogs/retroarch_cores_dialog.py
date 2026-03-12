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


def save_retroarch_core(app):
    self = app
    self.prefs["retroarch_core"] = self.core_var.get()
    save_prefs(self.prefs)
    try:
        self.refresh_profile_info()
    except Exception:
        pass

def audit_retroarch_cores(app):
    self = app
    """De-dupe and normalize RetroArch core list."""
    try:
        cores = list(self.prefs.get("retroarch_cores") or [])
        cleaned = []
        seen = set()
        for c in cores:
            c = (c or "").strip()
            if not c:
                continue
            key = c.casefold()
            if key in seen:
                continue
            seen.add(key)
            cleaned.append(c)

        default_name = "Default (no subfolder)"
        cleaned = [c for c in cleaned if c.casefold() != default_name.casefold()]
        cleaned.insert(0, default_name)

        self.prefs["retroarch_cores"] = cleaned
        cur = (self.prefs.get("retroarch_core") or "").strip()
        if not cur or cur.casefold() not in {c.casefold() for c in cleaned}:
            self.prefs["retroarch_core"] = default_name
        save_prefs(self.prefs)
    except Exception:
        pass

def sync_core_dropdown(app):
    self = app
    cores = list(self.prefs.get("retroarch_cores") or DEFAULT_RETROARCH_CORES)
    if not cores:
        cores = list(DEFAULT_RETROARCH_CORES)
        self.prefs["retroarch_cores"] = cores
    current = (self.prefs.get("retroarch_core") or "").strip()
    if not current or current.casefold() not in {c.casefold() for c in cores}:
        current = cores[0]
        self.prefs["retroarch_core"] = current
    self.core_var.set(current)
    try:
        self._core_cb.configure(values=cores)
    except Exception:
        pass

def manage_retroarch_cores(app):
    self = app
    win = tk.Toplevel(self.root)
    win.title("RetroArch cores")
    win.geometry("640x460")
    win.transient(self.root)
    win.grab_set()

    ttk.Label(
        win,
        text="Cores control the subfolder under cheats/. RetroArch is multi-platform.",
        wraplength=580,
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

    default_name = "Default (no subfolder)"

    def refresh(selected_name: Optional[str] = None):
        lb.delete(0, tk.END)
        for item in self.prefs.get("retroarch_cores", []):
            lb.insert(tk.END, item)
        target = selected_name or self.core_var.get() or default_name
        names = list(self.prefs.get("retroarch_cores", []))
        for idx, item in enumerate(names):
            if item.casefold() == target.casefold():
                lb.selection_clear(0, tk.END)
                lb.selection_set(idx)
                lb.see(idx)
                break

    def selected() -> Optional[str]:
        sel = lb.curselection()
        return lb.get(sel[0]) if sel else None

    def commit(cores: List[str], selected_name: Optional[str] = None):
        self.prefs["retroarch_cores"] = cores
        self._audit_retroarch_cores()
        self._sync_core_dropdown()
        save_prefs(self.prefs)
        refresh(selected_name)
        self.refresh_profile_info()

    def add():
        name = ask_text(win, "Add core", "Core name (folder name):")
        if not name:
            return
        cores = list(self.prefs.get("retroarch_cores") or [])
        if name.casefold() not in {c.casefold() for c in cores}:
            cores.append(name)
        commit(cores, name)

    def edit():
        current = selected()
        if not current:
            return
        if current.casefold() == default_name.casefold():
            messagebox.showinfo("RetroArch cores", "The default entry stays fixed.", parent=win)
            return
        name = ask_text(win, "Edit core", f"New name (current: {current}):")
        if not name:
            return
        cores = list(self.prefs.get("retroarch_cores") or [])
        for idx, item in enumerate(cores):
            if item.casefold() == current.casefold():
                cores[idx] = name
                break
        if (self.prefs.get("retroarch_core") or "").casefold() == current.casefold():
            self.prefs["retroarch_core"] = name
        commit(cores, name)

    def remove():
        current = selected()
        if not current:
            return
        if current.casefold() == default_name.casefold():
            messagebox.showinfo("RetroArch cores", "The default entry stays fixed.", parent=win)
            return
        if not messagebox.askyesno("Remove core", f"Remove '{current}' from the core list?", parent=win):
            return
        cores = [item for item in (self.prefs.get("retroarch_cores") or []) if item.casefold() != current.casefold()]
        if (self.prefs.get("retroarch_core") or "").casefold() == current.casefold():
            self.prefs["retroarch_core"] = default_name
        commit(cores, default_name)

    ttk.Button(btns, text="Add...", command=add).pack(fill="x", pady=(0, 6))
    ttk.Button(btns, text="Edit...", command=edit).pack(fill="x", pady=(0, 6))
    ttk.Button(btns, text="Remove", command=remove).pack(fill="x", pady=(0, 6))
    ttk.Button(btns, text="Close", command=win.destroy).pack(fill="x", pady=(18, 0))

    refresh()
