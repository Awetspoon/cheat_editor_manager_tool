from __future__ import annotations

from dataclasses import dataclass
import tkinter as tk
from tkinter import messagebox, ttk

from ...constants import DEFAULT_PROFILES
from ...storage import save_prefs
from ...ui.style import (
    CONTROL_GAP,
    DIALOG_CONTENT_PAD_X,
    DIALOG_FORM_PAD_X,
    DIALOG_FORM_PAD_Y,
    DIALOG_FORM_WRAP,
    FONT_PANEL_TITLE,
    FONT_SECTION,
    PAD_TIGHT,
    PANEL_GAP,
)
from ...ui.widgets import (
    AutoScrollbar,
    configure_text_theme,
)
from .dialog_utils import (
    build_dialog_page_header,
    configure_dialog_window,
    refresh_dialog_theme,
)


RESERVED_CONSOLE_TERMS = (
    "switch",
    "atmos",
    "3ds",
    "nintendo ds",
    "nintendo 3ds",
    "cfw",
    "luma",
    "taihen",
)
RESERVED_HARDCODED_TOKENS = ("<tid>", "<bid>", "<titleid>")
CONTENT_PAD = DIALOG_CONTENT_PAD_X
BUTTON_GAP = PAD_TIGHT
PROFILE_DIALOG_GEOMETRY = "560x575"
PROFILE_DIALOG_WRAP = DIALOG_FORM_WRAP
PROFILE_TABLE_ROWS = 8


@dataclass
class SettingsProfilesPage:
    root: ttk.Frame
    profile_table: ttk.Treeview
    surfaces: tuple = ()

    def apply_theme(self, app) -> None:
        refresh_dialog_theme(app, self.root, *self.surfaces)


def build_profiles_page(
    app, page: ttk.Frame, window: tk.Toplevel
) -> SettingsProfilesPage:
    build_dialog_page_header(
        page,
        "Profiles",
        (
            "Custom emulator profiles live here. Built-in CFW layouts stay fixed."
        ),
    )
    profile_table, btns = _build_profiles_list_area(page)

    page_model = SettingsProfilesPage(
        root=page,
        profile_table=profile_table,
        surfaces=(),
    )
    page_model.apply_theme(app)

    def get_selected_name() -> str | None:
        selected = profile_table.selection()
        if not selected:
            return None
        values = profile_table.item(selected[0], "values")
        return str(values[0]) if values else None

    def refresh_profile_table(select_name: str | None = None) -> None:
        current_name = get_selected_name()
        for item_id in profile_table.get_children():
            profile_table.delete(item_id)
        names = _custom_profile_names(app)
        item_for_name = {}
        for name in names:
            profile_data = (app.prefs.get("custom_profiles") or {}).get(name, {})
            item_id = profile_table.insert(
                "",
                tk.END,
                values=_profile_table_values(name, profile_data),
            )
            item_for_name[name] = item_id
        target = select_name if select_name in names else current_name
        if target not in names:
            target = names[0] if names else None
        if target is not None:
            item_id = item_for_name[target]
            profile_table.selection_set(item_id)
            profile_table.focus(item_id)
            profile_table.see(item_id)

    def profile_dialog(existing_name: str | None = None) -> None:
        dlg = tk.Toplevel(window)
        title = "Edit Profile" if existing_name else "Add Profile"
        configure_dialog_window(
            app,
            dlg,
            title,
            PROFILE_DIALOG_GEOMETRY,
            parent=window,
            resizable=False,
        )

        custom_profiles = app.prefs.get("custom_profiles") or {}
        existing = custom_profiles.get(existing_name, {}) if existing_name else {}

        name_var = tk.StringVar(value=existing_name or "")
        subdir_var = tk.StringVar(value=existing.get("subdir", ""))
        fname_var = tk.StringVar(value=existing.get("filename_hint", ""))
        exts_var = tk.StringVar(value=",".join(existing.get("extensions", [".txt"])))

        frm = _build_profile_dialog_form(dlg, title)
        name_entry = _pack_form_field(frm, "Name", name_var)
        _pack_form_field(frm, "Folder structure", subdir_var)
        ttk.Label(
            frm,
            text=(
                "Use <Game>, <GameID>, <CRC>, <SERIAL>, or <Core Name>. "
                "<TID> and <BID> are built-in CFW tokens."
            ),
            wraplength=PROFILE_DIALOG_WRAP,
        ).pack(anchor="w", pady=(0, CONTROL_GAP))
        _pack_form_field(frm, "Filename", fname_var)
        _pack_form_field(frm, "Extensions", exts_var)
        notes, helper_limit = _build_helper_notes_control(app, frm, existing)

        brow = ttk.Frame(frm)
        brow.pack(fill="x", pady=(PANEL_GAP, 4))

        def on_save() -> None:
            profile_name = name_var.get().strip()
            if not _validate_profile_dialog(
                dlg,
                profile_name=profile_name,
                existing_name=existing_name,
                subdir_text=subdir_var.get().strip(),
                filename_text=fname_var.get().strip(),
            ):
                return

            updated_profiles = dict(app.prefs.get("custom_profiles") or {})
            if existing_name and profile_name != existing_name:
                updated_profiles.pop(existing_name, None)
            updated_profiles[profile_name] = {
                "subdir": subdir_var.get().strip(),
                "filename_hint": fname_var.get().strip(),
                "extensions": _normalize_extensions(exts_var.get()),
                "notes": _trim_helper_notes(notes.get("1.0", "end-1c"), helper_limit),
            }
            app.prefs["custom_profiles"] = updated_profiles
            save_prefs(app.prefs)

            refresh_profile_table(profile_name)
            app.refresh_profiles_dropdown()
            app.refresh_profile_info()
            dlg.destroy()

        ttk.Button(brow, text="Cancel", command=dlg.destroy).pack(
            side="right", padx=(CONTROL_GAP, 0)
        )
        ttk.Button(brow, text="Save", command=on_save).pack(side="right")
        name_entry.focus_set()

    def add_custom() -> None:
        profile_dialog(None)

    def edit_custom() -> None:
        profile_name = get_selected_name()
        if profile_name:
            profile_dialog(profile_name)

    def delete_custom() -> None:
        profile_name = get_selected_name()
        if not profile_name:
            return
        confirmed = messagebox.askyesno(
            "Delete Profile",
            f"Delete custom profile '{profile_name}'?",
            parent=window,
        )
        if not confirmed:
            return

        custom_profiles = dict(app.prefs.get("custom_profiles") or {})
        custom_profiles.pop(profile_name, None)
        app.prefs["custom_profiles"] = custom_profiles
        save_prefs(app.prefs)
        refresh_profile_table()
        app.refresh_profiles_dropdown()
        app.refresh_profile_info()

    _pack_profile_action_button(btns, "New", add_custom)
    _pack_profile_action_button(btns, "Edit", edit_custom)
    _pack_profile_action_button(
        btns,
        "Delete",
        delete_custom,
        is_last=True,
        style="Danger.TButton",
    )

    refresh_profile_table()
    return page_model


def _build_profiles_list_area(parent) -> tuple[ttk.Treeview, ttk.Frame]:
    body = ttk.Frame(parent)
    body.pack(fill="x", expand=False, padx=CONTENT_PAD, pady=(0, CONTENT_PAD))
    body.columnconfigure(0, weight=1)

    list_title = ttk.Label(body, text="Custom profiles", font=FONT_PANEL_TITLE)
    list_title.grid(row=0, column=0, sticky="w", pady=(0, CONTROL_GAP))

    btns = ttk.Frame(body)
    btns.grid(row=0, column=0, sticky="e", pady=(0, CONTROL_GAP))

    table_frame = ttk.Frame(body)
    table_frame.grid(row=1, column=0, sticky="nsew")
    table_frame.columnconfigure(0, weight=1)
    table_frame.rowconfigure(0, weight=1)

    columns = ("name", "folder", "filename", "extensions", "notes")
    profile_table = ttk.Treeview(
        table_frame,
        columns=columns,
        show="headings",
        height=PROFILE_TABLE_ROWS,
        selectmode="browse",
    )
    headings = {
        "name": "Name",
        "folder": "Folder structure",
        "filename": "Filename",
        "extensions": "Extensions",
        "notes": "Helper note",
    }
    widths = {
        "name": 150,
        "folder": 210,
        "filename": 105,
        "extensions": 80,
        "notes": 195,
    }
    for column in columns:
        profile_table.heading(column, text=headings[column])
        profile_table.column(
            column,
            width=widths[column],
            minwidth=70,
            stretch=column in {"folder", "notes"},
        )

    scrollbar = AutoScrollbar(table_frame, orient="vertical", command=profile_table.yview)
    h_scrollbar = AutoScrollbar(
        table_frame,
        orient="horizontal",
        command=profile_table.xview,
    )
    profile_table.configure(
        yscrollcommand=scrollbar.set,
        xscrollcommand=h_scrollbar.set,
    )
    profile_table.grid(row=0, column=0, sticky="nsew")
    scrollbar.grid(row=0, column=1, sticky="ns")
    h_scrollbar.grid(row=1, column=0, sticky="ew")

    empty_hint = ttk.Label(
        body,
        text="Use New to add an emulator-only profile. Built-in CFW targets are managed by the app.",
    )
    empty_hint.grid(row=2, column=0, sticky="w", pady=(CONTROL_GAP, 0))
    return profile_table, btns


def _profile_table_values(profile_name: str, profile_data: dict) -> tuple[str, ...]:
    return (
        profile_name,
        profile_data.get("subdir", "") or "(Export Root)",
        profile_data.get("filename_hint", "") or "(Default)",
        ", ".join(profile_data.get("extensions", []) or [".txt"]),
        _compact_table_text(profile_data.get("notes", "") or ""),
    )


def _compact_table_text(text: str, *, limit: int = 64) -> str:
    compact = " ".join(str(text or "").split())
    if len(compact) <= limit:
        return compact or "(No helper note)"
    return compact[: limit - 3].rstrip() + "..."


def _build_profile_dialog_form(parent, title: str) -> ttk.Frame:
    frm = ttk.Frame(parent)
    frm.pack(
        fill="both",
        expand=True,
        padx=DIALOG_FORM_PAD_X,
        pady=DIALOG_FORM_PAD_Y,
    )
    ttk.Label(frm, text=title, font=FONT_SECTION).pack(anchor="w")
    ttk.Label(
        frm,
        text="Add one emulator-only profile. Built-in CFW layouts stay fixed.",
        wraplength=PROFILE_DIALOG_WRAP,
    ).pack(anchor="w", pady=(2, PANEL_GAP))
    return frm


def _pack_form_field(parent, label: str, variable: tk.StringVar) -> ttk.Entry:
    ttk.Label(parent, text=label).pack(anchor="w", pady=(0, 3))
    entry = ttk.Entry(parent, textvariable=variable)
    entry.pack(fill="x", pady=(0, CONTROL_GAP))
    return entry


def _build_helper_notes_control(app, form, existing: dict) -> tuple[tk.Text, int]:
    help_wrap = ttk.Frame(form)
    help_wrap.pack(fill="x", pady=(0, CONTROL_GAP))
    ttk.Label(help_wrap, text="Helper note").pack(anchor="w", pady=(0, 3))
    ttk.Label(
        help_wrap,
        text=(
            "Short text shown in the Helper panel for this profile."
        ),
        wraplength=PROFILE_DIALOG_WRAP,
    ).pack(anchor="w", pady=(0, 6))

    notes_frame = ttk.Frame(help_wrap)
    notes_frame.pack(fill="x")
    notes = tk.Text(notes_frame, height=4, wrap="word")
    configure_text_theme(notes, app, editor=True)
    notes_vsb = AutoScrollbar(notes_frame, orient="vertical", command=notes.yview)
    notes.configure(yscrollcommand=notes_vsb.set)
    notes.grid(row=0, column=0, sticky="nsew")
    notes_vsb.grid(row=0, column=1, sticky="ns")
    notes_frame.columnconfigure(0, weight=1)

    notes.insert("1.0", existing.get("notes", ""))

    helper_capacity = app._estimate_helper_visible_chars()
    helper_limit = max(140, min(280, helper_capacity - 80))
    ttk.Label(
        help_wrap,
        text=(
            f"Keep it under about {helper_limit} characters so it fits cleanly."
        ),
        wraplength=PROFILE_DIALOG_WRAP,
    ).pack(anchor="w", pady=(6, 0))

    counter_var = tk.StringVar(value="")
    counter_lbl = ttk.Label(help_wrap, textvariable=counter_var)
    counter_lbl.pack(anchor="w", pady=(6, 0))

    def update_counter(trimmed: bool = False) -> None:
        text = notes.get("1.0", "end-1c")
        chars = len(text)
        if trimmed:
            counter_var.set(
                f"Characters: {chars} / {helper_limit}   |   "
                "Trimmed to fit the Helper box."
            )
        else:
            counter_var.set(
                f"Characters: {chars} / {helper_limit}   |   "
                f"Helper capacity: ~{helper_capacity} total"
            )

    def enforce_notes_limit() -> None:
        text = notes.get("1.0", "end-1c")
        if len(text) <= helper_limit:
            update_counter()
            return
        notes.delete("1.0", f"1.0+{len(text)}c")
        notes.insert("1.0", text[:helper_limit])
        try:
            notes.mark_set(tk.INSERT, "end-1c")
        except Exception:
            pass
        update_counter(trimmed=True)

    notes.bind("<KeyRelease>", lambda _e: notes.after_idle(enforce_notes_limit))
    notes.bind("<<Paste>>", lambda _e: notes.after_idle(enforce_notes_limit))
    notes.bind("<<Cut>>", lambda _e: notes.after_idle(update_counter))
    update_counter()
    return notes, helper_limit


def _validate_profile_dialog(
    parent,
    *,
    profile_name: str,
    existing_name: str | None,
    subdir_text: str,
    filename_text: str,
) -> bool:
    if not profile_name:
        messagebox.showerror("Missing name", "Profile name is required.", parent=parent)
        return False
    if profile_name in DEFAULT_PROFILES and profile_name != existing_name:
        messagebox.showerror(
            "Name conflict",
            "That name is used by a built-in profile.",
            parent=parent,
        )
        return False

    is_new_or_renamed = existing_name is None or profile_name != existing_name
    if is_new_or_renamed and _uses_reserved_builtin_layout(
        profile_name, subdir_text, filename_text
    ):
        messagebox.showerror(
            "Emulator-only custom profile",
            (
                "Custom profiles are emulator-only.\n\n"
                "Switch / DS / CFW layouts are hardcoded in built-in profiles "
                "and cannot be customized here."
            ),
            parent=parent,
        )
        return False
    return True


def _custom_profile_names(app) -> list[str]:
    return sorted(
        (app.prefs.get("custom_profiles") or {}).keys(),
        key=lambda value: value.casefold(),
    )


def _uses_reserved_builtin_layout(
    profile_name: str, subdir_text: str, filename_text: str
) -> bool:
    profile_name_lower = profile_name.casefold()
    layout_text = f"{subdir_text} {filename_text}".casefold()
    return any(term in profile_name_lower for term in RESERVED_CONSOLE_TERMS) or any(
        token in layout_text for token in RESERVED_HARDCODED_TOKENS
    )


def _normalize_extensions(raw: str) -> list[str]:
    extensions = [item.strip() for item in raw.split(",") if item.strip()]
    return [item if item.startswith(".") else "." + item for item in extensions] or [
        ".txt"
    ]


def _trim_helper_notes(text: str, helper_limit: int) -> str:
    helper_notes = text.strip()
    if len(helper_notes) > helper_limit:
        return helper_notes[:helper_limit].rstrip()
    return helper_notes


def _pack_profile_action_button(
    parent, text: str, command, *, is_last: bool = False, style: str | None = None
) -> None:
    options = {"text": text, "command": command}
    if style is not None:
        options["style"] = style
    ttk.Button(parent, **options).pack(
        side="left",
        padx=(0, 0 if is_last else BUTTON_GAP),
    )
