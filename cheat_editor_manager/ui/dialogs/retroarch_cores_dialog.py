from __future__ import annotations

import tkinter as tk
from typing import Optional

from tkinter import messagebox

from ...services import retroarch_core_service
from ...storage import save_prefs
from ...ui.widgets import ask_text
from .dialog_utils import (
    build_dialog_header,
    build_dialog_list_with_sidebar,
    configure_dialog_window,
    pack_sidebar_button,
)


def manage_retroarch_cores(app):
    self = app
    retroarch_core_service.ensure_core_preferences(self.prefs)
    save_prefs(self.prefs)

    win = tk.Toplevel(self.root)
    configure_dialog_window(self, win, "RetroArch cores", "640x460")

    build_dialog_header(
        self,
        win,
        "RetroArch Cores",
        "Cores control the folder name used under cheats/.",
    )

    lb, btns = build_dialog_list_with_sidebar(self, win)

    default_name = retroarch_core_service.DEFAULT_CORE_NAME

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

    def commit(selected_name: Optional[str] = None):
        retroarch_core_service.ensure_core_preferences(self.prefs)
        self._sync_core_dropdown()
        save_prefs(self.prefs)
        refresh(selected_name)
        self.refresh_profile_info()

    def add():
        name = ask_text(win, "Add core", "Core name (folder name):")
        if not name:
            return
        retroarch_core_service.add_core(self.prefs, name)
        commit(name)

    def edit():
        current = selected()
        if not current:
            return
        if current.casefold() == default_name.casefold():
            messagebox.showinfo(
                "RetroArch cores",
                "The default entry stays fixed.",
                parent=win,
            )
            return
        name = ask_text(win, "Edit core", f"New name (current: {current}):")
        if not name:
            return
        retroarch_core_service.rename_core(self.prefs, current, name)
        commit(name)

    def remove():
        current = selected()
        if not current:
            return
        if current.casefold() == default_name.casefold():
            messagebox.showinfo(
                "RetroArch cores",
                "The default entry stays fixed.",
                parent=win,
            )
            return
        if not messagebox.askyesno(
            "Remove core",
            f"Remove '{current}' from the core list?",
            parent=win,
        ):
            return
        retroarch_core_service.remove_core(self.prefs, current)
        commit(default_name)

    pack_sidebar_button(btns, text="Add...", command=add)
    pack_sidebar_button(btns, text="Edit...", command=edit)
    pack_sidebar_button(btns, text="Remove", command=remove)
    pack_sidebar_button(btns, text="Close", command=win.destroy, pady=(18, 0))

    refresh()
