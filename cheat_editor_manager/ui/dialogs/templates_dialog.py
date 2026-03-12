from __future__ import annotations

import os
import tkinter as tk
from typing import Optional

from tkinter import messagebox, ttk

from ...export_logic import profile_id_label
from ...storage import (
    ensure_demo_templates,
    list_templates,
    profile_templates_dir,
    read_template,
    save_prefs,
    write_template,
)
from ...widgets import Scrollable, ask_text

def open_templates(app):
    self = app
    prof = self.profile_var.get()
    if not prof:
        messagebox.showerror("Templates", "Select a profile before opening templates.")
        return

    win = tk.Toplevel(self.root)
    win.title(f"Templates - {prof}")
    win.geometry("860x620")
    win.transient(self.root)
    win.grab_set()

    sf = Scrollable(win)
    sf.pack(fill="both", expand=True)
    sf.set_canvas_bg(self.effective_colors()["bg"])

    ttk.Label(sf.inner, text="Templates", font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=12, pady=(12, 6))
    ttk.Label(sf.inner, text=f"Profile: {prof}").pack(anchor="w", padx=12, pady=(0, 10))

    body = ttk.Frame(sf.inner)
    body.pack(fill="both", expand=True, padx=12, pady=(0, 10))
    body.columnconfigure(1, weight=1)
    body.rowconfigure(0, weight=1)

    list_frame = ttk.Frame(body)
    list_frame.grid(row=0, column=0, sticky="nsw")
    listbox = tk.Listbox(list_frame, height=14, width=34, activestyle="none")
    listbox.pack(side="left", fill="y")
    list_vsb = ttk.Scrollbar(list_frame, orient="vertical", command=listbox.yview)
    listbox.configure(yscrollcommand=list_vsb.set)
    list_vsb.pack(side="left", fill="y")

    preview_frame = ttk.Frame(body)
    preview_frame.grid(row=0, column=1, sticky="nsew", padx=(12, 0))
    preview_frame.columnconfigure(0, weight=1)
    preview_frame.rowconfigure(1, weight=1)
    ttk.Label(preview_frame, text="Template preview:").grid(row=0, column=0, sticky="w", pady=(0, 6))
    preview = tk.Text(preview_frame, wrap="word", height=18)
    preview.grid(row=1, column=0, sticky="nsew")
    p_vsb = ttk.Scrollbar(preview_frame, orient="vertical", command=preview.yview)
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
        info = self.get_profile_info(prof)
        kind = info.get("kind", "generic")
        if kind == "switch":
            snippet = (
                "# Switch helper\n"
                "# TitleID stays the same.\n"
                "# BuildID changes with updates.\n"
                "# You can enter multiple BIDs separated by commas.\n"
                "# Atmosphere path: atmosphere/contents/<TID>/cheats/<BID>.txt\n\n"
            )
        elif kind in {"titleid", "idfile"}:
            snippet = (
                f"# ID-based helper\n"
                f"# Use the {profile_id_label(info)} this target expects.\n"
                "# Quick Export builds the filename or plugin folder from that ID.\n"
            )
            if info.get("citra_enabled"):
                snippet += "*citra_enabled\n\n"
            else:
                snippet += "\n"
        elif kind == "retroarch":
            snippet = (
                "# RetroArch helper (multi-platform)\n"
                "# Path: RetroArch/cheats/<Core Name>/<Game>.cht\n"
                "# Pick your core in the Helper panel.\n\n"
            )
        else:
            snippet = "# Helper snippet\n# Safe starting structure for this emulator.\n\n"
        self.editor.insert(tk.INSERT, snippet)
        win.destroy()

    ttk.Separator(sf.inner).pack(fill="x", padx=12, pady=(0, 10))
    br = ttk.Frame(sf.inner)
    br.pack(fill="x", padx=12, pady=(0, 6))
    ttk.Label(br, text="Apply template to editor:").pack(side="left")
    ttk.Button(br, text="Insert", command=do_insert).pack(side="left", padx=(10, 0))
    ttk.Button(br, text="Load & replace", command=do_load_replace).pack(side="left", padx=(8, 0))
    ttk.Button(br, text="Close", command=win.destroy).pack(side="right")
    ttk.Label(
        sf.inner,
        text="Insert keeps your existing text. Load & replace starts the editor from the template.",
    ).pack(anchor="w", padx=12, pady=(0, 8))

    adv_var = tk.BooleanVar(value=False)
    ttk.Checkbutton(sf.inner, text="Show advanced options", variable=adv_var).pack(anchor="w", padx=12, pady=(0, 6))
    adv_panel = ttk.LabelFrame(sf.inner, text="Advanced (template management)")
    adv_row = ttk.Frame(adv_panel)
    adv_row.pack(fill="x", padx=10, pady=10)
    ttk.Button(adv_row, text="Save editor as template", command=do_save_current).pack(side="left")
    ttk.Button(adv_row, text="Set as default", command=do_set_default).pack(side="left", padx=(8, 0))
    ttk.Button(adv_row, text="Open template folder", command=do_open_folder).pack(side="left", padx=(8, 0))
    ttk.Button(adv_row, text="Reset templates (files)", style="Danger.TButton", command=do_reset_files).pack(side="left", padx=(8, 0))
    ttk.Button(adv_row, text="Insert helper snippet", command=do_insert_helper).pack(side="left", padx=(8, 0))
    ttk.Label(adv_panel, text="Advanced is optional. Most users only need Insert / Load.").pack(anchor="w", padx=10, pady=(0, 10))

    def sync_adv(*_):
        if adv_var.get():
            adv_panel.pack(fill="x", padx=12, pady=(0, 12))
        else:
            adv_panel.pack_forget()

    adv_var.trace_add("write", sync_adv)
    sync_adv()
    refresh()

