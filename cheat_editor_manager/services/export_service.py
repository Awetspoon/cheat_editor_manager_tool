from __future__ import annotations

import os
import re
import tkinter as tk
import tkinter.font as tkfont
import webbrowser
from pathlib import Path
from typing import Optional

from tkinter import colorchooser, filedialog, messagebox, ttk

from ..constants import APP_DIR, DEFAULT_RETROARCH_CORES
from ..export_logic import build_export_plan as build_export_plan_for_state, clean_hex as _clean_hex, extract_switch_metadata, normalize_bids, normalize_profile_id, prepare_export_text, profile_id_label, split_bids, validate_export_inputs
from ..resources import asset_path
from ..storage import ensure_demo_templates, list_templates, load_prefs, profile_templates_dir, read_template, save_prefs, write_template
from ..widgets import ToolTip, ask_text


def effective_export_root_for_profile(app, prof: str) -> Path:
    self = app
    """Return the export root for a profile.

    Atmosphère safeguard:
      - Atmosphère should never 'mysteriously' export somewhere else because of an override.
      - To keep first-time users safe, Atmosphère always uses the main Export Root (point this at SD root).
    """
    # Atmosphère: ignore per-profile overrides to avoid clashing with the official folder structure.
    if prof.strip() == "Atmosphère (Switch) (CFW)":
        return Path(self.export_var.get() or self.prefs.get("export_root", str(APP_DIR)))

    override = (self.prefs.get("emulator_paths", {}) or {}).get(prof, "").strip()
    if override:
        return Path(override)
    return Path(self.export_var.get() or self.prefs.get("export_root", str(APP_DIR)))

def get_all_known_extensions(app):
    self = app
    """Collect all unique extensions from built-in + custom profiles."""
    exts = set()
    try:
        for name in self.get_profile_values():
            info = self.get_profile_info(name)
            for e in (info.get("extensions") or []):
                if not e:
                    continue
                e = e.strip()
                if not e:
                    continue
                if not e.startswith("."):
                    e = "." + e
                exts.add(e.lower())
    except Exception:
        pass
    # Stable order: common first, then alpha
    preferred = [".txt", ".cht", ".ini", ".pnach", ".yml", ".yaml", ".json", ".xml", ".dat", ".patch.toml"]
    ordered = []
    for p in preferred:
        if p in exts:
            ordered.append(p)
            exts.remove(p)
    ordered.extend(sorted(exts))
    return ordered

def pick_extension_for_save(app, prof: str):
    self = app
    """Modal picker that returns an extension like '.txt' or None if cancelled."""
    info = self.get_profile_info(prof)
    profile_exts = [e.strip() for e in (info.get("extensions") or [".txt"]) if e and e.strip()]
    profile_exts = [(e if e.startswith(".") else "." + e).lower() for e in profile_exts] or [".txt"]
    all_exts = self._get_all_known_extensions()

    dlg = tk.Toplevel(self.root)
    dlg.title("Choose file extension")
    dlg.transient(self.root)
    dlg.grab_set()
    dlg.resizable(False, False)

    pad = ttk.Frame(dlg)
    pad.pack(fill="both", expand=True, padx=12, pady=12)
    ttk.Label(pad, text="Pick an extension before choosing the save location.", font=("Segoe UI", 10, "bold")).pack(anchor="w")
    ttk.Label(pad, text=f"Profile: {prof}",).pack(anchor="w", pady=(4, 10))

    use_all_var = tk.BooleanVar(value=False)
    ext_var = tk.StringVar(value=profile_exts[0])
    custom_var = tk.StringVar(value="")

    row = ttk.Frame(pad); row.pack(fill="x", pady=(0, 8))
    ttk.Label(row, text="Extension:").pack(side="left")
    cb = ttk.Combobox(row, textvariable=ext_var, state="readonly", values=profile_exts, width=14)
    cb.pack(side="left", padx=(8, 0))

    chk = ttk.Checkbutton(pad, text="Show all known extensions (all profiles)", variable=use_all_var)
    chk.pack(anchor="w", pady=(0, 8))

    crow = ttk.Frame(pad); crow.pack(fill="x", pady=(0, 8))
    ttk.Label(crow, text="Or type custom:").pack(side="left")
    cent = ttk.Entry(crow, textvariable=custom_var, width=14)
    cent.pack(side="left", padx=(8, 0))
    ttk.Label(crow, text="(example: .txt)").pack(side="left", padx=(8, 0))

    hint = ttk.Label(pad, text="If you're unsure, use the extension shown in Helper.",)
    hint.pack(anchor="w", pady=(6, 10))

    out = {"ext": None}

    def sync_lists(*_):
        vals = all_exts if use_all_var.get() else profile_exts
        cb.configure(values=vals)
        if ext_var.get() not in vals:
            ext_var.set(vals[0] if vals else ".txt")

    def ok():
        c = custom_var.get().strip()
        if c:
            if not c.startswith("."):
                c = "." + c
            out["ext"] = c.lower()
        else:
            out["ext"] = (ext_var.get() or ".txt").lower()
        dlg.destroy()

    def cancel():
        out["ext"] = None
        dlg.destroy()

    use_all_var.trace_add("write", sync_lists)
    sync_lists()

    brow = ttk.Frame(pad); brow.pack(fill="x", pady=(10, 0))
    ttk.Button(brow, text="Cancel", command=cancel).pack(side="right")
    ttk.Button(brow, text="Continue…", command=ok).pack(side="right", padx=(0, 8))

    dlg.wait_window()
    return out["ext"]

def convert_save(app):
    self = app
    prof = self.profile_var.get()
    ext = self._pick_extension_for_save(prof)
    if not ext:
        return

    # Build filetypes list for the save dialog
    info = self.get_profile_info(prof)
    prof_exts = [e.strip() for e in (info.get("extensions") or []) if e and e.strip()]
    prof_exts = [(e if e.startswith(".") else "." + e).lower() for e in prof_exts]
    all_exts = self._get_all_known_extensions()

    # If chosen ext isn't in profile list, still allow it
    if ext not in prof_exts and ext not in all_exts:
        all_exts = [ext] + all_exts

    # Show the most relevant list first
    primary_list = prof_exts if ext in prof_exts else all_exts
    patterns = " ".join([f"*{e}" for e in primary_list]) if primary_list else f"*{ext}"

    filetypes = [
        ("Cheat files", patterns),
        (f"Selected (*{ext})", f"*{ext}"),
        ("All files", "*.*"),
    ]

    path = filedialog.asksaveasfilename(defaultextension=ext, filetypes=filetypes)
    if not path:
        return
    Path(path).write_text(self.editor.get("1.0", tk.END), encoding="utf-8")
    self.status.set(f"Saved: {path}")

def validate_export_inputs_for_profile(app, prof: str) -> Optional[str]:
    self = app
    return validate_export_inputs(
        self.get_profile_info(prof),
        self.tid_var.get(),
        self.bid_var.get(),
        self.editor.get("1.0", "end"),
    )

def build_export_plan_from_app(app, prof: str) -> dict:
    self = app
    return build_export_plan_for_state(
        prof=prof,
        info=self.get_profile_info(prof),
        root=self._effective_export_root_for_profile(prof),
        tid=self.tid_var.get(),
        bid_text=self.bid_var.get(),
        core=self.core_var.get(),
        editor_text=self.editor.get("1.0", "end"),
    )

def schedule_export_preview_update(app, *_):
    self = app
    """Debounced export preview update (avoids heavy recompute on every keystroke)."""
    try:
        if getattr(self, "_preview_after", None):
            try:
                self.root.after_cancel(self._preview_after)
            except Exception:
                pass
        self._preview_after = self.root.after(160, self.update_export_preview)
    except Exception:
        pass

def on_editor_modified(app, *_):
    self = app
    try:
        if self.editor.edit_modified():
            self.editor.edit_modified(False)
            self._schedule_export_preview_update()
    except Exception:
        pass

def update_export_preview(app):
    self = app
    """Update the Helper preview line to show the resolved export output path(s)."""
    prof = self.profile_var.get()
    if not prof:
        try:
            self.path_preview.set("")
        except Exception:
            pass
        return

    try:
        info = self.get_profile_info(prof)
        plan = self.build_export_plan(prof)
        files = plan.get("files") or []
        out_dir = plan.get("out_dir")
        kind = plan.get("kind", "generic")

        # Basic validation hints (non-blocking)
        tid = (self.tid_var.get() or "").strip()
        bid_raw = (self.bid_var.get() or "").strip()

        def _is_placeholder(val: str) -> bool:
            v = val.strip()
            return v.startswith("<") and v.endswith(">")

        missing_bits = []
        if kind == "switch":
            if (not tid) or _is_placeholder(tid) or len(_clean_hex(tid)) != 16:
                missing_bits.append("TID")
            if not bid_raw:
                missing_bits.append("BID")
            else:
                bad_bids = [_clean_hex(b) for b in self._split_bids(bid_raw)]
                bad_bids = [b for b in bad_bids if b]
                if not bad_bids or any(len(b) not in (16, 32) for b in bad_bids):
                    self.path_preview.set("Export preview: each BID must be 16 or 32 hex characters.")
                    return
        elif kind == "titleid":
            if (not tid) or _is_placeholder(tid) or len(_clean_hex(tid)) != 16:
                missing_bits.append("TitleID / Game ID")
        elif kind == "idfile":
            normalized_id = normalize_profile_id(info, tid)
            id_regex = str(info.get("id_regex") or "").strip()
            if (not tid) or _is_placeholder(tid) or not normalized_id or (id_regex and not re.fullmatch(id_regex, normalized_id)):
                missing_bits.append(profile_id_label(info))

        if missing_bits:
            self.path_preview.set("Export preview: enter " + " + ".join(missing_bits) + " to see final output path.")
            return

        if not files:
            self.path_preview.set("Export preview: (no output)")
            return

        if len(files) == 1:
            self.path_preview.set(f"Export preview: {files[0]}")
            return

        names = [Path(f).name for f in files]
        show = names[:6]
        more = len(names) - len(show)
        lines = [f"Export preview: {out_dir}", "  " + "  ".join(show)]
        if more > 0:
            lines.append(f"  ... +{more} more")
        self.path_preview.set("\n".join(lines))
    except Exception:
        try:
            self.path_preview.set("Export preview: (could not build preview)")
        except Exception:
            pass

def quick_export(app):
    self = app
    prof = self.profile_var.get()
    if not prof:
        messagebox.showerror("Quick Export", "Select a profile before exporting.")
        return

    error = self._validate_export_inputs(prof)
    if error:
        messagebox.showerror("Quick Export", error)
        return
    plan = self.build_export_plan(prof)

    try:
        plan["root"].mkdir(parents=True, exist_ok=True)
    except Exception:
        pass
    try:
        plan["out_dir"].mkdir(parents=True, exist_ok=True)
    except Exception:
        pass

    content = prepare_export_text(self.get_profile_info(prof), self.editor.get("1.0", tk.END))
    wrote = []
    for fp in plan["files"]:
        try:
            fp.parent.mkdir(parents=True, exist_ok=True)
            fp.write_text(content, encoding="utf-8")
            wrote.append(str(fp))
        except Exception as e:
            messagebox.showerror("Quick Export", f"Could not write file:\n{fp}\n\n{e}")
            return

    self.status.set(f"Quick exported {len(wrote)} file(s).")
