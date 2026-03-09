from __future__ import annotations

import os
import re
import tkinter as tk
import tkinter.font as tkfont
import webbrowser
from pathlib import Path
from typing import Dict, List, Optional

try:
    from tkinterdnd2 import DND_FILES, TkinterDnD  # type: ignore
    _HAS_DND = True
except Exception:
    TkinterDnD = None  # type: ignore
    DND_FILES = None  # type: ignore
    _HAS_DND = False

from tkinter import colorchooser, filedialog, messagebox, ttk

from .constants import (
    APP_DIR,
    APP_NAME,
    APP_TAGLINE,
    APP_VERSION,
    DEFAULT_BUTTON_COLORS,
    DEFAULT_PREFS,
    DEFAULT_PROFILES,
    DEFAULT_RETROARCH_CORES,
    DEFAULT_THEME_DARK,
    DEFAULT_THEME_LIGHT,
)
from .export_logic import (
    build_export_plan as build_export_plan_for_state,
    clean_hex as _clean_hex,
    extract_switch_metadata,
    normalize_bids,
    normalize_profile_id,
    prepare_export_text,
    profile_id_label,
    split_bids,
    validate_export_inputs,
)
from .storage import (
    ensure_demo_templates,
    list_templates,
    load_prefs,
    profile_templates_dir,
    read_template,
    save_prefs,
    write_template,
)
from .resources import asset_path
from .widgets import Scrollable, ToolTip, ask_text

class App:
    def __init__(self):
        ensure_demo_templates()
        self.prefs = load_prefs()
        self._audit_retroarch_cores()
        self.root = (TkinterDnD.Tk() if _HAS_DND else tk.Tk())
        self.root.title(f"{APP_NAME} — {APP_VERSION}")
        self.root.geometry("1200x820")
        self._brand_images = {}

        # Desktop-style right-click menu (Cut/Copy/Paste/Delete/Select All)
        self._ctx_menu = tk.Menu(self.root, tearoff=0)
        self._ctx_menu.add_command(label="Cut", command=lambda: self._ctx_action("cut"))
        self._ctx_menu.add_command(label="Copy", command=lambda: self._ctx_action("copy"))
        self._ctx_menu.add_command(label="Paste", command=lambda: self._ctx_action("paste"))
        self._ctx_menu.add_separator()
        self._ctx_menu.add_command(label="Delete", command=lambda: self._ctx_action("delete"))
        self._ctx_menu.add_command(label="Select All", command=lambda: self._ctx_action("select_all"))
        self._ctx_widget = None

        for cls in ("Entry", "Text", "TEntry"):
            try:
                self.root.bind_class(cls, "<Button-3>", self._show_ctx_menu, add="+")
                self.root.bind_class(cls, "<Shift-F10>", self._show_ctx_menu, add="+")
            except Exception:
                pass


        # Window size memory (keeps your design; just restores geometry)
        try:
            if self.prefs.get("window_remember", True) and self.prefs.get("window_geometry"):
                self.root.geometry(self.prefs.get("window_geometry"))
        except Exception:
            pass
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self._build_styles()
        self._load_brand_assets()

        self.header = tk.Frame(self.root, bg=self.prefs.get("button_colors", DEFAULT_BUTTON_COLORS).get("header", DEFAULT_BUTTON_COLORS["header"]))
        self.header.pack(fill="x")

        self.header_brand = tk.Frame(self.header, bg=self.header["bg"])
        self.header_brand.pack(side="left", padx=12, pady=6)
        self.header_mark = tk.Label(self.header_brand, bg=self.header["bg"])
        self.header_mark.pack(side="left", padx=(0, 10))
        self.header_titles = tk.Frame(self.header_brand, bg=self.header["bg"])
        self.header_titles.pack(side="left")
        self.header_title = tk.Label(self.header_titles, text=APP_NAME, bg=self.header["bg"], fg="#fff6e8", font=("Bahnschrift SemiBold", 14))
        self.header_title.pack(anchor="w")
        self.header_subtitle = tk.Label(self.header_titles, text=APP_TAGLINE, bg=self.header["bg"], fg="#ffd5b8", font=("Consolas", 8))
        self.header_subtitle.pack(anchor="w")

        self.btn_dark = tk.Button(self.header, text="Dark Mode", command=self.toggle_mode, bg=self.header["bg"], fg="#ffffff", relief="flat", activebackground=self.header["bg"], activeforeground="#ffffff")
        self.btn_templates = tk.Button(self.header, text="Templates...", command=self.open_templates, bg=self.header["bg"], fg="#ffffff", relief="flat", activebackground=self.header["bg"], activeforeground="#ffffff")
        self.btn_links = tk.Button(self.header, text="Help Links", command=self.open_help_links, bg=self.header["bg"], fg="#ffffff", relief="flat", activebackground=self.header["bg"], activeforeground="#ffffff")
        self.btn_settings = tk.Button(self.header, text="Settings", command=self.open_settings, bg=self.header["bg"], fg="#ffffff", relief="flat", activebackground=self.header["bg"], activeforeground="#ffffff")
        for b in (self.btn_settings, self.btn_links, self.btn_templates, self.btn_dark):
            b.pack(side="right", padx=8, pady=8)

        self._apply_brand_images()

        self.body = Scrollable(self.root)
        self.body.pack(fill="both", expand=True)

        pr = ttk.Frame(self.body.inner)
        pr.pack(fill="x", padx=10, pady=(10, 6))
        ttk.Label(pr, text="Emulator / Console:").pack(side="left")
        self.profile_var = tk.StringVar(value=self.get_profile_values()[0] if self.get_profile_values() else "")
        # Combined control: Emulator/Console dropdown + menu button (flush)
        combo_wrap = ttk.Frame(pr)
        combo_wrap.pack(side="left", padx=(8, 0))
        combo_wrap.columnconfigure(0, weight=1)
        self.profile_cb = ttk.Combobox(combo_wrap, textvariable=self.profile_var, values=self.get_profile_values(), state="readonly", width=42, style="Profile.TCombobox")
        self.profile_cb.grid(row=0, column=0, sticky="nsew")
        self.profile_sort_btn = ttk.Button(
            combo_wrap,
            text="☰",
            width=2,
            style="ProfileSort.TButton",
            command=lambda: self.open_profile_sort_menu(self.profile_sort_btn),
        )
        self.profile_sort_btn.grid(row=0, column=1, sticky="nsew", padx=(0, 0))

        self.profile_cb.bind("<<ComboboxSelected>>", lambda _e: self.refresh_profile_info())

        er = ttk.Frame(self.body.inner)
        er.pack(fill="x", padx=10, pady=(0, 8))
        ttk.Label(er, text="Export Root:").pack(side="left")
        self.export_var = tk.StringVar(value=self.prefs.get("export_root", str(APP_DIR)))
        ttk.Entry(er, textvariable=self.export_var, width=72).pack(side="left", padx=(8, 0))
        b_open = ttk.Button(er, text="Open Folder", command=self.open_export_root)
        b_open.pack(side="left", padx=(8, 0))
        self._tt(b_open, "Opens the Export Root folder in your file explorer.")
        ttk.Button(er, text="Change…", command=self.change_root).pack(side="left", padx=(8, 0))
        b_rst = ttk.Button(er, text="Reset Default", command=self.reset_export_root)
        b_rst.pack(side="left", padx=(8, 0))
        self._tt(b_rst, "Resets Export Root back to the default location.")
        self.info_var = tk.StringVar(value="Quick Export builds the folder layout for you. Convert & Save stays available when you want manual control.")
        self.info_label = ttk.Label(self.body.inner, textvariable=self.info_var)
        self.info_label.pack(anchor="w", padx=10, pady=(0, 10))

        self.helper = ttk.LabelFrame(self.body.inner, text="Helper")
        self.helper.pack(fill="x", padx=10, pady=(0, 10))

        self.helper_text = tk.StringVar(value="Select an emulator to see helper info.")

        self._helper_card = tk.Frame(self.helper, bd=1, relief="solid", highlightthickness=1)
        self._helper_card.grid(row=0, column=0, columnspan=10, sticky="ew", padx=10, pady=(8, 6))
        self._helper_display = tk.Label(
            self._helper_card,
            textvariable=self.helper_text,
            justify="left",
            anchor="nw",
            padx=0,
            pady=0,
        )
        self._helper_display.pack(fill="x", padx=12, pady=10)
        self.helper.bind("<Configure>", self._on_helper_configure, add="+")

        try:
            self.helper.columnconfigure(0, weight=1)
        except Exception:
            pass

        self.tid_var = tk.StringVar()
        self.bid_var = tk.StringVar()
        self.core_var = tk.StringVar(value=self.prefs.get("retroarch_core", DEFAULT_RETROARCH_CORES[0]))
        # Live export preview updates (uses unified export builder)
        self._preview_after = None
        try:
            for _v in (self.profile_var, self.export_var, self.tid_var, self.bid_var, self.core_var):
                try:
                    _v.trace_add("write", self._schedule_export_preview_update)
                except Exception:
                    pass
        except Exception:
            pass

        self._atmo_layout = tk.Frame(self.helper, bd=1, relief="solid", highlightthickness=1)
        self._atmo_layout.grid(row=1, column=0, columnspan=10, sticky="ew", padx=10, pady=(0, 4))
        self._atmo_title = tk.Label(self._atmo_layout, text="Atmosphere export layout", font=("Segoe UI", 9, "bold"))
        self._atmo_title.grid(row=0, column=0, sticky="w", padx=12, pady=(10, 0))
        self._atmo_hint = tk.Label(
            self._atmo_layout,
            text="The folder structure is fixed. Only TitleID and BuildID fields are editable.",
            justify="left",
            anchor="w",
        )
        self._atmo_hint.grid(row=1, column=0, sticky="ew", padx=12, pady=(2, 8))
        self._atmo_path_row = tk.Frame(self._atmo_layout)
        self._atmo_path_row.grid(row=2, column=0, sticky="w", padx=12, pady=(0, 8))
        self._atmo_prefix_1 = tk.Label(self._atmo_path_row, text="SD:/atmosphere/contents/")
        self._atmo_prefix_1.grid(row=0, column=0, sticky="w")
        self._atmo_tid_entry = ttk.Entry(self._atmo_path_row, textvariable=self.tid_var, width=18)
        self._atmo_tid_entry.grid(row=0, column=1, sticky="w", padx=(6, 6))
        self._atmo_prefix_2 = tk.Label(self._atmo_path_row, text="/cheats/")
        self._atmo_prefix_2.grid(row=0, column=2, sticky="w")
        self._atmo_bid_entry = ttk.Entry(self._atmo_path_row, textvariable=self.bid_var, width=28)
        self._atmo_bid_entry.grid(row=0, column=3, sticky="w", padx=(6, 6))
        self._atmo_suffix = tk.Label(self._atmo_path_row, text=".txt")
        self._atmo_suffix.grid(row=0, column=4, sticky="w")
        self._atmo_path_note = tk.Label(
            self._atmo_layout,
            text="BuildID changes when the game updates, but the Atmosphere folder layout itself stays fixed.",
            justify="left",
            anchor="w",
        )
        self._atmo_path_note.grid(row=3, column=0, sticky="ew", padx=12, pady=(0, 10))
        self._atmo_layout.grid_remove()

        self._switch_layout_title = tk.StringVar(value="Switch emulator layout")
        self._switch_layout_template = tk.StringVar(value="")
        self._switch_layout_note = tk.StringVar(value="")
        self._switch_layout = tk.Frame(self.helper, bd=1, relief="solid", highlightthickness=1)
        self._switch_layout.grid(row=1, column=0, columnspan=10, sticky="ew", padx=10, pady=(0, 4))
        self._switch_layout_heading = tk.Label(self._switch_layout, textvariable=self._switch_layout_title, font=("Segoe UI", 9, "bold"))
        self._switch_layout_heading.grid(row=0, column=0, sticky="w", padx=12, pady=(10, 0))
        self._switch_layout_hint = tk.Label(
            self._switch_layout,
            text="This target uses the emulator's folder pattern. Enter TitleID and BuildID(s) for the file it expects.",
            justify="left",
            anchor="w",
        )
        self._switch_layout_hint.grid(row=1, column=0, sticky="ew", padx=12, pady=(2, 8))
        self._switch_layout_template_frame = tk.Frame(self._switch_layout, bd=0, highlightthickness=0)
        self._switch_layout_template_frame.grid(row=2, column=0, sticky="ew", padx=12, pady=(0, 8))
        self._switch_layout_template_label = tk.Label(
            self._switch_layout_template_frame,
            textvariable=self._switch_layout_template,
            justify="left",
            anchor="w",
            font=("Consolas", 10, "bold"),
        )
        self._switch_layout_template_label.pack(fill="x", padx=10, pady=8)
        self._switch_inputs = tk.Frame(self._switch_layout)
        self._switch_inputs.grid(row=3, column=0, sticky="w", padx=12, pady=(0, 8))
        self._switch_tid_title = tk.Label(self._switch_inputs, text="TitleID (TID):")
        self._switch_tid_title.grid(row=0, column=0, sticky="w")
        self._switch_tid_entry = ttk.Entry(self._switch_inputs, textvariable=self.tid_var, width=18)
        self._switch_tid_entry.grid(row=0, column=1, sticky="w", padx=(8, 14))
        self._switch_bid_title = tk.Label(self._switch_inputs, text="BuildID(s) (BID):")
        self._switch_bid_title.grid(row=0, column=2, sticky="w")
        self._switch_bid_entry = ttk.Entry(self._switch_inputs, textvariable=self.bid_var, width=28)
        self._switch_bid_entry.grid(row=0, column=3, sticky="w", padx=(8, 0))
        self._switch_layout_note_label = tk.Label(
            self._switch_layout,
            textvariable=self._switch_layout_note,
            justify="left",
            anchor="w",
        )
        self._switch_layout_note_label.grid(row=4, column=0, sticky="ew", padx=12, pady=(0, 10))
        self._switch_layout.grid_remove()

        self._titleid_layout_title = tk.StringVar(value="ID-based export layout")
        self._titleid_layout_template = tk.StringVar(value="")
        self._titleid_layout_note = tk.StringVar(value="")
        self._titleid_field_label = tk.StringVar(value="TitleID / Game ID:")
        self._titleid_layout = tk.Frame(self.helper, bd=1, relief="solid", highlightthickness=1)
        self._titleid_layout.grid(row=1, column=0, columnspan=10, sticky="ew", padx=10, pady=(0, 4))
        self._titleid_layout_heading = tk.Label(self._titleid_layout, textvariable=self._titleid_layout_title, font=("Segoe UI", 9, "bold"))
        self._titleid_layout_heading.grid(row=0, column=0, sticky="w", padx=12, pady=(10, 0))
        self._titleid_hint = tk.Label(
            self._titleid_layout,
            text="This target uses a required ID for the cheat filename or export folder.",
            justify="left",
            anchor="w",
        )
        self._titleid_hint.grid(row=1, column=0, sticky="ew", padx=12, pady=(2, 8))
        self._titleid_template_frame = tk.Frame(self._titleid_layout, bd=0, highlightthickness=0)
        self._titleid_template_frame.grid(row=2, column=0, sticky="ew", padx=12, pady=(0, 8))
        self._titleid_template_label = tk.Label(
            self._titleid_template_frame,
            textvariable=self._titleid_layout_template,
            justify="left",
            anchor="w",
            font=("Consolas", 10, "bold"),
        )
        self._titleid_template_label.pack(fill="x", padx=10, pady=8)
        self._titleid_inputs = tk.Frame(self._titleid_layout)
        self._titleid_inputs.grid(row=3, column=0, sticky="w", padx=12, pady=(0, 8))
        self._titleid_label = tk.Label(self._titleid_inputs, textvariable=self._titleid_field_label)
        self._titleid_label.grid(row=0, column=0, sticky="w")
        self._titleid_entry = ttk.Entry(self._titleid_inputs, textvariable=self.tid_var, width=18)
        self._titleid_entry.grid(row=0, column=1, sticky="w", padx=(8, 0))
        self._titleid_note_label = tk.Label(
            self._titleid_layout,
            textvariable=self._titleid_layout_note,
            justify="left",
            anchor="w",
        )
        self._titleid_note_label.grid(row=4, column=0, sticky="ew", padx=12, pady=(0, 10))
        self._titleid_layout.grid_remove()

        self._retro_layout_template = tk.StringVar(value="")
        self._retro_layout_note = tk.StringVar(value="")
        self._retro_layout = tk.Frame(self.helper, bd=1, relief="solid", highlightthickness=1)
        self._retro_layout.grid(row=1, column=0, columnspan=10, sticky="ew", padx=10, pady=(0, 4))
        self._retro_layout_heading = tk.Label(self._retro_layout, text="RetroArch export layout", font=("Segoe UI", 9, "bold"))
        self._retro_layout_heading.grid(row=0, column=0, sticky="w", padx=12, pady=(10, 0))
        self._retro_layout_hint = tk.Label(
            self._retro_layout,
            text="Choose the core folder first. Quick Export then places the cheat in RetroArch's cheats layout.",
            justify="left",
            anchor="w",
        )
        self._retro_layout_hint.grid(row=1, column=0, sticky="ew", padx=12, pady=(2, 8))
        self._retro_layout_template_frame = tk.Frame(self._retro_layout, bd=0, highlightthickness=0)
        self._retro_layout_template_frame.grid(row=2, column=0, sticky="ew", padx=12, pady=(0, 8))
        self._retro_layout_template_label = tk.Label(
            self._retro_layout_template_frame,
            textvariable=self._retro_layout_template,
            justify="left",
            anchor="w",
            font=("Consolas", 10, "bold"),
        )
        self._retro_layout_template_label.pack(fill="x", padx=10, pady=8)
        self._retro_inputs = tk.Frame(self._retro_layout)
        self._retro_inputs.grid(row=3, column=0, sticky="w", padx=12, pady=(0, 8))
        self._core_label = tk.Label(self._retro_inputs, text="RetroArch Core:")
        self._core_cb = ttk.Combobox(self._retro_inputs, textvariable=self.core_var, values=self.prefs.get("retroarch_cores", DEFAULT_RETROARCH_CORES), state="readonly", width=18)
        self._core_manage = ttk.Button(self._retro_inputs, text="Manage Cores...", command=self.manage_retroarch_cores)
        self._core_label.grid(row=0, column=0, sticky="w")
        self._core_cb.grid(row=0, column=1, sticky="w", padx=(8, 10))
        self._core_cb.bind("<<ComboboxSelected>>", lambda _e: self._save_retroarch_core())
        self._core_manage.grid(row=0, column=2, sticky="w")
        self._retro_layout_note_label = tk.Label(
            self._retro_layout,
            textvariable=self._retro_layout_note,
            justify="left",
            anchor="w",
        )
        self._retro_layout_note_label.grid(row=4, column=0, sticky="ew", padx=12, pady=(0, 10))
        self._retro_layout.grid_remove()

        self._generic_layout_title = tk.StringVar(value="Target export layout")
        self._generic_layout_template = tk.StringVar(value="")
        self._generic_layout_note = tk.StringVar(value="")
        self._generic_layout = tk.Frame(self.helper, bd=1, relief="solid", highlightthickness=1)
        self._generic_layout.grid(row=1, column=0, columnspan=10, sticky="ew", padx=10, pady=(0, 4))
        self._generic_layout_heading = tk.Label(self._generic_layout, textvariable=self._generic_layout_title, font=("Segoe UI", 9, "bold"))
        self._generic_layout_heading.grid(row=0, column=0, sticky="w", padx=12, pady=(10, 0))
        self._generic_layout_hint = tk.Label(
            self._generic_layout,
            text="This target keeps a fixed export pattern. Use Quick Export to build the folder or file layout for you.",
            justify="left",
            anchor="w",
        )
        self._generic_layout_hint.grid(row=1, column=0, sticky="ew", padx=12, pady=(2, 8))
        self._generic_layout_template_frame = tk.Frame(self._generic_layout, bd=0, highlightthickness=0)
        self._generic_layout_template_frame.grid(row=2, column=0, sticky="ew", padx=12, pady=(0, 8))
        self._generic_layout_template_label = tk.Label(
            self._generic_layout_template_frame,
            textvariable=self._generic_layout_template,
            justify="left",
            anchor="w",
            font=("Consolas", 10, "bold"),
        )
        self._generic_layout_template_label.pack(fill="x", padx=10, pady=8)
        self._generic_layout_note_label = tk.Label(
            self._generic_layout,
            textvariable=self._generic_layout_note,
            justify="left",
            anchor="w",
        )
        self._generic_layout_note_label.grid(row=3, column=0, sticky="ew", padx=12, pady=(0, 10))
        self._generic_layout.grid_remove()

        self.path_preview = tk.StringVar(value="")
        self._path_preview_label = ttk.Label(self.helper, textvariable=self.path_preview, justify="left")
        self._path_preview_label.grid(row=2, column=0, columnspan=10, sticky="w", padx=10, pady=(0, 8))

        self._set_helper_display(self.helper_text.get())

        tb = ttk.Frame(self.body.inner)
        tb.pack(fill="x", padx=10, pady=(0, 6))
        ttk.Button(tb, text="Heading", style="Toolbar.TButton", command=self.fmt_heading).pack(side="left")
        ttk.Button(tb, text="Bold", style="Toolbar.TButton", command=self.fmt_bold).pack(side="left", padx=(8, 0))
        ttk.Button(tb, text="Undo", style="Toolbar.TButton", command=self.do_undo).pack(side="left", padx=(8, 0))
        ttk.Button(tb, text="Redo", style="Toolbar.TButton", command=self.do_redo).pack(side="left", padx=(8, 0))
        ttk.Button(tb, text="Clear text", style="Danger.TButton", command=self.clear_editor).pack(side="left", padx=(8, 0))
        self.wrap_var = tk.BooleanVar(value=bool(self.prefs.get("wrap", True)))
        ttk.Checkbutton(tb, text="Wrap text", variable=self.wrap_var, command=self.toggle_wrap).pack(side="right")

        ttk.Label(self.body.inner, text="Cheat Editor", font=("Segoe UI", 11, "bold")).pack(anchor="w", padx=10, pady=(0, 6))
        ef = ttk.Frame(self.body.inner)
        ef.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.editor = tk.Text(ef, height=16, wrap=tk.WORD if self.wrap_var.get() else tk.NONE, undo=True, autoseparators=True, maxundo=4000)
        vs = ttk.Scrollbar(ef, orient="vertical", command=self.editor.yview)
        hs = ttk.Scrollbar(ef, orient="horizontal", command=self.editor.xview)
        self.editor.configure(yscrollcommand=vs.set, xscrollcommand=hs.set)
        # Drag-and-drop: drop a file onto the editor to load it (optional)
        if _HAS_DND:
            try:
                self.editor.drop_target_register(DND_FILES)
                self.editor.dnd_bind('<<Drop>>', self._on_drop_files)
            except Exception:
                pass

        self.editor.grid(row=0, column=0, sticky="nsew")
        vs.grid(row=0, column=1, sticky="ns")
        hs.grid(row=1, column=0, sticky="ew")
        ef.columnconfigure(0, weight=1)
        ef.rowconfigure(0, weight=1)
        self.editor.bind("<Control-z>", self.do_undo)
        self.editor.bind("<Control-y>", self.do_redo)
        self.editor.bind("<Control-Shift-Z>", self.do_redo)
        self.editor.bind("<Control-Shift-z>", self.do_redo)
        # Update export preview when editor content changes (cheat name/heading affects paths for some profiles)
        try:
            self.editor.bind("<<Modified>>", self._on_editor_modified)
            self.editor.edit_modified(False)
        except Exception:
            pass

        # Fixed bottom action bar (always visible)
        self.bottom_bar = ttk.Frame(self.root)
        self.bottom_bar.pack(side="bottom", fill="x")

        ar = ttk.Frame(self.bottom_bar)
        ar.pack(fill="x", padx=10, pady=(8, 6))

        # Bottom actions (left-to-right): Load → Quick Export → Convert & Save
        btn_lf = ttk.Button(ar, text="Load File…", command=self.load_file)
        btn_lf.pack(side="left")
        btn_qe = ttk.Button(ar, text="Quick Export", style="Primary.TButton", command=self.quick_export)
        btn_qe.pack(side="left", padx=(8, 0))
        btn_cs = ttk.Button(ar, text="Convert & Save…", command=self.convert_save)
        btn_cs.pack(side="left", padx=(8, 0))
        ToolTip(btn_qe, "Quick Export: builds the correct folder structure automatically for the selected profile.")
        ToolTip(btn_cs, "Convert & Save: save the editor text anywhere with any filename/extension.")
        ToolTip(btn_lf, "Load an existing cheat file into the editor (auto-detects profile fields where possible).")

        self.status = tk.StringVar(value="Ready.")
        ttk.Label(self.root, textvariable=self.status).pack(side="bottom", fill="x")

        self.apply_theme()
        self.refresh_profile_info()

    def _load_brand_assets(self):
        assets = {
            "window_icon": asset_path("app-icon.ico"),
            "icon_photo": asset_path("icon-256.png"),
            "header_mark": asset_path("mark-48.png"),
        }
        for key, path in assets.items():
            if not path.exists():
                continue
            if key == "window_icon":
                try:
                    self.root.iconbitmap(default=str(path))
                except Exception:
                    pass
                continue
            try:
                self._brand_images[key] = tk.PhotoImage(file=str(path))
            except Exception:
                pass
        icon_photo = self._brand_images.get("icon_photo")
        if icon_photo is not None:
            try:
                self.root.iconphoto(True, icon_photo)
            except Exception:
                pass

    def _apply_brand_images(self):
        header_mark = self._brand_images.get("header_mark")
        if header_mark is not None:
            self.header_mark.configure(image=header_mark, text="")
        else:
            self.header_mark.configure(text="[]", fg="#fff6e8", font=("Consolas", 12, "bold"))

    def _tt(self, widget, text: str):
        # Keep a reference so tooltips are not garbage-collected.
        if not hasattr(self, "_tooltips"):
            self._tooltips = []
        self._tooltips.append(ToolTip(widget, text))

    def _set_helper_display(self, txt: str) -> None:
        """Update the Helper display without making it look editable."""
        self.helper_text.set((txt or "").strip())
        self._on_helper_configure()

    def _on_helper_configure(self, event=None):
        try:
            width = getattr(event, "width", 0) or self.helper.winfo_width()
            wrap = max(320, width - 48)
            card_wrap = max(280, wrap - 24)
            self._helper_display.configure(wraplength=wrap)
            self._path_preview_label.configure(wraplength=wrap)
            self._atmo_hint.configure(wraplength=card_wrap)
            self._atmo_path_note.configure(wraplength=card_wrap)
            self._switch_layout_hint.configure(wraplength=card_wrap)
            self._switch_layout_note_label.configure(wraplength=card_wrap)
            self._switch_layout_template_label.configure(wraplength=card_wrap)
            self._titleid_hint.configure(wraplength=card_wrap)
            self._titleid_note_label.configure(wraplength=card_wrap)
            self._titleid_template_label.configure(wraplength=card_wrap)
            self._retro_layout_hint.configure(wraplength=card_wrap)
            self._retro_layout_note_label.configure(wraplength=card_wrap)
            self._retro_layout_template_label.configure(wraplength=card_wrap)
            self._generic_layout_hint.configure(wraplength=card_wrap)
            self._generic_layout_note_label.configure(wraplength=card_wrap)
            self._generic_layout_template_label.configure(wraplength=card_wrap)
        except Exception:
            pass

    def _estimate_helper_visible_chars(self) -> int:
        """Approximate how many characters fit in the Helper display area (depends on DPI/font/window)."""
        try:
            w = max(1, self._helper_display.winfo_width())
            h = max(1, self._helper_display.winfo_height())
            f = tkfont.Font(font=self._helper_display.cget("font"))
            avg_char = max(6, f.measure("0"))
            line_h = max(10, f.metrics("linespace"))
            # leave a little padding
            chars_per_line = max(1, int((w - 12) / avg_char))
            lines_visible = max(1, int((h - 6) / line_h))
            return int(chars_per_line * lines_visible)
        except Exception:
            # safe fallback that matches a small helper box
            return 240
    def _build_styles(self):
        style = ttk.Style(self.root)
        # Make dropdown + menu button look like one combined control
        try:
            style.configure("Profile.TCombobox", padding=(6, 3))
            # Keep the sort button tight so it doesn't become taller than the combobox
            # (this can vary by theme/packaged builds).
            style.configure("ProfileSort.TButton", padding=(4, 0))
        except Exception:
            pass
        try:
            style.theme_use("clam")
        except Exception:
            pass
        style.configure("TButton", padding=7, borderwidth=1, relief="solid")
        style.configure("Primary.TButton", padding=7, borderwidth=1, relief="solid")
        style.configure("Danger.TButton", padding=7, borderwidth=1, relief="solid")


    def get_profile_values(self):
        """Return profile list for the dropdown based on user preference."""
        names = list(DEFAULT_PROFILES.keys())
        custom = list((self.prefs.get("custom_profiles") or {}).keys())
        for n in custom:
            if n not in names:
                names.append(n)
        mode = (self.prefs.get("profile_sort") or "default").lower()
        if mode in ("az", "a-z", "alphabetical", "alpha"):
            return sorted(names, key=lambda s: s.casefold())
        # default order (as defined in DEFAULT_PROFILES)
        return names


    def get_profile_info(self, name: str) -> dict:
        """Return info for built-in or custom profile."""
        if name in DEFAULT_PROFILES:
            return dict(DEFAULT_PROFILES.get(name, {}))
        return dict((self.prefs.get("custom_profiles") or {}).get(name, {}))

    def refresh_profiles_dropdown(self):
        try:
            vals = self.get_profile_values()
            self.profile_cb["values"] = vals
            if self.profile_var.get() not in vals and vals:
                self.profile_var.set(vals[0])
        except Exception:
            pass

    def _build_profile_sort_menu(self):
        m = tk.Menu(self.root, tearoff=0)
        c = self.effective_colors()
        # Try to theme the menu for dark/light. (Some OS themes may limit this.)
        try:
            panel_fg = self._ensure_text_contrast(c["panel"], preferred=c["text"], minimum=4.5)
            active_fg = self._ensure_text_contrast(c["panel2"], preferred=c["text"], minimum=4.5)
            m.configure(
                bg=c["panel"],
                fg=panel_fg,
                activebackground=c["panel2"],
                activeforeground=active_fg,
                disabledforeground=self._ensure_text_contrast(c["panel"], preferred=c["muted"], minimum=3.0),
                bd=1,
                relief="solid",
            )
        except Exception:
            pass

        var = tk.StringVar(value=(self.prefs.get("profile_sort") or "default"))

        def set_mode(val: str):
            self.prefs["profile_sort"] = val
            save_prefs(self.prefs)
            cur = self.profile_var.get()
            values = self.get_profile_values()
            self.profile_cb.configure(values=values)
            # keep current selection if possible
            if cur in values:
                self.profile_var.set(cur)
            else:
                self.profile_var.set(values[0] if values else "")
            self.refresh_profile_info()

        m.add_radiobutton(label="Default order", variable=var, value="default", command=lambda: set_mode("default"))
        m.add_radiobutton(label="Alphabetical (A–Z)", variable=var, value="az", command=lambda: set_mode("az"))
        return m

    def open_profile_sort_menu(self, widget):
        if not hasattr(self, "_profile_sort_menu") or self._profile_sort_menu is None:
            self._profile_sort_menu = self._build_profile_sort_menu()
        else:
            # rebuild each time to re-apply theme + current selection
            self._profile_sort_menu = self._build_profile_sort_menu()
        try:
            x = widget.winfo_rootx()
            y = widget.winfo_rooty() + widget.winfo_height()
            self._profile_sort_menu.tk_popup(x, y)
        finally:
            try:
                self._profile_sort_menu.grab_release()
            except Exception:
                pass

    def effective_colors(self) -> dict:
        defaults = dict(DEFAULT_THEME_DARK if self.prefs.get("mode") == "dark" else DEFAULT_THEME_LIGHT)
        base = dict(defaults)
        if self.prefs.get("custom_theme_enabled"):
            base.update(self.prefs.get("custom_theme", {}))
        return self._sanitize_theme_colors(base, defaults)

    @staticmethod
    def _normalize_hex_color(value: str, fallback: str = "#000000") -> str:
        raw = (value or "").strip()
        if re.fullmatch(r"#[0-9a-fA-F]{6}", raw):
            return raw.lower()
        return fallback.lower()

    @classmethod
    def _relative_luminance(cls, color: str) -> float:
        value = cls._normalize_hex_color(color, "#000000").lstrip("#")
        rgb = [int(value[i:i + 2], 16) / 255.0 for i in (0, 2, 4)]

        def _linear(channel: float) -> float:
            return channel / 12.92 if channel <= 0.04045 else ((channel + 0.055) / 1.055) ** 2.4

        r, g, b = (_linear(channel) for channel in rgb)
        return (0.2126 * r) + (0.7152 * g) + (0.0722 * b)

    @classmethod
    def _contrast_ratio(cls, fg: str, bg: str) -> float:
        light = max(cls._relative_luminance(fg), cls._relative_luminance(bg))
        dark = min(cls._relative_luminance(fg), cls._relative_luminance(bg))
        return (light + 0.05) / (dark + 0.05)

    @classmethod
    def _blend_colors(cls, start: str, end: str, amount: float) -> str:
        start = cls._normalize_hex_color(start, "#000000").lstrip("#")
        end = cls._normalize_hex_color(end, "#000000").lstrip("#")
        amount = max(0.0, min(1.0, float(amount)))
        out = []
        for idx in (0, 2, 4):
            s = int(start[idx:idx + 2], 16)
            e = int(end[idx:idx + 2], 16)
            out.append(f"{round(s + ((e - s) * amount)):02x}")
        return f"#{''.join(out)}"

    @classmethod
    def _ensure_text_contrast(
        cls,
        bg: str,
        *,
        preferred: Optional[str] = None,
        light: str = "#fff8eb",
        dark: str = "#231b15",
        minimum: float = 4.5,
    ) -> str:
        bg = cls._normalize_hex_color(bg, "#ffffff")
        candidates = []
        if preferred:
            candidates.append(cls._normalize_hex_color(preferred, dark if cls._relative_luminance(bg) >= 0.5 else light))
        for candidate in (light, dark, "#ffffff", "#000000"):
            normalized = cls._normalize_hex_color(candidate, dark)
            if normalized not in candidates:
                candidates.append(normalized)
        if candidates and cls._contrast_ratio(candidates[0], bg) >= minimum:
            return candidates[0]
        return max(candidates, key=lambda candidate: cls._contrast_ratio(candidate, bg))

    @classmethod
    def _selection_palette(cls, accent: str, preferred_text: str = "#ffffff") -> tuple[str, str]:
        bg = cls._normalize_hex_color(accent, DEFAULT_BUTTON_COLORS["primary"])
        fg = cls._ensure_text_contrast(bg, preferred=preferred_text, minimum=4.5)
        return bg, fg

    @classmethod
    def _button_palette(
        cls,
        bg: str,
        surface_bg: str,
        preferred_text: str,
        *,
        minimum: float = 4.5,
        disabled_minimum: float = 3.0,
    ) -> dict:
        bg = cls._normalize_hex_color(bg, surface_bg)
        surface_bg = cls._normalize_hex_color(surface_bg, bg)
        fg = cls._ensure_text_contrast(bg, preferred=preferred_text, minimum=minimum)
        active_target = "#ffffff" if cls._relative_luminance(bg) < 0.45 else "#000000"
        active_bg = cls._blend_colors(bg, active_target, 0.14)
        active_fg = cls._ensure_text_contrast(active_bg, preferred=fg, minimum=minimum)
        disabled_bg = cls._blend_colors(bg, surface_bg, 0.42)
        disabled_pref = cls._blend_colors(fg, surface_bg, 0.45)
        disabled_fg = cls._ensure_text_contrast(disabled_bg, preferred=disabled_pref, minimum=disabled_minimum)
        border_target = "#000000" if cls._relative_luminance(bg) >= 0.55 else "#ffffff"
        border = cls._blend_colors(bg, border_target, 0.22)
        if cls._contrast_ratio(border, surface_bg) < 1.25:
            border = cls._blend_colors(surface_bg, fg, 0.3)
        focus = cls._blend_colors(bg, fg, 0.55)
        return {
            "bg": bg,
            "fg": fg,
            "active_bg": active_bg,
            "active_fg": active_fg,
            "disabled_bg": disabled_bg,
            "disabled_fg": disabled_fg,
            "border": border,
            "focus": focus,
        }

    @classmethod
    def _sanitize_theme_colors(cls, colors: dict, defaults: dict) -> dict:
        fixed = {key: cls._normalize_hex_color(colors.get(key, value), value) for key, value in defaults.items()}
        fixed["text"] = cls._ensure_text_contrast(fixed["bg"], preferred=fixed["text"], minimum=4.5)
        fixed["muted"] = cls._ensure_text_contrast(fixed["panel"], preferred=fixed["muted"], minimum=3.4)
        fixed["editor_fg"] = cls._ensure_text_contrast(fixed["editor_bg"], preferred=fixed["editor_fg"], minimum=4.5)
        if cls._contrast_ratio(fixed["panel2"], fixed["panel"]) < 1.08:
            shift = "#000000" if cls._relative_luminance(fixed["panel"]) >= 0.55 else "#ffffff"
            fixed["panel2"] = cls._blend_colors(fixed["panel"], shift, 0.08)
        if cls._contrast_ratio(fixed["entry"], fixed["panel"]) < 1.08:
            shift = "#000000" if cls._relative_luminance(fixed["panel"]) >= 0.55 else "#ffffff"
            fixed["entry"] = cls._blend_colors(fixed["panel"], shift, 0.06)
        if cls._contrast_ratio(fixed["border"], fixed["bg"]) < 1.2 and cls._contrast_ratio(fixed["border"], fixed["panel"]) < 1.2:
            fixed["border"] = cls._blend_colors(fixed["bg"], fixed["text"], 0.32)
        if cls._contrast_ratio(fixed["accent"], fixed["bg"]) < 2.2:
            shift = "#000000" if cls._relative_luminance(fixed["bg"]) >= 0.55 else "#ffffff"
            fixed["accent"] = cls._blend_colors(fixed["accent"], shift, 0.22)
        return fixed

    @classmethod
    def _readable_text_color(cls, bg: str, *, light: str = "#fff8eb", dark: str = "#231b15") -> str:
        preferred = dark if cls._relative_luminance(bg) >= 0.58 else light
        return cls._ensure_text_contrast(bg, preferred=preferred, light=light, dark=dark, minimum=4.5)

    def toggle_mode(self):
        self.prefs["mode"] = "dark" if self.prefs.get("mode") == "light" else "light"
        save_prefs(self.prefs)
        self.apply_theme()

    def apply_theme(self):
        c = self.effective_colors()
        btn = {key: self._normalize_hex_color(value, DEFAULT_BUTTON_COLORS[key]) for key, value in DEFAULT_BUTTON_COLORS.items()}
        btn.update({
            key: self._normalize_hex_color(value, DEFAULT_BUTTON_COLORS[key])
            for key, value in (self.prefs.get("button_colors", {}) or {}).items()
            if key in DEFAULT_BUTTON_COLORS
        })
        style = ttk.Style(self.root)
        selection_bg, selection_fg = self._selection_palette(btn.get("primary", DEFAULT_BUTTON_COLORS["primary"]))
        panel_text = self._ensure_text_contrast(c["panel"], preferred=c["text"], minimum=4.5)
        panel2_text = self._ensure_text_contrast(c["panel2"], preferred=c["text"], minimum=4.5)
        hint_fg = self._ensure_text_contrast(c["panel"], preferred=c["muted"], minimum=3.4)
        bg_hint_fg = self._ensure_text_contrast(c["bg"], preferred=c["muted"], minimum=3.4)
        entry_fg = self._ensure_text_contrast(c["entry"], preferred=c["text"], minimum=4.5)
        entry_disabled_bg = self._blend_colors(c["entry"], c["panel"], 0.25)
        entry_disabled_fg = self._ensure_text_contrast(
            entry_disabled_bg,
            preferred=self._blend_colors(entry_fg, c["panel"], 0.35),
            minimum=3.0,
        )
        style.configure(".", background=c["bg"], foreground=c["text"])
        style.configure("TFrame", background=c["bg"])
        style.configure("TLabel", background=c["bg"], foreground=c["text"])
        style.configure("TLabelframe", background=c["bg"], foreground=c["text"])
        style.configure("TLabelframe.Label", background=c["bg"], foreground=c["text"])
        style.configure("TCheckbutton", background=c["bg"], foreground=c["text"])
        style.map("TCheckbutton", foreground=[("disabled", bg_hint_fg)])
        style.configure("TRadiobutton", background=c["bg"], foreground=c["text"])
        style.map("TRadiobutton", foreground=[("disabled", bg_hint_fg)])
        style.configure("TEntry", fieldbackground=c["entry"], foreground=entry_fg)
        style.map(
            "TEntry",
            fieldbackground=[("disabled", entry_disabled_bg), ("readonly", c["entry"])],
            foreground=[("disabled", entry_disabled_fg), ("readonly", entry_fg)],
        )

        style.configure(
            "TCombobox",
            fieldbackground=c["entry"],
            background=c["entry"],
            foreground=entry_fg,
        )
        style.map(
            "TCombobox",
            fieldbackground=[("readonly", c["entry"]), ("disabled", entry_disabled_bg)],
            background=[("readonly", c["entry"]), ("disabled", entry_disabled_bg)],
            foreground=[("readonly", entry_fg), ("disabled", entry_disabled_fg)],
        )
        try:
            style.configure("TCombobox", arrowcolor=entry_fg, arrowsize=12)
            style.configure("Profile.TCombobox", arrowcolor=entry_fg, arrowsize=12)
            style.map("TCombobox", arrowcolor=[("readonly", entry_fg), ("disabled", entry_disabled_fg)])
            style.map("Profile.TCombobox", arrowcolor=[("readonly", entry_fg), ("disabled", entry_disabled_fg)])
        except Exception:
            pass

        style.configure("TSpinbox", fieldbackground=c["entry"], foreground=entry_fg)
        style.map(
            "TSpinbox",
            fieldbackground=[("disabled", entry_disabled_bg)],
            foreground=[("disabled", entry_disabled_fg)],
        )

        try:
            self.root.option_add("*TCombobox*Listbox.background", c["entry"])
            self.root.option_add("*TCombobox*Listbox.foreground", entry_fg)
            self.root.option_add("*TCombobox*Listbox.selectBackground", selection_bg)
            self.root.option_add("*TCombobox*Listbox.selectForeground", selection_fg)
        except Exception:
            pass

        style.configure(
            "Treeview",
            background=c["entry"],
            fieldbackground=c["entry"],
            foreground=entry_fg,
            bordercolor=c.get("border", c["panel2"]),
        )
        style.configure("Treeview.Heading", background=c["panel2"], foreground=panel2_text)
        style.map("Treeview", background=[("selected", selection_bg)], foreground=[("selected", selection_fg)])

        sec_bg = btn.get("secondary", c["panel"])
        if self.prefs.get("mode") == "dark" and sec_bg in ("#ffffff", "white"):
            sec_bg = c["panel"]
        sec_palette = self._button_palette(sec_bg, c["bg"], c["text"])
        style.configure(
            "TButton",
            background=sec_palette["bg"],
            foreground=sec_palette["fg"],
            bordercolor=sec_palette["border"],
            darkcolor=sec_palette["border"],
            lightcolor=sec_palette["active_bg"],
            focuscolor=sec_palette["focus"],
        )
        style.map(
            "TButton",
            background=[("disabled", sec_palette["disabled_bg"]), ("active", sec_palette["active_bg"])],
            foreground=[("disabled", sec_palette["disabled_fg"]), ("active", sec_palette["active_fg"])],
        )
        style.configure(
            "ProfileSort.TButton",
            background=sec_palette["bg"],
            foreground=sec_palette["fg"],
            bordercolor=sec_palette["border"],
            darkcolor=sec_palette["border"],
            lightcolor=sec_palette["active_bg"],
            focuscolor=sec_palette["focus"],
        )
        style.map(
            "ProfileSort.TButton",
            background=[("disabled", sec_palette["disabled_bg"]), ("active", sec_palette["active_bg"])],
            foreground=[("disabled", sec_palette["disabled_fg"]), ("active", sec_palette["active_fg"])],
        )

        toolbar_bg = btn.get("toolbar", sec_bg)
        if self.prefs.get("mode") == "dark" and toolbar_bg in ("#ffffff", "white"):
            toolbar_bg = c["panel"]
        toolbar_palette = self._button_palette(toolbar_bg, c["bg"], c["text"])
        style.configure(
            "Toolbar.TButton",
            background=toolbar_palette["bg"],
            foreground=toolbar_palette["fg"],
            bordercolor=toolbar_palette["border"],
            darkcolor=toolbar_palette["border"],
            lightcolor=toolbar_palette["active_bg"],
            focuscolor=toolbar_palette["focus"],
        )
        style.map(
            "Toolbar.TButton",
            background=[("disabled", toolbar_palette["disabled_bg"]), ("active", toolbar_palette["active_bg"])],
            foreground=[("disabled", toolbar_palette["disabled_fg"]), ("active", toolbar_palette["active_fg"])],
        )

        primary_bg = btn.get("primary", DEFAULT_BUTTON_COLORS["primary"])
        primary_palette = self._button_palette(primary_bg, c["bg"], "#ffffff")
        style.configure(
            "Primary.TButton",
            background=primary_palette["bg"],
            foreground=primary_palette["fg"],
            bordercolor=primary_palette["border"],
            darkcolor=primary_palette["border"],
            lightcolor=primary_palette["active_bg"],
            focuscolor=primary_palette["focus"],
        )
        style.map(
            "Primary.TButton",
            background=[("disabled", primary_palette["disabled_bg"]), ("active", primary_palette["active_bg"])],
            foreground=[("disabled", primary_palette["disabled_fg"]), ("active", primary_palette["active_fg"])],
        )

        danger_bg = btn.get("danger", DEFAULT_BUTTON_COLORS["danger"])
        danger_palette = self._button_palette(danger_bg, c["bg"], "#ffffff")
        style.configure(
            "Danger.TButton",
            background=danger_palette["bg"],
            foreground=danger_palette["fg"],
            bordercolor=danger_palette["border"],
            darkcolor=danger_palette["border"],
            lightcolor=danger_palette["active_bg"],
            focuscolor=danger_palette["focus"],
        )
        style.map(
            "Danger.TButton",
            background=[("disabled", danger_palette["disabled_bg"]), ("active", danger_palette["active_bg"])],
            foreground=[("disabled", danger_palette["disabled_fg"]), ("active", danger_palette["active_fg"])],
        )

        style.configure("TNotebook", background=c["bg"])
        style.configure("TNotebook.Tab", background=c["panel"], foreground=panel_text)
        style.map(
            "TNotebook.Tab",
            background=[("selected", c["panel2"]), ("active", c["panel2"])],
            foreground=[("selected", panel2_text), ("active", panel2_text)],
        )
        self.root.configure(bg=c["bg"])
        self.body.set_canvas_bg(c["bg"])

        menu_bg = c["panel"]
        menu_fg = panel_text
        menu_active_bg = self._blend_colors(c["panel2"], c["accent"], 0.18)
        menu_active_fg = self._ensure_text_contrast(menu_active_bg, preferred=c["text"], minimum=4.5)
        try:
            self._ctx_menu.configure(
                bg=menu_bg,
                fg=menu_fg,
                activebackground=menu_active_bg,
                activeforeground=menu_active_fg,
                disabledforeground=hint_fg,
                bd=1,
                relief="solid",
            )
        except Exception:
            pass

        header_bg = btn.get("header", btn.get("primary", DEFAULT_BUTTON_COLORS["header"]))
        header_palette = self._button_palette(header_bg, c["bg"], c["text"])
        header_fg = header_palette["fg"]
        subtitle_fg = self._ensure_text_contrast(
            header_bg,
            preferred=self._blend_colors(header_fg, header_bg, 0.35),
            minimum=3.2,
        )
        self.header.configure(bg=header_bg)
        self.header_brand.configure(bg=header_bg)
        self.header_titles.configure(bg=header_bg)
        self.header_mark.configure(bg=header_bg, fg=header_fg)
        self.header_title.configure(bg=header_bg, fg=header_fg)
        self.header_subtitle.configure(bg=header_bg, fg=subtitle_fg)
        for w in (self.btn_dark, self.btn_templates, self.btn_links, self.btn_settings):
            w.configure(
                bg=header_bg,
                fg=header_fg,
                activebackground=header_palette["active_bg"],
                activeforeground=header_palette["active_fg"],
                disabledforeground=header_palette["disabled_fg"],
                highlightbackground=header_palette["border"],
            )
        self.btn_dark.configure(text=("Light Mode" if self.prefs.get("mode") == "dark" else "Dark Mode"))
        self.editor.configure(
            bg=c["editor_bg"],
            fg=c["editor_fg"],
            insertbackground=c["editor_fg"],
            selectbackground=selection_bg,
            selectforeground=selection_fg,
            font=("Consolas", int(self.prefs.get("editor_font_size", 11) or 11)),
        )

        try:
            helper_font = str(self.prefs.get("helper_font_family") or "Consolas")
            self._helper_card.configure(bg=c["panel"], highlightbackground=c["border"], highlightcolor=c["border"])
            self._helper_display.configure(bg=c["panel"], fg=panel_text, font=(helper_font, 10))
            for card in (self._atmo_layout, self._switch_layout, self._titleid_layout, self._retro_layout, self._generic_layout):
                card.configure(bg=c["panel"], highlightbackground=c["border"], highlightcolor=c["border"])
            for subframe in (
                self._atmo_path_row,
                self._switch_layout_template_frame,
                self._switch_inputs,
                self._titleid_template_frame,
                self._titleid_inputs,
                self._retro_layout_template_frame,
                self._retro_inputs,
                self._generic_layout_template_frame,
            ):
                subframe.configure(bg=c["panel2"] if subframe in (self._atmo_path_row, self._switch_layout_template_frame, self._retro_layout_template_frame, self._generic_layout_template_frame) else c["panel"])
            for heading in (
                self._atmo_title,
                self._switch_layout_heading,
                self._titleid_layout_heading,
                self._retro_layout_heading,
                self._generic_layout_heading,
            ):
                heading.configure(bg=c["panel"], fg=panel_text)
            for hint in (
                self._atmo_hint,
                self._atmo_path_note,
                self._switch_layout_hint,
                self._switch_layout_note_label,
                self._titleid_hint,
                self._titleid_note_label,
                self._retro_layout_hint,
                self._retro_layout_note_label,
                self._generic_layout_hint,
                self._generic_layout_note_label,
            ):
                hint.configure(bg=c["panel"], fg=hint_fg)
            for template_label in (
                self._switch_layout_template_label,
                self._titleid_template_label,
                self._retro_layout_template_label,
                self._generic_layout_template_label,
            ):
                template_label.configure(bg=c["panel2"], fg=panel2_text, font=("Consolas", 10, "bold"))
            for w in (self._atmo_prefix_1, self._atmo_prefix_2, self._atmo_suffix):
                w.configure(bg=c["panel2"], fg=panel2_text, font=("Consolas", 10, "bold"))
            for w in (self._switch_tid_title, self._switch_bid_title, self._titleid_label, self._core_label):
                w.configure(bg=c["panel"], fg=panel_text)
            self._on_helper_configure()
        except Exception:
            pass

    def _show_tid_bid(self, show: bool):
        if show:
            self._switch_layout.grid()
        else:
            self._switch_layout.grid_remove()

    def _show_titleid_layout(self, show: bool):
        if show:
            self._titleid_layout.grid()
        else:
            self._titleid_layout.grid_remove()

    def _show_core(self, show: bool):
        if show:
            self._retro_layout.grid()
        else:
            self._retro_layout.grid_remove()

    def _show_generic_layout(self, show: bool):
        if show:
            self._generic_layout.grid()
        else:
            self._generic_layout.grid_remove()

    def _show_atmosphere_layout(self, show: bool):
        if show:
            self._atmo_layout.grid()
        else:
            self._atmo_layout.grid_remove()

    def _is_atmosphere_profile(self, prof: str, info: Optional[dict] = None) -> bool:
        info = info or self.get_profile_info(prof)
        subdir = (info.get("subdir") or "").replace("\\", "/").lower()
        return subdir.startswith("atmosphere/contents/")

    def _primary_extension(self, info: dict) -> str:
        exts = info.get("extensions") or []
        if not exts:
            return ".txt"
        ext = (exts[0] or ".txt").strip()
        if not ext:
            return ".txt"
        return ext if ext.startswith(".") else f".{ext}"

    def _uses_id_layout(self, info: dict) -> bool:
        return info.get("kind", "generic") in {"titleid", "idfile"}

    def _profile_id_field_label(self, info: dict) -> str:
        return f"{profile_id_label(info)}:"

    def _profile_id_hint(self, info: dict) -> str:
        return (info.get("titleid_hint") or info.get("id_hint") or "Use the ID this target expects.").strip()

    def _profile_template_path(self, prof: str, info: dict) -> str:
        if self._is_atmosphere_profile(prof, info):
            return "SD:/atmosphere/contents/<TID>/cheats/<BID>.txt"

        kind = info.get("kind", "generic")
        ext = self._primary_extension(info)
        fixed_filename = (info.get("fixed_filename") or "").strip()
        subdir = (info.get("subdir") or "").strip().replace("\\", "/")

        if kind == "retroarch":
            core = (self.core_var.get() or "").strip()
            base = "Export Root/RetroArch/cheats"
            if core and core.casefold() != "default (no subfolder)":
                base += f"/{core}"
            return f"{base}/<Game>{ext}"

        if fixed_filename:
            filename = fixed_filename
        else:
            hint = (info.get("filename_hint") or "<File>").strip() or "<File>"
            filename = hint if hint.lower().endswith(ext.lower()) else f"{hint}{ext}"

        if subdir:
            return f"Export Root/{subdir}/{filename}" if filename else f"Export Root/{subdir}"
        return f"Export Root/{filename}" if filename else "Export Root"

    def _refresh_target_cards(self, prof: str, info: dict) -> None:
        kind = info.get("kind", "generic")
        ext_text = " ".join(info.get("extensions") or [self._primary_extension(info)])

        if self._is_atmosphere_profile(prof, info):
            return

        if kind == "switch":
            self._switch_layout_title.set(f"{prof} layout")
            self._switch_layout_template.set(self._profile_template_path(prof, info))
            self._switch_layout_note.set(
                "TID selects the title folder. BID is usually the cheat file name and can change when the game updates. "
                f"File types: {ext_text}"
            )
            return

        if self._uses_id_layout(info):
            self._titleid_layout_title.set(f"{prof} layout")
            self._titleid_field_label.set(self._profile_id_field_label(info))
            self._titleid_hint.configure(text=self._profile_id_hint(info) or "Use the ID this target expects.")
            self._titleid_layout_template.set(self._profile_template_path(prof, info))
            note = self._profile_id_hint(info) or "Use the ID this target expects."
            if info.get("citra_enabled"):
                note += " Quick Export adds *citra_enabled if it is missing."
            elif info.get("fixed_filename"):
                note += " The folder uses that ID, while the cheat file name itself stays fixed."
            else:
                note += " Quick Export writes one file for that ID."
            self._titleid_layout_note.set(f"{note} File types: {ext_text}")
            return

        if kind == "retroarch":
            current_core = (self.core_var.get() or "Default (no subfolder)").strip() or "Default (no subfolder)"
            self._retro_layout_template.set(self._profile_template_path(prof, info))
            if current_core.casefold() == "default (no subfolder)":
                core_note = "Current core folder: Default (no subfolder)."
            else:
                core_note = f"Current core folder: {current_core}."
            self._retro_layout_note.set(f"{core_note} File types: {ext_text}")
            return

        self._generic_layout_title.set(f"{prof} layout")
        self._generic_layout_template.set(self._profile_template_path(prof, info))
        if kind == "singlefile":
            note = "This target exports one fixed file under the selected Export Root."
        elif kind == "modded":
            note = "Point Export Root or Emulator Paths at the SD or homebrew folder you actually want to target."
        else:
            note = "Quick Export builds the folder and filename pattern above under the selected Export Root."
        self._generic_layout_note.set(f"{note} File types: {ext_text}")

    def refresh_profile_info(self):
        prof = self.profile_var.get()
        info = self.get_profile_info(prof)
        kind = info.get("kind", "generic")
        is_atmosphere = self._is_atmosphere_profile(prof, info)

        self._refresh_target_cards(prof, info)

        if is_atmosphere:
            self._show_atmosphere_layout(True)
            self._show_tid_bid(False)
            self._show_titleid_layout(False)
            self._show_core(False)
            self._show_generic_layout(False)
        elif kind == "switch":
            self._show_atmosphere_layout(False)
            self._show_tid_bid(True)
            self._show_titleid_layout(False)
            self._show_core(False)
            self._show_generic_layout(False)
        elif self._uses_id_layout(info):
            self._show_atmosphere_layout(False)
            self._show_tid_bid(False)
            self._show_titleid_layout(True)
            self._show_core(False)
            self._show_generic_layout(False)
        elif kind == "retroarch":
            self._show_atmosphere_layout(False)
            self._show_tid_bid(False)
            self._show_titleid_layout(False)
            self._show_core(True)
            self._show_generic_layout(False)
        else:
            self._show_atmosphere_layout(False)
            self._show_tid_bid(False)
            self._show_titleid_layout(False)
            self._show_core(False)
            self._show_generic_layout(True)

        notes = (info.get("notes") or "").strip()
        if is_atmosphere:
            base = "Atmosphere exports use a fixed folder layout. Fill in TitleID and BuildID below."
        elif kind == "switch":
            base = notes or "Switch emulator exports follow the target layout shown below. Fill in TitleID and BuildID(s) for the selected target."
        elif self._uses_id_layout(info):
            base = notes or f"This target exports by {profile_id_label(info)} instead of using a free-form filename."
        elif kind == "retroarch":
            base = notes or "RetroArch exports are grouped by core folder, then saved as a cheat file for the selected game."
        else:
            base = notes or "Quick Export builds the target layout shown below using the selected Export Root."

        exts = info.get("extensions", [".txt"]) or [".txt"]
        ext_line = "Expected file types: " + " ".join(exts)
        if is_atmosphere:
            tip_line = "Tip: only the TID and BID boxes are editable for Atmosphere exports."
        elif kind == "switch":
            tip_line = "Tip: the template card shows the target's folder pattern while TID and BID stay editable."
        elif self._uses_id_layout(info):
            tip_line = f"Tip: enter the {profile_id_label(info)} and Quick Export builds the final cheat path for you."
        elif kind == "retroarch":
            tip_line = "Tip: choose the core here before exporting so the file lands in the right cheat folder."
        else:
            tip_line = "Tip: Convert & Save still works when you want a manual filename or location."
        self._set_helper_display(base + "\n\n" + ext_line + "\n" + tip_line)
        self.update_export_preview()

    def fmt_heading(self):
        try:
            line_start = self.editor.index("insert linestart")
            cur = self.editor.get(line_start, f"{line_start} lineend")
            if cur.lstrip().startswith("#"):
                return
            self.editor.insert(line_start, "# ")
        except Exception:
            pass

    def fmt_bold(self):
        try:
            if self.editor.tag_ranges(tk.SEL):
                s = self.editor.get(tk.SEL_FIRST, tk.SEL_LAST)
                self.editor.delete(tk.SEL_FIRST, tk.SEL_LAST)
                self.editor.insert(tk.INSERT, f"*{s}*")
            else:
                self.editor.insert(tk.INSERT, "**")
                self.editor.mark_set(tk.INSERT, f"{self.editor.index(tk.INSERT)}-1c")
        except Exception:
            pass

    def do_undo(self, *_):
        try: self.editor.edit_undo()
        except Exception: pass

    def do_redo(self, *_):
        try: self.editor.edit_redo()
        except Exception: pass

    def clear_editor(self):
        if messagebox.askyesno(
            "Clear editor text",
            "This will remove all text from the editor only.\n\nTemplates, settings, and files on disk will NOT be affected.\n\nDo you want to continue?",
        ):
            try: self.editor.edit_separator()
            except Exception: pass
            self.editor.delete("1.0", tk.END)

    def toggle_wrap(self):
        self.prefs["wrap"] = bool(self.wrap_var.get())
        save_prefs(self.prefs)
        self.editor.configure(wrap=tk.WORD if self.wrap_var.get() else tk.NONE)

    def change_root(self):
        p = filedialog.askdirectory()
        if not p: return
        self.export_var.set(p)
        self.prefs["export_root"] = p
        save_prefs(self.prefs)
        self.status.set(f"Export root set: {p}")

    def open_export_root(self):
        p = Path(self.export_var.get() or self.prefs.get("export_root", str(APP_DIR)))
        try: os.startfile(p)  # type: ignore[attr-defined]
        except Exception: messagebox.showinfo("Export Root", str(p))

    def reset_export_root(self):
        self.export_var.set(str(APP_DIR))
        self.prefs["export_root"] = str(APP_DIR)
        save_prefs(self.prefs)
        self.status.set("Export root reset to default.")

    def _effective_export_root_for_profile(self, prof: str) -> Path:
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

    def _get_all_known_extensions(self):
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

    def _pick_extension_for_save(self, prof: str):
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

    def convert_save(self):
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



    def load_file(self, filepath: Optional[str] = None):
        # Load an existing cheat file into the editor (safe: editor-only)
        if not filepath:
            filepath = filedialog.askopenfilename(
                title="Load cheat file",
                filetypes=[("Cheat files", "*.txt *.cht *.ini *.pnach *.yml *.yaml *.json *.xml *.dat"), ("All files", "*.*")]
            )
        if not filepath:
            return
        p = Path(filepath)
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
        except Exception:
            try:
                text = p.read_text(encoding="latin-1", errors="replace")
            except Exception as e:
                messagebox.showerror("Load File", f"Could not read file:\n{p}\n\n{e}")
                return

        # Fill editor
        self.editor.delete("1.0", tk.END)
        self.editor.insert("1.0", text)
        self.status.set(f"Loaded: {p.name}")

        # Best-effort auto-detect (never destructive)
        s = str(p).replace("\\", "/")
        sl = s.lower()
        fname = p.name.lower()

        # 3DS Citra core: .../RetroArch/saves/Citra/cheats/<TitleID>.txt
        if "/saves/citra/cheats/" in sl and p.suffix.lower() == ".txt":
            try:
                title_id = _clean_hex(p.stem)
                if len(title_id) == 16:
                    self.tid_var.set(title_id)
                citra_name = "Citra (3DS) - PC"
                if citra_name in self.get_profile_values():
                    self.profile_var.set(citra_name)
                    try:
                        self.profile_cb.set(citra_name)
                    except Exception:
                        pass
            except Exception:
                pass

        # 3DS Luma / CTRPF plugin layout: .../luma/plugins/<TitleID>/cheats.txt
        if "/luma/plugins/" in sl and fname == "cheats.txt":
            try:
                tid_raw = sl.split("/luma/plugins/")[-1].split("/")[0]
                title_id = _clean_hex(tid_raw)
                if len(title_id) == 16:
                    self.tid_var.set(title_id)
                luma_name = "Nintendo 3DS (CFW) (Luma)"
                if luma_name in self.get_profile_values():
                    self.profile_var.set(luma_name)
                    try:
                        self.profile_cb.set(luma_name)
                    except Exception:
                        pass
            except Exception:
                pass

        # RetroArch: .../cheats/<core>/<game>.cht  (core folder matters for auto-load)
        if "/cheats/" in sl and p.suffix.lower() == ".cht" and "/duckstation/" not in sl:
            try:
                # Smarter detection:
                # - Works for different RetroArch install roots (Android/PC)
                # - Supports both /cheats/<game>.cht and /cheats/<core>/<game>.cht
                # - Keeps user's core list unchanged (no auto-adding unknown cores)
                parts_orig = s.replace("\\", "/").split("/")
                parts_low = [part.lower() for part in parts_orig]

                default_core_name = "Default (no subfolder)"
                core_folder = ""
                if "cheats" in parts_low:
                    i = len(parts_low) - 1 - parts_low[::-1].index("cheats")  # last occurrence
                    remaining = parts_orig[i + 1 :]
                    if len(remaining) >= 2:
                        core_folder = (remaining[0] or "").strip()
                    elif len(remaining) == 1:
                        core_folder = default_core_name

                def _norm_core(x: str) -> str:
                    x = (x or "").strip().casefold()
                    # treat hyphen/underscore/multiple spaces as equivalent
                    x = re.sub(r"[-_]+", " ", x)
                    x = re.sub(r"\s+", " ", x).strip()
                    return x

                if core_folder:
                    retro_name = "RetroArch (Multi-platform)"
                    if retro_name in self.get_profile_values():
                        self.profile_var.set(retro_name)
                        try:
                            self.profile_cb.set(retro_name)
                        except Exception:
                            pass

                    cores = list(self.prefs.get("retroarch_cores", DEFAULT_RETROARCH_CORES) or [])
                    want = _norm_core(core_folder)

                    matched_name = ""
                    for c in cores:
                        if _norm_core(c) == want:
                            matched_name = c
                            break

                    if matched_name:
                        self.core_var.set(matched_name)
                        self._show_core(True)
                        self.status.set(f"Detected RetroArch core: {matched_name}")
                    elif want == _norm_core(default_core_name):
                        self.core_var.set(default_core_name)
                        self._show_core(True)
                        self.status.set(f"Detected RetroArch core: {default_core_name}")
                    elif len(remaining) >= 2:
                        # Don't change the user's list automatically (no surprise edits).
                        self._show_core(True)
                        self.status.set(f"Detected RetroArch core folder '{core_folder}', but it isn't in your core list.")
            except Exception:
                pass


        # Atmosphère: .../atmosphere/contents/<TID>/cheats/<BID>.txt
        if "/atmosphere/contents/" in sl and "/cheats/" in sl:
            try:
                tid_raw = sl.split("/atmosphere/contents/")[-1].split("/")[0]
                tid = _clean_hex(tid_raw)
                if len(tid) == 16:
                    self.tid_var.set(tid)

                # Atmosphère BuildID is commonly 32 hex, but some sources show 16.
                bid = _clean_hex(p.stem)
                if len(bid) in (16, 32):
                    self.bid_var.set(bid)

                # Auto-switch profile to Atmosphère
                atm_name = "Atmosphère (Switch) (CFW)"
                if atm_name in self.get_profile_values():
                    self.profile_var.set(atm_name)
                    try:
                        self.profile_cb.set(atm_name)
                    except Exception:
                        pass
            except Exception:
                pass


        # Switch emulator patterns: .../load/<TID>/cheats/<BID>.txt or Ryujinx mods/contents/<TID>/cheats/<BID>.txt
        if "/load/" in sl and "/cheats/" in sl:
            try:
                tid_raw = sl.split("/load/")[-1].split("/")[0]
                tid = _clean_hex(tid_raw)
                if len(tid) == 16:
                    self.tid_var.set(tid)

                bid = _clean_hex(p.stem)
                if len(bid) in (16, 32):
                    self.bid_var.set(bid)

                # Best-effort emulator auto-switch based on path segment.
                if "/yuzu/" in sl:
                    name = "Yuzu (Switch) - PC"
                elif "/sudachi/" in sl:
                    name = "Sudachi (Switch) - PC"
                elif "/suyu/" in sl:
                    name = "Suyu (Switch) - PC"
                else:
                    name = ""
                if name and name in self.get_profile_values():
                    self.profile_var.set(name)
                    try:
                        self.profile_cb.set(name)
                    except Exception:
                        pass
            except Exception:
                pass
        if "/mods/contents/" in sl and "/cheats/" in sl:
            try:
                tid_raw = sl.split("/mods/contents/")[-1].split("/")[0]
                tid = _clean_hex(tid_raw)
                if len(tid) == 16:
                    self.tid_var.set(tid)

                bid = _clean_hex(p.stem)
                if len(bid) in (16, 32):
                    self.bid_var.set(bid)

                ry_name = "Ryujinx (Switch) - PC"
                if ry_name in self.get_profile_values():
                    self.profile_var.set(ry_name)
                    try:
                        self.profile_cb.set(ry_name)
                    except Exception:
                        pass
            except Exception:
                pass


        # Header fallback (CheatSlips / text headers): look for TID/BID inside the first lines.
        # This is Switch-focused and helps first-time users who download cheats as plain text.
        try:
            metadata = extract_switch_metadata(text)
            current_bids = normalize_bids(self.bid_var.get())
            merged_bids = list(current_bids)

            if len(_clean_hex(self.tid_var.get())) != 16 and metadata["tid"]:
                self.tid_var.set(metadata["tid"])

            for bid in metadata["bids"]:
                if bid not in merged_bids:
                    merged_bids.append(bid)
            if merged_bids:
                self.bid_var.set(", ".join(merged_bids))

            # Only prefer Atmosphere when the text actually looks Switch-specific.
            if metadata["bids"] and len(_clean_hex(self.tid_var.get())) == 16:
                atm_name = "Atmosphère (Switch) (CFW)"
                if atm_name in self.get_profile_values():
                    self.profile_var.set(atm_name)
                    try:
                        self.profile_cb.set(atm_name)
                    except Exception:
                        pass
        except Exception:
            pass


        # Generic profile auto-detect (best-effort, non-destructive)
        try:
            sl2 = sl

            def _set_profile_id_from_filename(profile_name: str, raw_value: str) -> None:
                normalized = normalize_profile_id(self.get_profile_info(profile_name), raw_value)
                if normalized:
                    self.tid_var.set(normalized)

            # PCSX2 (.pnach)
            if fname.endswith(".pnach") and "PCSX2 (PS2) - PC" in self.get_profile_values():
                self.profile_var.set("PCSX2 (PS2) - PC")
                _set_profile_id_from_filename("PCSX2 (PS2) - PC", p.stem)

            # Dolphin GameSettings (.ini)
            if "/gamesettings/" in sl2 and fname.endswith(".ini") and "Dolphin (GC/Wii) - PC" in self.get_profile_values():
                self.profile_var.set("Dolphin (GC/Wii) - PC")
                _set_profile_id_from_filename("Dolphin (GC/Wii) - PC", p.stem)

            # PPSSPP cheats (.ini) commonly in memstick/PSP/Cheats
            if ("/psp/cheats/" in sl2 or "/memstick/psp/cheats/" in sl2) and fname.endswith(".ini") and "PPSSPP (PSP) - PC" in self.get_profile_values():
                self.profile_var.set("PPSSPP (PSP) - PC")
                _set_profile_id_from_filename("PPSSPP (PSP) - PC", p.stem)

            # DuckStation (.cht)
            if "/duckstation/" in sl2 and "/cheats/" in sl2 and fname.endswith(".cht") and "DuckStation (PS1) - PC" in self.get_profile_values():
                self.profile_var.set("DuckStation (PS1) - PC")
                _set_profile_id_from_filename("DuckStation (PS1) - PC", p.stem)

            # Xenia patches (.patch.toml)
            if "/patches/" in sl2 and fname.endswith(".patch.toml") and "Xenia (Xbox 360) - PC" in self.get_profile_values():
                self.profile_var.set("Xenia (Xbox 360) - PC")
                _set_profile_id_from_filename("Xenia (Xbox 360) - PC", p.name[:-len(".patch.toml")])

            # RPCS3 patch.yml
            if fname in ("patch.yml", "patch.yaml") and "RPCS3 (PS3) - PC" in self.get_profile_values():
                self.profile_var.set("RPCS3 (PS3) - PC")
        except Exception:
            pass

        # Refresh helper UI state based on current selected profile
        self.refresh_profile_info()

    def _on_drop_files(self, event):
        # event.data can contain one or more paths; take the first
        data = getattr(event, "data", "") or ""
        data = data.strip()
        if not data:
            return
        paths = []
        for braced, plain in re.findall(r"\{([^}]*)\}|([^\s]+)", data):
            candidate = (braced or plain).strip()
            if candidate:
                paths.append(candidate)
        filepath = paths[0] if paths else data
        self.load_file(filepath)

    def _split_bids(self, bids: str) -> List[str]:
        return split_bids(bids)

    def _validate_export_inputs(self, prof: str) -> Optional[str]:
        return validate_export_inputs(
            self.get_profile_info(prof),
            self.tid_var.get(),
            self.bid_var.get(),
            self.editor.get("1.0", "end"),
        )

    def build_export_plan(self, prof: str) -> dict:
        return build_export_plan_for_state(
            prof=prof,
            info=self.get_profile_info(prof),
            root=self._effective_export_root_for_profile(prof),
            tid=self.tid_var.get(),
            bid_text=self.bid_var.get(),
            core=self.core_var.get(),
            editor_text=self.editor.get("1.0", "end"),
        )

    def _schedule_export_preview_update(self, *_):
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

    def _on_editor_modified(self, *_):
        try:
            if self.editor.edit_modified():
                self.editor.edit_modified(False)
                self._schedule_export_preview_update()
        except Exception:
            pass

    def update_export_preview(self):
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

    def quick_export(self):
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

    def _save_retroarch_core(self):
        self.prefs["retroarch_core"] = self.core_var.get()
        save_prefs(self.prefs)
        try:
            self.refresh_profile_info()
        except Exception:
            pass

    def _audit_retroarch_cores(self) -> None:
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

    def _sync_core_dropdown(self):
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

    def manage_retroarch_cores(self):
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

    def open_help_links(self):
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

    def open_templates(self):
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

    def open_settings(self):
        win = tk.Toplevel(self.root); win.title("Settings"); win.geometry("980x640")
        win.transient(self.root); win.grab_set()
        sf = Scrollable(win); sf.pack(fill="both", expand=True); sf.set_canvas_bg(self.effective_colors()["bg"])
        nb = ttk.Notebook(sf.inner); nb.pack(fill="both", expand=True, padx=12, pady=12)


        # Profiles tab (custom profiles)
        tab_profiles = ttk.Frame(nb); nb.add(tab_profiles, text="Profiles")
        prof_sf = Scrollable(tab_profiles); prof_sf.pack(fill="both", expand=True, padx=6, pady=6); prof_sf.set_canvas_bg(self.effective_colors()["bg"])

        ttk.Label(prof_sf.inner, text="Profiles", font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=12, pady=(12, 6))
        ttk.Label(prof_sf.inner, text="Add custom emulators/consoles here. Custom profiles can include helper text shown in the Helper box.", wraplength=900).pack(anchor="w", padx=12, pady=(0, 10))

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

            ttk.Label(frm, text="Profile Name:").grid(row=0, column=0, sticky="w", pady=4)
            ttk.Entry(frm, textvariable=name_var).grid(row=0, column=1, sticky="ew", pady=4)

            ttk.Label(frm, text="Export Folder Structure:").grid(row=1, column=0, sticky="w", pady=4)
            ttk.Entry(frm, textvariable=subdir_var).grid(row=1, column=1, sticky="ew", pady=4)
            ttk.Label(
                frm,
                text="Where cheats will be exported inside Export Root. You can use placeholders like <Game>, <GameID>, <CRC>, <SERIAL>, <TitleID>, <Core Name> (if applicable).",
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

                exts = [e.strip() for e in exts_var.get().split(",") if e.strip()]
                exts = [e if e.startswith(".") else "." + e for e in exts] or [".txt"]

                helper_notes = notes.get("1.0", "end-1c").strip()
                if len(helper_notes) > helper_limit:
                    helper_notes = helper_notes[:helper_limit].rstrip()

                info = {
                    "subdir": subdir_var.get().strip(),
                    "filename_hint": fname_var.get().strip(),
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
    
    def _show_ctx_menu(self, event):
        try:
            self._ctx_widget = event.widget
            self._ctx_menu.tk_popup(event.x_root, event.y_root)
        finally:
            try: self._ctx_menu.grab_release()
            except Exception: pass
        return "break"

    def _ctx_action(self, action: str):
        w = getattr(self, "_ctx_widget", None)
        if w is None:
            return
        try:
            if action == "cut":
                w.event_generate("<<Cut>>")
            elif action == "copy":
                w.event_generate("<<Copy>>")
            elif action == "paste":
                w.event_generate("<<Paste>>")
            elif action == "delete":
                # delete selection if possible
                try:
                    if isinstance(w, tk.Text):
                        if w.tag_ranges("sel"):
                            w.delete("sel.first", "sel.last")
                        else:
                            w.delete("insert")
                    else:
                        sel = w.selection_present()
                        if sel:
                            w.delete("sel.first", "sel.last")
                        else:
                            idx = w.index("insert")
                            if idx is not None:
                                try: w.delete(idx)
                                except Exception: pass
                except Exception:
                    pass
            elif action == "select_all":
                try:
                    if isinstance(w, tk.Text):
                        w.tag_add("sel", "1.0", "end-1c")
                        w.mark_set("insert", "end-1c")
                        w.see("insert")
                    else:
                        w.selection_range(0, "end")
                        w.icursor("end")
                except Exception:
                    pass
        except Exception:
            pass
    def on_close(self):
            """Handle close: first-time prompt + optional remember geometry."""
            try:
                if not self.prefs.get("window_asked_once", False):
                    self.prefs["window_asked_once"] = True
                    ans = messagebox.askyesno(
                        "Remember window size?",
                        "Save this window size and position as your default for next time?\n\n"
                        "You can change this later in Settings → Advanced."
                    )
                    self.prefs["window_remember"] = bool(ans)

                if self.prefs.get("window_remember", True):
                    try:
                        self.prefs["window_geometry"] = self.root.geometry()
                    except Exception:
                        pass

                save_prefs(self.prefs)
            finally:
                try:
                    self.root.destroy()
                except Exception:
                    pass

    def save_current_window_size(self):
        self.prefs["window_remember"] = True
        try:
            self.prefs["window_geometry"] = self.root.geometry()
        except Exception:
            self.prefs["window_geometry"] = ""
        save_prefs(self.prefs)
        self.status.set("Window size saved as default.")

    def clear_saved_window_size(self):
        self.prefs["window_geometry"] = ""
        save_prefs(self.prefs)
        self.status.set("Saved window size cleared.")


    def run(self):
        self.root.mainloop()












