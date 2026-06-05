from __future__ import annotations

import tkinter as tk
from pathlib import Path
from typing import Optional

from tkinter import filedialog, messagebox

from ..constants import APP_DIR
from ..export_logic import (
    build_export_preview_message,
    build_export_plan as build_export_plan_for_state,
    prepare_export_text,
    validate_export_inputs,
)


def effective_export_root_for_profile(app, prof: str) -> Path:
    """Return the export root for a profile.

    Atmosphere safeguard:
      - Atmosphere should never 'mysteriously' export somewhere else because of an override.
      - To keep first-time users safe, Atmosphere always uses the main Export Root (point this at SD root).
    """
    self = app
    # Atmosphere: ignore per-profile overrides to avoid clashing with the official folder structure.
    if prof.strip() == "Atmosphere (Switch) (CFW)":
        return Path(self.export_var.get() or self.prefs.get("export_root", str(APP_DIR)))

    override = (self.prefs.get("emulator_paths", {}) or {}).get(prof, "").strip()
    if override:
        return Path(override)
    return Path(self.export_var.get() or self.prefs.get("export_root", str(APP_DIR)))

def get_all_known_extensions(app):
    """Collect all unique extensions from built-in + custom profiles."""
    self = app
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


def extension_options_for_profile(app, prof: str) -> tuple[list[str], list[str]]:
    """Return profile extensions and all known extensions for save-as choices."""
    self = app
    info = self.get_profile_info(prof)
    profile_exts = [e.strip() for e in (info.get("extensions") or [".txt"]) if e and e.strip()]
    profile_exts = [(e if e.startswith(".") else "." + e).lower() for e in profile_exts] or [".txt"]
    all_exts = self._get_all_known_extensions()
    return profile_exts, all_exts

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
        self.path_preview.set(
            build_export_preview_message(
                info=info,
                plan=plan,
                tid=self.tid_var.get(),
                bid_text=self.bid_var.get(),
            )
        )
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
