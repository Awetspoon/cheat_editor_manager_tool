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


from .bootstrap import configure_tcl_environment
from .profiles import (
    get_profile_info as get_profile_info_for_prefs,
    get_profile_values as get_profile_values_for_prefs,
    is_atmosphere_profile,
    primary_extension,
    profile_id_field_label,
    profile_id_hint,
    profile_template_path,
    uses_id_layout,
)
from .services import theme_service
from .services.export_service import (
    build_export_plan_from_app,
    convert_save as convert_save_from_app,
    effective_export_root_for_profile,
    get_all_known_extensions,
    on_editor_modified,
    pick_extension_for_save,
    quick_export as quick_export_from_app,
    schedule_export_preview_update,
    update_export_preview as update_export_preview_for_app,
    validate_export_inputs_for_profile,
)
from .services.file_load_service import load_file_into_app
from .state import AppState
from .ui.dialogs.help_links_dialog import open_help_links as open_help_links_dialog
from .ui.dialogs.retroarch_cores_dialog import (
    audit_retroarch_cores,
    manage_retroarch_cores as manage_retroarch_cores_dialog,
    save_retroarch_core,
    sync_core_dropdown,
)
from .ui.dialogs.settings_dialog import open_settings as open_settings_dialog
from .ui.dialogs.templates_dialog import open_templates as open_templates_dialog

class App:
    DEFAULT_WINDOW_WIDTH = 1200
    DEFAULT_WINDOW_HEIGHT = 820

    def __init__(self):
        configure_tcl_environment()
        ensure_demo_templates()
        self.prefs = load_prefs()
        self.state = AppState.from_prefs(self.prefs)
        self._audit_retroarch_cores()
        self.root = (TkinterDnD.Tk() if _HAS_DND else tk.Tk())
        self.root.title(f"{APP_NAME} — {APP_VERSION}")
        self._apply_startup_geometry()
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
        self.header_wordmark = tk.Label(self.header_titles, bg=self.header["bg"])
        self.header_wordmark.pack(anchor="w")
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

        self.status = tk.StringVar(value="[READY] Waiting for input")
        self.status_frame = tk.Frame(self.root, bd=1, relief="sunken")
        self.status_frame.pack(side="bottom", fill="x")
        self.status_label = tk.Label(self.status_frame, textvariable=self.status, anchor="w", padx=8, pady=2)
        self.status_label.pack(fill="x")

        self.apply_theme()
        self.refresh_profile_info()

    def _default_window_size(self) -> tuple[int, int]:
        return self.DEFAULT_WINDOW_WIDTH, self.DEFAULT_WINDOW_HEIGHT

    def _center_geometry(self, width: int, height: int) -> str:
        try:
            self.root.update_idletasks()
            screen_w = max(width, self.root.winfo_screenwidth())
            screen_h = max(height, self.root.winfo_screenheight())
        except Exception:
            return f"{width}x{height}"
        x = max(0, (screen_w - width) // 2)
        y = max(0, (screen_h - height) // 2 - 18)
        return f"{width}x{height}+{x}+{y}"

    @staticmethod
    def _parse_geometry_size(geometry: str) -> Optional[tuple[int, int]]:
        m = re.match(r"^\s*(\d+)x(\d+)", (geometry or "").strip())
        if not m:
            return None
        try:
            w = int(m.group(1))
            h = int(m.group(2))
        except Exception:
            return None
        if w < 640 or h < 480:
            return None
        return w, h

    def _apply_startup_geometry(self) -> None:
        default_w, default_h = self._default_window_size()
        self.root.geometry(self._center_geometry(default_w, default_h))

    def _load_brand_assets(self):
        assets = {
            "window_icon": asset_path("app-icon.ico"),
            "icon_photo": asset_path("icon-256.png"),
            "header_mark": asset_path("mark-48.png"),
            "header_wordmark": asset_path("wordmark-360.png"),
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

        header_wordmark = self._brand_images.get("header_wordmark")
        if header_wordmark is not None:
            self.header_wordmark.configure(image=header_wordmark, text="")
            if self.header_wordmark.winfo_manager() != "pack":
                self.header_wordmark.pack(anchor="w")
            if self.header_title.winfo_manager() == "pack":
                self.header_title.pack_forget()
            if self.header_subtitle.winfo_manager() == "pack":
                self.header_subtitle.pack_forget()
        else:
            self.header_wordmark.configure(image="", text="")
            if self.header_title.winfo_manager() != "pack":
                self.header_title.pack(anchor="w")
            if self.header_subtitle.winfo_manager() != "pack":
                self.header_subtitle.pack(anchor="w")

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

        try:
            tkfont.nametofont("TkDefaultFont").configure(family="Consolas", size=10)
            tkfont.nametofont("TkTextFont").configure(family="Consolas", size=10)
            tkfont.nametofont("TkFixedFont").configure(family="Consolas", size=10)
            tkfont.nametofont("TkMenuFont").configure(family="Consolas", size=10)
            tkfont.nametofont("TkHeadingFont").configure(family="Bahnschrift SemiBold", size=10, weight="bold")
        except Exception:
            pass

        style.configure("TButton", padding=(8, 5), borderwidth=2, relief="ridge")
        style.configure("Primary.TButton", padding=(8, 5), borderwidth=2, relief="ridge")
        style.configure("Danger.TButton", padding=(8, 5), borderwidth=2, relief="ridge")
        style.configure("TLabelframe", borderwidth=2, relief="groove")


    def get_profile_values(self):
        return get_profile_values_for_prefs(self.prefs)


    def get_profile_info(self, profile_name: str):
        return get_profile_info_for_prefs(self.prefs, profile_name)

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
        return theme_service.effective_colors(self.prefs)
    @staticmethod
    def _normalize_hex_color(value: str, fallback: str = "#000000") -> str:
        return theme_service.normalize_hex_color(value, fallback)
    @classmethod
    def _relative_luminance(cls, color: str) -> float:
        return theme_service.relative_luminance(color)
    @classmethod
    def _contrast_ratio(cls, fg: str, bg: str) -> float:
        return theme_service.contrast_ratio(fg, bg)
    @classmethod
    def _blend_colors(cls, start: str, end: str, amount: float) -> str:
        return theme_service.blend_colors(start, end, amount)
    @classmethod
    def _ensure_text_contrast(cls, bg: str, *, preferred: Optional[str] = None, light: str = "#fff8eb", dark: str = "#231b15", minimum: float = 4.5) -> str:
        return theme_service.ensure_text_contrast(bg, preferred=preferred, light=light, dark=dark, minimum=minimum)
    @classmethod
    def _selection_palette(cls, accent: str, preferred_text: str = "#ffffff") -> tuple[str, str]:
        return theme_service.selection_palette(accent, preferred_text)
    @classmethod
    def _button_palette(cls, bg: str, surface_bg: str, preferred_text: str, *, minimum: float = 4.5, disabled_minimum: float = 3.0) -> dict:
        return theme_service.button_palette(bg, surface_bg, preferred_text, minimum=minimum, disabled_minimum=disabled_minimum)
    @classmethod
    def _sanitize_theme_colors(cls, colors: dict, defaults: dict) -> dict:
        return theme_service.sanitize_theme_colors(colors, defaults)
    @staticmethod
    def _readable_text_color(bg: str) -> str:
        from .ui.widgets import _readable_text_color as readable_text_color
        return readable_text_color(bg)

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

        try:
            status_bg = c["panel2"]
            status_fg = self._ensure_text_contrast(status_bg, preferred=c["text"], minimum=4.5)
            self.status_frame.configure(bg=status_bg, highlightbackground=c["border"], highlightcolor=c["border"])
            self.status_label.configure(bg=status_bg, fg=status_fg, font=("Consolas", 9, "bold"))
        except Exception:
            pass

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
        self.header_wordmark.configure(bg=header_bg)
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
                relief="raised",
                bd=1,
                overrelief="sunken",
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
        return is_atmosphere_profile(self.prefs, prof, info)

    def _primary_extension(self, info: dict) -> str:
        return primary_extension(info)

    def _uses_id_layout(self, info: dict) -> bool:
        return uses_id_layout(info)

    def _profile_id_field_label(self, info: dict) -> str:
        return profile_id_field_label(info)

    def _profile_id_hint(self, info: dict) -> str:
        return profile_id_hint(info)

    def _profile_template_path(self, prof: str, info: dict) -> str:
        return profile_template_path(self.prefs, prof, info, self.core_var.get())

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
        return effective_export_root_for_profile(self, prof)

    def _get_all_known_extensions(self):
        return get_all_known_extensions(self)

    def _pick_extension_for_save(self, prof: str):
        return pick_extension_for_save(self, prof)

    def convert_save(self):
        return convert_save_from_app(self)



    def load_file(self, filepath: Optional[str] = None):
        return load_file_into_app(self, filepath)

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
        return validate_export_inputs_for_profile(self, prof)

    def build_export_plan(self, prof: str) -> dict:
        return build_export_plan_from_app(self, prof)

    def _schedule_export_preview_update(self, *_):
        return schedule_export_preview_update(self, *_)

    def _on_editor_modified(self, *_):
        return on_editor_modified(self, *_)

    def update_export_preview(self):
        return update_export_preview_for_app(self)

    def quick_export(self):
        return quick_export_from_app(self)

    def _save_retroarch_core(self):
        return save_retroarch_core(self)

    def _audit_retroarch_cores(self):
        return audit_retroarch_cores(self)

    def _sync_core_dropdown(self):
        return sync_core_dropdown(self)

    def manage_retroarch_cores(self):
        return manage_retroarch_cores_dialog(self)

    def open_help_links(self):
        return open_help_links_dialog(self)

    def open_templates(self):
        return open_templates_dialog(self)

    def open_settings(self):
        return open_settings_dialog(self)
    
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
            """Persist prefs and close the app."""
            try:
                save_prefs(self.prefs)
            finally:
                try:
                    self.root.destroy()
                except Exception:
                    pass

    def save_current_window_size(self):
        self.status.set("Startup is fixed to the default centered window size (1200x820).")

    def clear_saved_window_size(self):
        self.status.set("Startup already uses the default centered window size (1200x820).")


    def run(self):
        self.root.mainloop()



















