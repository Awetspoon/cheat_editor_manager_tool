from __future__ import annotations

from dataclasses import dataclass
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from ...constants import APP_DIR, DEFAULT_PROFILES
from ...ui.style import (
    CONTROL_GAP,
    DIALOG_CONTENT_PAD_X,
    FONT_PANEL_TITLE,
    PANEL_GAP,
)
from ...ui.widgets import AutoScrollbar, configure_listbox_theme
from .dialog_utils import build_dialog_page_header, refresh_dialog_theme


ATMOSPHERE_PROFILE = "Atmosphere (Switch) (CFW)"
CONTENT_PAD = DIALOG_CONTENT_PAD_X
BUTTON_GAP = CONTROL_GAP


@dataclass
class SettingsExportRootsPage:
    app: object
    root: ttk.Frame
    profile_list: tk.Listbox
    pending_overrides: dict[str, str]
    surfaces: tuple = ()

    def save_to_prefs(self) -> None:
        self.app.prefs["emulator_paths"] = {
            profile_name: str(path).strip()
            for profile_name, path in self.pending_overrides.items()
            if str(path).strip()
        }

    def apply_theme(self, app) -> None:
        self.root.configure(style="TFrame")
        configure_listbox_theme(self.profile_list, app)
        refresh_dialog_theme(app, self.root, *self.surfaces)


def build_export_roots_page(
    app, page: ttk.Frame, window: tk.Toplevel
) -> SettingsExportRootsPage:
    build_dialog_page_header(
        page,
        "Export Roots",
        (
            "Optional folder overrides for built-in profiles. Custom profile "
            "folder layouts stay in Profiles."
        ),
    )

    body = ttk.Frame(page)
    body.pack(fill="both", expand=True, padx=CONTENT_PAD, pady=(0, CONTENT_PAD))
    body.columnconfigure(0, weight=1)
    body.columnconfigure(1, weight=2)
    body.rowconfigure(1, weight=1)

    profile_list = _build_profile_list(body)
    detail_vars = _build_override_detail(body)
    action_buttons = _build_override_actions(body)
    pending_overrides = dict(app.prefs.get("emulator_paths", {}) or {})
    is_refreshing = {"value": False}

    def selected_profile() -> str | None:
        selected = profile_list.curselection()
        return profile_list.get(selected[0]) if selected else None

    def inherited_export_root() -> str:
        return str(
            app.export_var.get()
            or app.prefs.get("export_root", str(APP_DIR))
            or APP_DIR
        )

    def refresh_detail(*_) -> None:
        profile_name = selected_profile()
        is_refreshing["value"] = True
        if not profile_name:
            _set_detail_empty(detail_vars, inherited_export_root())
            is_refreshing["value"] = False
            return
        _set_detail_values(
            detail_vars,
            profile_name=profile_name,
            inherited_root=inherited_export_root(),
            override=str(pending_overrides.get(profile_name, "") or ""),
        )
        is_refreshing["value"] = False

    def refresh_list(select_name: str | None = None) -> None:
        profile_list.delete(0, tk.END)
        names = _override_profile_names()
        for profile_name in names:
            profile_list.insert(tk.END, profile_name)
        target = select_name if select_name in names else names[0] if names else None
        if target is not None:
            index = names.index(target)
            profile_list.selection_set(index)
            profile_list.see(index)
        refresh_detail()

    def remember_override(*_) -> None:
        if is_refreshing["value"]:
            return
        profile_name = selected_profile()
        if not profile_name:
            return
        override = detail_vars["override"].get().strip()
        if override:
            pending_overrides[profile_name] = override
        else:
            pending_overrides.pop(profile_name, None)
        _set_effective_from_override(
            detail_vars,
            inherited_root=inherited_export_root(),
            override=override,
        )

    def reset_selected() -> None:
        profile_name = selected_profile()
        if not profile_name:
            return
        pending_overrides.pop(profile_name, None)
        detail_vars["override"].set("")
        refresh_detail()

    def browse_override() -> None:
        profile_name = selected_profile()
        if not profile_name:
            messagebox.showinfo("Export Roots", "Select a profile first.", parent=window)
            return
        selected_path = filedialog.askdirectory(parent=window)
        if selected_path:
            detail_vars["override"].set(selected_path)

    action_buttons["browse"].configure(command=browse_override)
    action_buttons["reset"].configure(command=reset_selected)
    profile_list.bind("<<ListboxSelect>>", refresh_detail)
    try:
        detail_vars["override"].trace_add("write", remember_override)
    except Exception:
        pass
    refresh_list()

    page_model = SettingsExportRootsPage(
        app=app,
        root=page,
        profile_list=profile_list,
        pending_overrides=pending_overrides,
        surfaces=(),
    )
    page_model.apply_theme(app)
    return page_model


def _build_profile_list(parent) -> tk.Listbox:
    ttk.Label(parent, text="Built-in profiles", font=FONT_PANEL_TITLE).grid(
        row=0, column=0, sticky="w", padx=CONTENT_PAD, pady=(0, CONTROL_GAP)
    )

    list_frame = ttk.Frame(parent)
    list_frame.grid(
        row=1,
        column=0,
        sticky="nsew",
        padx=CONTENT_PAD,
        pady=(0, CONTENT_PAD),
    )
    list_frame.columnconfigure(0, weight=1)
    list_frame.rowconfigure(0, weight=1)

    profile_list = tk.Listbox(list_frame, activestyle="none", exportselection=False)
    scrollbar = AutoScrollbar(list_frame, orient="vertical", command=profile_list.yview)
    profile_list.configure(yscrollcommand=scrollbar.set)
    profile_list.grid(row=0, column=0, sticky="nsew")
    scrollbar.grid(row=0, column=1, sticky="ns")
    return profile_list


def _build_override_detail(parent) -> dict[str, tk.StringVar]:
    ttk.Label(parent, text="Selected folder", font=FONT_PANEL_TITLE).grid(
        row=0, column=1, sticky="w", padx=CONTENT_PAD, pady=(0, CONTROL_GAP)
    )

    detail = ttk.Frame(parent)
    detail.grid(
        row=1,
        column=1,
        sticky="nsew",
        padx=(0, CONTENT_PAD),
        pady=(0, CONTENT_PAD),
    )
    detail.columnconfigure(0, weight=1)

    detail_vars = {
        "profile": tk.StringVar(value="No profile selected"),
        "inherited": tk.StringVar(value=""),
        "effective": tk.StringVar(value=""),
        "override": tk.StringVar(value=""),
        "note": tk.StringVar(value=""),
    }

    _detail_label(detail, "Profile", detail_vars["profile"]).grid(
        row=0, column=0, sticky="ew", pady=(0, PANEL_GAP)
    )
    _detail_label(detail, "Default export root", detail_vars["inherited"]).grid(
        row=1, column=0, sticky="ew", pady=(0, PANEL_GAP)
    )
    _detail_label(detail, "Effective export root", detail_vars["effective"]).grid(
        row=2, column=0, sticky="ew", pady=(0, PANEL_GAP)
    )

    ttk.Label(detail, text="Override path").grid(row=3, column=0, sticky="w", pady=(0, 4))
    ttk.Entry(detail, textvariable=detail_vars["override"]).grid(
        row=4, column=0, sticky="ew", pady=(0, PANEL_GAP)
    )
    ttk.Label(detail, textvariable=detail_vars["note"], wraplength=560).grid(
        row=5, column=0, sticky="ew", pady=(0, PANEL_GAP)
    )
    return detail_vars


def _detail_label(parent, title: str, variable: tk.StringVar) -> ttk.Frame:
    frame = ttk.Frame(parent)
    ttk.Label(frame, text=title).pack(anchor="w")
    ttk.Label(frame, textvariable=variable, wraplength=560).pack(anchor="w", pady=(2, 0))
    return frame


def _build_override_actions(parent) -> dict[str, ttk.Button]:
    actions = ttk.Frame(parent)
    actions.grid(
        row=2,
        column=1,
        sticky="ew",
        padx=(0, CONTENT_PAD),
        pady=(0, CONTENT_PAD),
    )

    browse = ttk.Button(actions, text="Browse folder")
    reset = ttk.Button(actions, text="Use default")
    browse.pack(side="left")
    reset.pack(side="left", padx=(BUTTON_GAP, 0))
    return {"browse": browse, "reset": reset}


def _set_detail_empty(detail_vars: dict[str, tk.StringVar], inherited_root: str) -> None:
    detail_vars["profile"].set("No profile selected")
    detail_vars["inherited"].set(inherited_root)
    detail_vars["effective"].set(inherited_root)
    detail_vars["override"].set("")
    detail_vars["note"].set("Select a built-in profile to edit its export-root override.")


def _set_detail_values(
    detail_vars: dict[str, tk.StringVar],
    *,
    profile_name: str,
    inherited_root: str,
    override: str,
) -> None:
    detail_vars["profile"].set(profile_name)
    detail_vars["inherited"].set(inherited_root)
    detail_vars["override"].set(override)
    _set_effective_from_override(
        detail_vars,
        inherited_root=inherited_root,
        override=override,
    )


def _set_effective_from_override(
    detail_vars: dict[str, tk.StringVar], *, inherited_root: str, override: str
) -> None:
    effective_root = override or inherited_root
    detail_vars["effective"].set(effective_root)
    detail_vars["note"].set(
        "Leave the override empty to use the default Export Root."
        if not override
        else "This profile will export under the override path above."
    )


def _override_profile_names() -> list[str]:
    return [name for name in DEFAULT_PROFILES if name != ATMOSPHERE_PROFILE]


def _profile_override(prefs: dict, profile_name: str) -> str:
    return str((prefs.get("emulator_paths", {}) or {}).get(profile_name, ""))


def _set_profile_override(prefs: dict, profile_name: str, raw_path: str) -> None:
    value = str(raw_path or "").strip()
    overrides = prefs.setdefault("emulator_paths", {})
    if value:
        overrides[profile_name] = value
    else:
        overrides.pop(profile_name, None)


def _clear_profile_override(prefs: dict, profile_name: str) -> None:
    prefs.setdefault("emulator_paths", {}).pop(profile_name, None)
