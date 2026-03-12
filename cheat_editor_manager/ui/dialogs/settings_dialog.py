from __future__ import annotations

import re
import tkinter as tk
from typing import Dict, Optional

from tkinter import colorchooser, filedialog, messagebox, ttk

from ...constants import (
    DEFAULT_BUTTON_COLORS,
    DEFAULT_PROFILES,
    DEFAULT_THEME_DARK,
    DEFAULT_THEME_LIGHT,
)
from ...storage import save_prefs
from ...widgets import Scrollable

def open_settings(app):
    self = app
    reserved_console_terms = (
        "switch",
        "atmos",
        "3ds",
        "nintendo ds",
        "nintendo 3ds",
        "cfw",
        "luma",
        "taihen",
    )
    reserved_hardcoded_tokens = ("<tid>", "<bid>", "<titleid>")
    win = tk.Toplevel(self.root); win.title("Settings"); win.geometry("980x640")
    win.transient(self.root); win.grab_set()
    sf = Scrollable(win); sf.pack(fill="both", expand=True); sf.set_canvas_bg(self.effective_colors()["bg"])
    nb = ttk.Notebook(sf.inner); nb.pack(fill="both", expand=True, padx=12, pady=12)


    # Profiles tab (custom profiles)
    tab_profiles = ttk.Frame(nb); nb.add(tab_profiles, text="Profiles")
    prof_sf = Scrollable(tab_profiles); prof_sf.pack(fill="both", expand=True, padx=6, pady=6); prof_sf.set_canvas_bg(self.effective_colors()["bg"])

    ttk.Label(prof_sf.inner, text="Profiles", font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=12, pady=(12, 6))
    ttk.Label(prof_sf.inner, text="Add custom emulator profiles here. Switch / DS / CFW targets are hardcoded and should use built-in profiles.", wraplength=900).pack(anchor="w", padx=12, pady=(0, 10))

    body = ttk.Frame(prof_sf.inner); body.pack(fill="both", expand=True, padx=12, pady=6)
    # Keep the Profiles list tidy when the Settings window is maximized:
    # - Do NOT let the list stretch super-wide
    # - Let a spacer absorb extra width instead
    body.columnconfigure(0, weight=0)   # list column (fixed width)
    body.columnconfigure(1, weight=0)   # buttons column (fixed)
    body.columnconfigure(2, weight=1)   # spacer column (expands)

    custom_list = tk.Listbox(body, height=14, width=42)
    custom_list.grid(row=0, column=0, sticky="nsw", padx=(0, 10))
    c = self.effective_colors(); btn = dict(DEFAULT_BUTTON_COLORS); btn.update(self.prefs.get("button_colors", {}))
    selection_bg, selection_fg = self._selection_palette(btn.get("primary", DEFAULT_BUTTON_COLORS["primary"]))
    custom_list.configure(bg=c["panel2"], fg=self._ensure_text_contrast(c["panel2"], preferred=c["text"], minimum=4.5), selectbackground=selection_bg, selectforeground=selection_fg, highlightthickness=1, highlightbackground=c["border"])
    btns = ttk.Frame(body); btns.grid(row=0, column=1, sticky="ns")
    spacer = ttk.Frame(body)
    spacer.grid(row=0, column=2, sticky="nsew")

    def refresh_custom_list():
        custom_list.delete(0, "end")
        for n in sorted((self.prefs.get("custom_profiles") or {}).keys(), key=lambda s: s.casefold()):
            custom_list.insert("end", n)

    def get_sel():
        sel = custom_list.curselection()
        return custom_list.get(sel[0]) if sel else None

    def profile_dialog(existing_name=None):
        dlg = tk.Toplevel(win); dlg.title("Edit Profile" if existing_name else "Add Profile")
        dlg.transient(win); dlg.grab_set()
        dlg.geometry("700x620")
        frm = ttk.Frame(dlg); frm.pack(fill="both", expand=True, padx=12, pady=12)
        frm.columnconfigure(1, weight=1)

        cp = (self.prefs.get("custom_profiles") or {})
        existing = cp.get(existing_name, {}) if existing_name else {}

        name_var = tk.StringVar(value=existing_name or "") 
        subdir_var = tk.StringVar(value=existing.get("subdir", ""))
        fname_var = tk.StringVar(value=existing.get("filename_hint", ""))
        exts_var = tk.StringVar(value=",".join(existing.get("extensions", [".txt"])))

        ttk.Label(frm, text="Emulator Profile Name:").grid(row=0, column=0, sticky="w", pady=4)
        ttk.Entry(frm, textvariable=name_var).grid(row=0, column=1, sticky="ew", pady=4)

        ttk.Label(frm, text="Export Folder Structure:").grid(row=1, column=0, sticky="w", pady=4)
        ttk.Entry(frm, textvariable=subdir_var).grid(row=1, column=1, sticky="ew", pady=4)
        ttk.Label(
            frm,
            text="Where cheats will be exported inside Export Root. Use emulator placeholders like <Game>, <GameID>, <CRC>, <SERIAL>, <Core Name> (if applicable). Switch/DS tokens (<TID>, <BID>, <TitleID>) are reserved for built-in profiles.",
            wraplength=520,
        ).grid(row=2, column=1, sticky="w", pady=(0, 8))

        ttk.Label(frm, text="Filename hint:").grid(row=3, column=0, sticky="w", pady=4)
        ttk.Entry(frm, textvariable=fname_var).grid(row=3, column=1, sticky="ew", pady=4)

        ttk.Label(frm, text="Extensions (comma):").grid(row=4, column=0, sticky="w", pady=4)
        ttk.Entry(frm, textvariable=exts_var).grid(row=4, column=1, sticky="ew", pady=4)

        ttk.Label(frm, text="Helper Text (shown in the Helper box):").grid(row=5, column=0, sticky="nw", pady=(10, 4))

        help_wrap = ttk.Frame(frm)
        help_wrap.grid(row=5, column=1, sticky="nsew", pady=(10, 4))
        ttk.Label(
            help_wrap,
            text="Write short cheat instructions for this profile (keep it brief — the Helper box is limited height).",
            wraplength=520,
        ).pack(anchor="w")

        notes_frame = ttk.Frame(help_wrap)
        notes_frame.pack(fill="both", expand=True, pady=(6, 0))
        notes = tk.Text(notes_frame, height=5, wrap="word")
        dialog_colors = self.effective_colors()
        dialog_btn = dict(DEFAULT_BUTTON_COLORS); dialog_btn.update(self.prefs.get("button_colors", {}))
        dialog_selection_bg, dialog_selection_fg = self._selection_palette(dialog_btn.get("primary", DEFAULT_BUTTON_COLORS["primary"]))
        notes.configure(
            bg=dialog_colors["editor_bg"],
            fg=dialog_colors["editor_fg"],
            insertbackground=dialog_colors["editor_fg"],
            selectbackground=dialog_selection_bg,
            selectforeground=dialog_selection_fg,
        )
        notes_vsb = ttk.Scrollbar(notes_frame, orient="vertical", command=notes.yview)
        notes.configure(yscrollcommand=notes_vsb.set)
        notes.grid(row=0, column=0, sticky="nsew")
        notes_vsb.grid(row=0, column=1, sticky="ns")
        notes_frame.columnconfigure(0, weight=1)
        notes_frame.rowconfigure(0, weight=1)

        # Allow the helper text area to expand inside this dialog.
        frm.rowconfigure(5, weight=1)

        notes.insert("1.0", existing.get("notes", ""))

        helper_capacity = self._estimate_helper_visible_chars()
        helper_limit = max(140, min(280, helper_capacity - 80))
        ttk.Label(
            help_wrap,
            text=f"Keep helper text under about {helper_limit} characters so it fits the Helper card cleanly.",
            wraplength=520,
        ).pack(anchor="w", pady=(6, 0))

        counter_var = tk.StringVar(value="")
        counter_lbl = ttk.Label(help_wrap, textvariable=counter_var)
        counter_lbl.pack(anchor="w", pady=(6, 0))

        def update_counter(trimmed: bool = False):
            txt = notes.get("1.0", "end-1c")
            chars = len(txt)
            if trimmed:
                counter_var.set(f"Characters: {chars} / {helper_limit}   |   Trimmed to fit the Helper box.")
            else:
                counter_var.set(f"Characters: {chars} / {helper_limit}   |   Helper capacity: ~{helper_capacity} total")

        def enforce_notes_limit():
            txt = notes.get("1.0", "end-1c")
            if len(txt) <= helper_limit:
                update_counter()
                return
            notes.delete("1.0", "1.0+%dc" % len(txt))
            notes.insert("1.0", txt[:helper_limit])
            try:
                notes.mark_set(tk.INSERT, "end-1c")
            except Exception:
                pass
            update_counter(trimmed=True)

        notes.bind("<KeyRelease>", lambda _e: notes.after_idle(enforce_notes_limit))
        notes.bind("<<Paste>>", lambda _e: notes.after_idle(enforce_notes_limit))
        notes.bind("<<Cut>>", lambda _e: notes.after_idle(update_counter))
        update_counter()

        brow = ttk.Frame(frm); brow.grid(row=6, column=1, sticky="e", pady=(10,0))

        def on_save():
            nm = name_var.get().strip()
            if not nm:
                messagebox.showerror("Missing name", "Profile name is required.", parent=dlg)
                return
            if nm in DEFAULT_PROFILES and nm != existing_name:
                messagebox.showerror("Name conflict", "That name is used by a built-in profile.", parent=dlg)
                return

            nm_lower = nm.casefold()
            subdir_text = subdir_var.get().strip()
            fname_text = fname_var.get().strip()
            layout_text = f"{subdir_text} {fname_text}".casefold()
            is_reserved_console_name = any(term in nm_lower for term in reserved_console_terms)
            uses_reserved_tokens = any(token in layout_text for token in reserved_hardcoded_tokens)
            if (is_reserved_console_name or uses_reserved_tokens) and (existing_name is None or nm != existing_name):
                messagebox.showerror(
                    "Emulator-only custom profile",
                    "Custom profiles are emulator-only.\n\nSwitch / DS / CFW layouts are hardcoded in built-in profiles and cannot be customized here.",
                    parent=dlg,
                )
                return

            exts = [e.strip() for e in exts_var.get().split(",") if e.strip()]
            exts = [e if e.startswith(".") else "." + e for e in exts] or [".txt"]

            helper_notes = notes.get("1.0", "end-1c").strip()
            if len(helper_notes) > helper_limit:
                helper_notes = helper_notes[:helper_limit].rstrip()

            info = {
                "subdir": subdir_text,
                "filename_hint": fname_text,
                "extensions": exts,
                "notes": helper_notes,
            }

            cp2 = dict(self.prefs.get("custom_profiles") or {})
            if existing_name and nm != existing_name:
                cp2.pop(existing_name, None)
            cp2[nm] = info
            self.prefs["custom_profiles"] = cp2
            save_prefs(self.prefs)

            refresh_custom_list()
            self.refresh_profiles_dropdown()
            self.refresh_profile_info()
            dlg.destroy()

        ttk.Button(brow, text="Cancel", command=dlg.destroy).pack(side="right", padx=(8,0))
        ttk.Button(brow, text="Save", command=on_save).pack(side="right")

    def add_custom():
        profile_dialog(None)

    def edit_custom():
        nm = get_sel()
        if nm: profile_dialog(nm)

    def del_custom():
        nm = get_sel()
        if not nm: return
        if not messagebox.askyesno("Delete Profile", f"Delete custom profile '{nm}'?", parent=win): return
        cp = dict(self.prefs.get("custom_profiles") or {})
        cp.pop(nm, None)
        self.prefs["custom_profiles"] = cp
        save_prefs(self.prefs)
        refresh_custom_list()
        self.refresh_profiles_dropdown()
        self.refresh_profile_info()

    ttk.Button(btns, text="Add…", command=add_custom).pack(fill="x", pady=(0,6))
    ttk.Button(btns, text="Edit…", command=edit_custom).pack(fill="x", pady=(0,6))
    ttk.Button(btns, text="Delete", command=del_custom).pack(fill="x")

    refresh_custom_list()


    tab_app = ttk.Frame(nb); nb.add(tab_app, text="Appearance")
    app_sf = Scrollable(tab_app); app_sf.pack(fill="both", expand=True, padx=6, pady=6); app_sf.set_canvas_bg(self.effective_colors()["bg"])

    ttk.Label(app_sf.inner, text="Appearance", font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=12, pady=(12, 6))
    ttk.Label(app_sf.inner, text="Choose a preset or use Custom to fully control colours.", wraplength=900).pack(anchor="w", padx=12, pady=(0, 10))

    # Mode: Dark / Light / Custom
    cur_mode = "custom" if self.prefs.get("custom_theme_enabled", False) else str(self.prefs.get("mode", "dark") or "dark")
    mode_var = tk.StringVar(value=cur_mode if cur_mode in ("dark","light","custom") else "dark")
    def _on_mode_change(*_):
        # If user switches to Custom, keep the current Dark/Light base (don't silently flip).
        if mode_var.get() != "custom":
            return
        try:
            base = DEFAULT_THEME_DARK if self.prefs.get("mode") == "dark" else DEFAULT_THEME_LIGHT
            # If fields still match Dark defaults while we're in Light mode, seed from Light base.
            if self.prefs.get("mode") == "light":
                current_vals = {k: v.get().strip() for k, v in color_vars.items()}
                if current_vals and current_vals == dict(DEFAULT_THEME_DARK):
                    for k, v in base.items():
                        if k in color_vars:
                            color_vars[k].set(str(v))
        except Exception:
            pass


    mode_row = ttk.Frame(app_sf.inner); mode_row.pack(fill="x", padx=12, pady=(0, 10))
    ttk.Label(mode_row, text="Mode:").pack(side="left")
    ttk.Radiobutton(mode_row, text="Dark", value="dark", variable=mode_var).pack(side="left", padx=(12,0))
    ttk.Radiobutton(mode_row, text="Light", value="light", variable=mode_var).pack(side="left", padx=(12,0))
    ttk.Radiobutton(mode_row, text="Custom", value="custom", variable=mode_var).pack(side="left", padx=(12,0))

    ttk.Label(app_sf.inner, text="Custom colours only apply when Mode is set to Custom.", wraplength=900).pack(anchor="w", padx=12, pady=(0, 10))

    # Editor font size (applies after Apply)
    row = ttk.Frame(app_sf.inner); row.pack(fill="x", padx=12, pady=(0, 10))
    ttk.Label(row, text="Editor font size:").pack(side="left")
    font_var = tk.IntVar(value=int(self.prefs.get("editor_font_size", 11) or 11))
    ttk.Spinbox(row, from_=8, to=24, textvariable=font_var, width=6).pack(side="left", padx=(8, 0))
    ttk.Label(row, text="(updates instantly)").pack(side="left", padx=(8, 0))

    # Helper font family (affects Helper box only)
    helper_fonts = ["Consolas", "Courier New", "Segoe UI", "Arial", "Calibri", "Tahoma"]
    hf_row = ttk.Frame(app_sf.inner); hf_row.pack(fill="x", padx=12, pady=(0, 10))
    ttk.Label(hf_row, text="Helper font:").pack(side="left")
    helper_font_var = tk.StringVar(value=str(self.prefs.get("helper_font_family") or "Consolas"))
    hf_combo = ttk.Combobox(hf_row, textvariable=helper_font_var, values=helper_fonts, state="readonly", width=20)
    hf_combo.pack(side="left", padx=(8, 0))

    ttk.Separator(app_sf.inner).pack(fill="x", padx=12, pady=10)

    # Theme colours (Custom mode)
    ttk.Label(app_sf.inner, text="Theme colours", font=("Segoe UI", 11, "bold")).pack(anchor="w", padx=12, pady=(0, 6))
    ttk.Label(app_sf.inner, text="Custom mode only. These control UI + editor colours.", wraplength=900).pack(anchor="w", padx=12, pady=(0, 8))

    fields = [("bg","Window background"),("panel","Panel background"),("panel2","Secondary panel"),("text","Main text"),("muted","Muted text"),("entry","Entry/dropdown background"),("border","Borders"),("editor_bg","Editor background"),("editor_fg","Editor text")]
    color_vars: Dict[str, tk.StringVar] = {}
    try:
        mode_var.trace_add("write", _on_mode_change)
    except Exception:
        pass
    base_theme = DEFAULT_THEME_DARK if self.prefs.get("mode")=="dark" else DEFAULT_THEME_LIGHT
    cur_theme = dict(base_theme)
    saved_custom = dict(self.prefs.get("custom_theme", {}) or {})
    # If Custom was enabled while in Light mode and the user hasn't customised yet,
    # the stored default custom theme may still be Dark defaults. Don't let that force Dark styling.
    if self.prefs.get("custom_theme_enabled", False) and self.prefs.get("mode")=="light" and saved_custom == dict(DEFAULT_THEME_DARK):
        saved_custom = {}
    cur_theme.update(saved_custom)
    grid = ttk.Frame(app_sf.inner); grid.pack(fill="x", padx=12, pady=(0, 12))

    theme_entries = []
    theme_buttons = []
    for r,(key,label) in enumerate(fields):
        ttk.Label(grid, text=label).grid(row=r, column=0, sticky="w", pady=4)
        v = tk.StringVar(value=str(cur_theme.get(key,""))); color_vars[key]=v
        e = ttk.Entry(grid, textvariable=v, width=18); e.grid(row=r, column=1, sticky="w", padx=(10,0), pady=4)
        theme_entries.append(e)
        def pick(k=key,var=v):
            col=colorchooser.askcolor(title=f"Choose {k}")
            if col and col[1]: var.set(col[1])
        b = ttk.Button(grid, text="Pick…", command=pick); b.grid(row=r, column=2, sticky="w", padx=(10,0), pady=4)
        theme_buttons.append(b)

    ttk.Separator(app_sf.inner).pack(fill="x", padx=12, pady=10)

    # Button colours (Custom mode)
    ttk.Label(app_sf.inner, text="Button colours", font=("Segoe UI", 11, "bold")).pack(anchor="w", padx=12, pady=(0, 6))
    ttk.Label(app_sf.inner, text="Custom mode only. Controls header + buttons + selection colours.", wraplength=900).pack(anchor="w", padx=12, pady=(0, 8))

    btn_vars: Dict[str, tk.StringVar] = {}
    cur_btn = dict(DEFAULT_BUTTON_COLORS); cur_btn.update(self.prefs.get("button_colors", {}))
    bgrid = ttk.Frame(app_sf.inner); bgrid.pack(fill="x", padx=12, pady=(0, 12))

    btn_entries = []
    btn_buttons = []
    keys=[
        ("header","Top header (app title bar)"),
        ("primary","Primary action (Quick Export)"),
        ("secondary","Standard buttons (Load / Convert / Settings)"),
        ("toolbar","Toolbar buttons (Heading / Bold / Undo / Redo)"),
        ("danger","Destructive buttons (Clear / Delete)"),
    ]
    for r,(key,label) in enumerate(keys):
        ttk.Label(bgrid, text=label).grid(row=r, column=0, sticky="w", pady=4)
        v=tk.StringVar(value=str(cur_btn.get(key,""))); btn_vars[key]=v
        e=ttk.Entry(bgrid, textvariable=v, width=18); e.grid(row=r, column=1, sticky="w", padx=(10,0), pady=4)
        btn_entries.append(e)
        def pick_btn(k=key,var=v):
            col=colorchooser.askcolor(title=f"Choose {k}")
            if col and col[1]: var.set(col[1])
        b=ttk.Button(bgrid, text="Pick…", command=pick_btn); b.grid(row=r, column=2, sticky="w", padx=(10,0), pady=4)
        btn_buttons.append(b)

    def _sync_custom_controls():
        is_custom = (mode_var.get() == "custom")
        state = "normal" if is_custom else "disabled"
        for w in theme_entries + btn_entries:
            try: w.configure(state=state)
            except Exception: pass
        for w in theme_buttons + btn_buttons:
            try: w.configure(state=state)
            except Exception: pass

    mode_var.trace_add("write", lambda *_: _sync_custom_controls())

    def _valid_preview_colour(raw: str) -> bool:
        return bool(re.fullmatch(r"#[0-9a-fA-F]{6}", (raw or "").strip()))

    def _collect_theme_preview_values() -> dict:
        base = dict(DEFAULT_THEME_DARK if self.prefs.get("mode") == "dark" else DEFAULT_THEME_LIGHT)
        base.update(self.prefs.get("custom_theme", {}) or {})
        for k, v in color_vars.items():
            raw = v.get().strip()
            if _valid_preview_colour(raw):
                base[k] = raw
        return base

    def _collect_button_preview_values() -> dict:
        base = dict(DEFAULT_BUTTON_COLORS)
        base.update(self.prefs.get("button_colors", {}) or {})
        for k, v in btn_vars.items():
            raw = v.get().strip()
            if _valid_preview_colour(raw):
                base[k] = raw
        return base

    def _apply_appearance_preview(*_):
        try:
            self.prefs["custom_theme_enabled"] = (mode_var.get() == "custom")
            if mode_var.get() in ("dark", "light"):
                self.prefs["mode"] = mode_var.get()
            try:
                self.prefs["editor_font_size"] = int(font_var.get())
            except Exception:
                pass
            self.prefs["helper_font_family"] = helper_font_var.get().strip() or "Consolas"
            self.prefs["custom_theme"] = _collect_theme_preview_values()
            self.prefs["button_colors"] = _collect_button_preview_values()
            self.apply_theme()
            colors = self.effective_colors()
            bg = colors["bg"]
            sf.set_canvas_bg(bg)
            prof_sf.set_canvas_bg(bg)
            app_sf.set_canvas_bg(bg)
            try:
                win.configure(bg=bg)
            except Exception:
                pass
            try:
                preview_btn = dict(DEFAULT_BUTTON_COLORS)
                preview_btn.update(self.prefs.get("button_colors", {}) or {})
                preview_selection_bg, preview_selection_fg = self._selection_palette(preview_btn.get("primary", DEFAULT_BUTTON_COLORS["primary"]))
                custom_list.configure(
                    bg=colors["panel2"],
                    fg=self._ensure_text_contrast(colors["panel2"], preferred=colors["text"], minimum=4.5),
                    selectbackground=preview_selection_bg,
                    selectforeground=preview_selection_fg,
                    highlightbackground=colors["border"],
                )
            except Exception:
                pass
        except Exception:
            pass

    _sync_custom_controls()
    try:
        mode_var.trace_add("write", _apply_appearance_preview)
        font_var.trace_add("write", _apply_appearance_preview)
        helper_font_var.trace_add("write", _apply_appearance_preview)
        for _v in color_vars.values():
            _v.trace_add("write", _apply_appearance_preview)
        for _v in btn_vars.values():
            _v.trace_add("write", _apply_appearance_preview)
    except Exception:
        pass

    # Reset Custom colours back to safe defaults (in case user breaks readability)
    reset_row = ttk.Frame(app_sf.inner); reset_row.pack(fill="x", padx=12, pady=(0, 12))

    def reset_default_colours():
        base_theme = dict(DEFAULT_THEME_DARK if self.prefs.get("mode") == "dark" else DEFAULT_THEME_LIGHT)
        for k, v in color_vars.items():
            v.set(str(base_theme.get(k, "") or ""))
        base_btn = dict(DEFAULT_BUTTON_COLORS)
        for k, v in btn_vars.items():
            v.set(str(base_btn.get(k, "") or ""))
        mode_var.set("custom")

    ttk.Button(reset_row, text="Reset default colours", command=reset_default_colours).pack(side="left")
    ttk.Label(reset_row, text="Resets Custom colours back to safe defaults.").pack(side="left", padx=(10, 0))
    tab_adv = ttk.Frame(nb); nb.add(tab_adv, text="Advanced")

    ttk.Label(tab_adv, text="Advanced", font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=12, pady=(12, 6))
    ttk.Label(tab_adv, text="Window size memory and other power options.",).pack(anchor="w", padx=12, pady=(0, 12))

    remember_var = tk.BooleanVar(value=bool(self.prefs.get("window_remember", True)))
    ttk.Checkbutton(tab_adv, text="Remember window size & position", variable=remember_var).pack(anchor="w", padx=12, pady=(0, 10))

    adv_btns = ttk.Frame(tab_adv); adv_btns.pack(fill="x", padx=12, pady=(0, 12))
    ttk.Button(adv_btns, text="Save current size as default", command=self.save_current_window_size).pack(side="left")
    ttk.Button(adv_btns, text="Clear saved window size", command=self.clear_saved_window_size).pack(side="left", padx=(8, 0))

    paths_frame = ttk.Labelframe(tab_adv, text="Export Root Overrides (built-in profiles)")
    paths_frame.pack(fill="both", expand=True, padx=12, pady=(0, 12))
    # Emulator paths tab
    ttk.Label(paths_frame, text="Export Root Overrides (optional)", font=("Segoe UI", 12, "bold")).grid(row=0, column=0, sticky="w", padx=12, pady=(12, 6))
    ttk.Label(paths_frame, text="Export Root is the default. Overrides are optional exceptions; they change only the export root.").grid(row=1, column=0, sticky="w", padx=12, pady=(0, 10))

    paths_frame.columnconfigure(0, weight=1)
    paths_frame.rowconfigure(2, weight=1)

    table = ttk.Frame(paths_frame)
    table.grid(row=2, column=0, sticky="nsew", padx=12, pady=(0, 10))
    table.columnconfigure(0, weight=1)
    table.rowconfigure(0, weight=1)

    tree = ttk.Treeview(table, columns=("profile", "path"), show="headings")
    tree.heading("profile", text="Profile")
    tree.heading("path", text="Export path override")
    tree.column("profile", width=320, anchor="w")
    tree.column("path", width=640, anchor="w")

    vsb = ttk.Scrollbar(table, orient="vertical", command=tree.yview)
    hsb = ttk.Scrollbar(table, orient="horizontal", command=tree.xview)
    tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

    tree.grid(row=0, column=0, sticky="nsew")
    vsb.grid(row=0, column=1, sticky="ns")
    hsb.grid(row=1, column=0, sticky="ew")

    btn_row = ttk.Frame(paths_frame)
    btn_row.grid(row=3, column=0, sticky="ew", padx=12, pady=(0, 10))

    sel_frame = ttk.LabelFrame(paths_frame, text="Edit selected override")
    sel_frame.grid(row=4, column=0, sticky="ew", padx=12, pady=(0, 12))
    sel_frame.columnconfigure(0, weight=1)

    sel_path_var = tk.StringVar(value="")

    ttk.Label(sel_frame, text="Override path (paste here or use Browse):").grid(row=0, column=0, sticky="w", padx=10, pady=(10, 4))
    sel_entry = ttk.Entry(sel_frame, textvariable=sel_path_var)
    sel_entry.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 10))

    row2 = ttk.Frame(sel_frame)
    row2.grid(row=2, column=0, sticky="ew", padx=10, pady=(0, 10))

    def refresh_paths():
        for i in tree.get_children():
            tree.delete(i)
        mp = self.prefs.get("emulator_paths", {}) or {}
        for prof_name in DEFAULT_PROFILES.keys():
            tree.insert("", "end", values=(prof_name, mp.get(prof_name, "")))

    def get_selected_profile():
        sel = tree.selection()
        if not sel:
            return None
        vals = tree.item(sel[0], "values")
        return vals[0] if vals else None

    def load_selected_into_entry(*_):
        prof_name = get_selected_profile()
        if not prof_name:
            sel_path_var.set("")
            return
        sel_path_var.set((self.prefs.get("emulator_paths", {}) or {}).get(prof_name, # noqa: E501
            ""))

    def save_entry_to_selected():
        prof_name = get_selected_profile()
        if not prof_name:
            messagebox.showinfo("Emulator paths", "Select a profile first.")
            return
        val = sel_path_var.get().strip()
        if val:
            self.prefs.setdefault("emulator_paths", {})[prof_name] = val
        else:
            self.prefs.setdefault("emulator_paths", {}).pop(prof_name, None)
        refresh_paths()
        for iid in tree.get_children():
            if tree.item(iid, "values")[0] == prof_name:
                tree.selection_set(iid)
                tree.see(iid)
                break

    def reset_selected_to_default():
        sel_path_var.set("")
        save_entry_to_selected()

    def browse_for_selected():
        prof_name = get_selected_profile()
        if not prof_name:
            messagebox.showinfo("Emulator paths", "Select a profile first.")
            return
        p = filedialog.askdirectory()
        if not p:
            return
        sel_path_var.set(p)
        save_entry_to_selected()

    def clear_selected():
        prof_name = get_selected_profile()
        if not prof_name:
            return
        self.prefs.setdefault("emulator_paths", {}).pop(prof_name, None)
        sel_path_var.set("")
        refresh_paths()

    def clear_all():
        self.prefs.setdefault("emulator_paths", {}).clear()
        sel_path_var.set("")
        refresh_paths()

    ttk.Button(btn_row, text="Browse…", command=browse_for_selected).pack(side="left")
    ttk.Button(btn_row, text="Clear selected", command=clear_selected).pack(side="left", padx=(8, 0))
    ttk.Button(btn_row, text="Clear ALL overrides", style="Danger.TButton", command=clear_all).pack(side="left", padx=(8, 0))

    ttk.Button(row2, text="Save override", command=save_entry_to_selected).pack(side="left")
    ttk.Button(row2, text="Reset to default", command=reset_selected_to_default).pack(side="left", padx=(8, 0))

    tree.bind("<<TreeviewSelect>>", load_selected_into_entry)
    refresh_paths()
    kids = tree.get_children()
    if kids:
        tree.selection_set(kids[0])
        tree.see(kids[0])
        load_selected_into_entry()
    bottom=ttk.Frame(sf.inner); bottom.pack(fill="x", padx=12, pady=(0,12))
    def apply_and_close():
        self.prefs["custom_theme_enabled"] = (mode_var.get() == "custom")
        if mode_var.get() in ("dark", "light"):
            self.prefs["mode"] = mode_var.get()
        self.prefs["window_remember"] = bool(remember_var.get())
        self.prefs["editor_font_size"] = int(font_var.get())
        self.prefs["helper_font_family"] = helper_font_var.get().strip() or "Consolas"
        self.prefs["custom_theme"] = _collect_theme_preview_values()
        self.prefs["button_colors"] = _collect_button_preview_values()
        save_prefs(self.prefs)
        self.apply_theme(); self._sync_core_dropdown()
        self.status.set("Settings saved.")
        win.destroy()


    # Apply settings even if the user closes the window via the X button.
    try:
        win.protocol("WM_DELETE_WINDOW", apply_and_close)
    except Exception:
        pass
    ttk.Button(bottom, text="Close", command=apply_and_close).pack(side="right")



