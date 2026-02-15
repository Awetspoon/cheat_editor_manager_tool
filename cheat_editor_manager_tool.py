# Cheat Editor Manager Tool
# Clean Rewrite (stable single-file)
from __future__ import annotations

import json
import os
import webbrowser
from pathlib import Path
from typing import Dict, List, Optional


import re as _re

def _clean_hex(s: str) -> str:
    """Return uppercase hex chars only."""
    return "".join(ch for ch in (s or "").strip() if ch.lower() in "0123456789abcdef").upper()

def _is_hex_len(s: str, n: int) -> bool:
    s = _clean_hex(s)
    return len(s) == n

import tkinter as tk
import tkinter.font as tkfont

# Optional drag-and-drop support (requires: pip install tkinterdnd2)
try:
    from tkinterdnd2 import TkinterDnD, DND_FILES  # type: ignore
    _HAS_DND = True
except Exception:
    TkinterDnD = None  # type: ignore
    DND_FILES = None  # type: ignore
    _HAS_DND = False
from tkinter import ttk, filedialog, messagebox, colorchooser
import re

class ToolTip:
    """Simple Tk tooltip (pure tkinter, no dependencies)."""

    def __init__(self, widget, text: str, delay_ms: int = 450):
        self.widget = widget
        self.text = text
        self.delay_ms = delay_ms
        self._after_id = None
        self._tip = None
        widget.bind("<Enter>", self._schedule, add="+")
        widget.bind("<Leave>", self._hide, add="+")
        widget.bind("<ButtonPress>", self._hide, add="+")

    def _schedule(self, *_):
        self._cancel()
        self._after_id = self.widget.after(self.delay_ms, self._show)

    def _cancel(self):
        if self._after_id is not None:
            try:
                self.widget.after_cancel(self._after_id)
            except Exception:
                pass
            self._after_id = None

    def _show(self):
        if self._tip or not self.text:
            return
        try:
            x = self.widget.winfo_rootx() + 12
            y = self.widget.winfo_rooty() + self.widget.winfo_height() + 8
        except Exception:
            return

        self._tip = tk.Toplevel(self.widget)
        self._tip.wm_overrideredirect(True)
        self._tip.wm_geometry(f"+{x}+{y}")

        frm = tk.Frame(self._tip, bd=1, relief="solid")
        frm.pack(fill="both", expand=True)

        lbl = tk.Label(frm, text=self.text, justify="left", padx=8, pady=6, wraplength=380)
        lbl.pack()

        # Try to inherit theme-ish colours (works fine in light/dark/custom)
        try:
            bg = self.widget.winfo_toplevel().cget("bg")
            fg = "#000000"
            lbl.configure(bg=bg, fg=fg)
            frm.configure(bg=bg)
        except Exception:
            pass

    def _hide(self, *_):
        self._cancel()
        if self._tip:
            try:
                self._tip.destroy()
            except Exception:
                pass
            self._tip = None


APP_NAME = "Cheat Editor Manager Tool"
APP_VERSION = "1.2.4 (Final Release)"

APP_DIR = Path.home() / "CheatCreator"
APP_DIR.mkdir(parents=True, exist_ok=True)

PREFS_FILE = APP_DIR / "prefs.json"
TEMPLATES_DIR = APP_DIR / "templates"
TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)

DEFAULT_HELP_LINKS = [
    {"name": "GameHacking.org (Cheat DB)", "url": "https://gamehacking.org"},
    {"name": "CodeTwink (Cheat Codes)", "url": "https://www.codetwink.com"},
    {"name": "CMGSCCC (PS2 Cheat Codes)", "url": "https://www.cmgsccc.com"},
    {"name": "WiiRD Code Database", "url": "https://geckocodes.org"},
    {"name": "CheatSlips (Switch Cheats)", "url": "https://cheatslips.com"},
    {"name": "GBAtemp — Cheats Forum", "url": "https://gbatemp.net/forums/nintendo-switch-cheats.289/"},
    {"name": "RetroArch Docs — Cheats", "url": "https://docs.libretro.com/guides/cheat-codes/"},
    {"name": "Dolphin Emulator — Guides", "url": "https://dolphin-emu.org/docs/guides/"},
    {"name": "PCSX2 Wiki — Cheats", "url": "https://wiki.pcsx2.net/Category:Cheats"},
    {"name": "PPSSPP — Cheats (Docs)", "url": "https://www.ppsspp.org/docs/reference/ini-file/#cheats"},
    {"name": "DuckStation — Cheat Codes", "url": "https://www.duckstation.org/codes.html"},
    {"name": "RPCS3 Wiki — Game Patches", "url": "https://wiki.rpcs3.net/index.php?title=Help:Game_Patches"},
    {"name": "Xenia — Patches (GitHub)", "url": "https://github.com/xenia-project/xenia/wiki/Options#patches"},
    {"name": "Cemu — Graphic Packs", "url": "https://cemu.info/#graphic-packs"},
]

DEFAULT_RETROARCH_CORES = [
    "Default (no subfolder)",
    "mGBA",
    "VBA-M",
    "Gambatte",
    "SameBoy",
    "DeSmuME",
    "Mesen",
    "Nestopia UE",
    "FCEUmm",
    "Snes9x",
    "Snes9x 2010",
    "Mupen64Plus-Next",
    "ParaLLEl N64",
    "Genesis Plus GX",
    "PicoDrive",
    "PCSX ReARMed",
    "Beetle PSX",
    "Beetle PSX HW",
    "FinalBurn Neo",
    "MAME 2003-Plus",
    "Flycast",
]

DEFAULT_PROFILES: Dict[str, dict] = {'Atmosphère (Switch) (CFW)': {'extensions': ['.txt'],
                               'subdir': 'atmosphere/contents/<TID>/cheats',
                               'filename_hint': '<BID>',
                               'notes': 'Atmosphère: SD:/atmosphere/contents/<TID>/cheats/<BID>.txt (BuildID changes '
                                        'with updates)',
                               'kind': 'switch'},
 'Yuzu (Switch) - PC': {'extensions': ['.txt'],
                        'subdir': 'yuzu/load/<TID>/<Cheat Name>/cheats',
                        'filename_hint': '<BID>',
                        'notes': 'Yuzu (PC): %APPDATA%/yuzu/load/<TID>/<Cheat Name>/cheats/<BID>.txt',
                        'kind': 'switch'},
 'Ryujinx (Switch) - PC': {'extensions': ['.txt'],
                           'subdir': 'Ryujinx/mods/contents/<TID>/<Cheat Name>/cheats',
                           'filename_hint': '<BID>',
                           'notes': 'Ryujinx (PC): %APPDATA%/Ryujinx/mods/contents/<TID>/<Cheat Name>/cheats/<BID>.txt',
                           'kind': 'switch'},
 'Sudachi (Switch) - PC': {'extensions': ['.txt'],
                           'subdir': 'Sudachi/load/<TID>/<Cheat Name>/cheats',
                           'filename_hint': '<BID>',
                           'notes': 'Sudachi (PC): Yuzu-style load/<TID>/<Cheat Name>/cheats/<BID>.txt',
                           'kind': 'switch'},
 'Suyu (Switch) - PC': {'extensions': ['.txt'],
                        'subdir': 'Suyu/load/<TID>/<Cheat Name>/cheats',
                        'filename_hint': '<BID>',
                        'notes': 'Suyu (PC): Yuzu-style load/<TID>/<Cheat Name>/cheats/<BID>.txt',
                        'kind': 'switch'},
 'Citra (3DS) - PC': {'extensions': ['.txt'],
                      'subdir': 'RetroArch/saves/Citra/cheats',
                      'filename_hint': '<GameID>',
                      'notes': 'Citra (Libretro core): RetroArch saves/Citra/cheats/<GameID>.txt (override if using '
                               'standalone Citra)',
                      'kind': 'generic'},
 'RetroArch (Multi-platform)': {'extensions': ['.cht'],
                                'subdir': 'RetroArch/cheats/<Core Name>',
                                'filename_hint': '<Game>',
                                'notes': 'RetroArch is multi-platform. Cheats: cheats/<Core Name>/<Game>.cht',
                                'kind': 'retroarch'},
 'Dolphin (GC/Wii) - PC': {'extensions': ['.ini'],
                           'subdir': 'Dolphin Emulator/GameSettings',
                           'filename_hint': '<GameID>',
                           'notes': 'Dolphin: Documents/Dolphin Emulator/GameSettings/<GameID>.ini (override if your '
                                    'Dolphin user folder differs)',
                           'kind': 'generic'},
 'PCSX2 (PS2) - PC': {'extensions': ['.pnach'],
                      'subdir': 'PCSX2/Cheats',
                      'filename_hint': '<CRC>',
                      'notes': 'PCSX2: Cheats/<CRC>.pnach (CRC must match game; override if your cheats folder '
                               'differs)',
                      'kind': 'generic'},
 'PPSSPP (PSP) - PC': {'extensions': ['.ini'],
                       'subdir': 'PPSSPP/memstick/PSP/Cheats',
                       'filename_hint': '<GameID>',
                       'notes': 'PPSSPP: memstick/PSP/Cheats/<GameID>.ini (enable cheats first; override if your '
                                'Memstick differs)',
                       'kind': 'generic'},
 'DuckStation (PS1) - PC': {'extensions': ['.cht'],
                            'subdir': 'DuckStation/cheats',
                            'filename_hint': '<SERIAL>',
                            'notes': 'DuckStation: cheats/<SERIAL>.cht (location varies by install—use Emulator Paths '
                                     'override if needed)',
                            'kind': 'generic'},
 'Cemu (Wii U) - PC': {'extensions': ['.txt'],
                       'subdir': 'Cemu/graphicPacks/<Pack Name>',
                       'filename_hint': 'patches',
                       'notes': 'Cemu: graphicPacks/<Pack Name>/patches.txt (pack name derived from first Heading; '
                                'override if needed)',
                       'kind': 'generic'},
 'Xenia (Xbox 360) - PC': {'extensions': ['.patch.toml'],
                           'subdir': 'Xenia/patches',
                           'filename_hint': '<TitleID>',
                           'notes': 'Xenia: patches/<TitleID>.patch.toml',
                           'kind': 'generic'},
 'RPCS3 (PS3) - PC': {'extensions': ['.yml'],
                      'subdir': 'RPCS3',
                      'filename_hint': 'patch',
                      'notes': 'RPCS3: patch.yml (legacy-compatible). You can also use Patch Manager; override if '
                               'needed.',
                      'kind': 'singlefile',
                      'fixed_filename': 'patch.yml'},
 'Nintendo 3DS (CFW) (Luma)': {'extensions': ['.txt'],
                               'subdir': 'MODDED/3DS/cheats',
                               'filename_hint': '<Game>',
                               'notes': 'Modded console export (paths vary). Use Emulator Paths override to point to '
                                        'your SD card/homebrew folder.',
                               'kind': 'modded'},
 'PS Vita (CFW) (taiHEN)': {'extensions': ['.txt'],
                            'subdir': 'MODDED/PSVITA/cheats',
                            'filename_hint': '<Game>',
                            'notes': 'Modded console export (paths vary). Use Emulator Paths override to point to your '
                                     'SD card/homebrew folder.',
                            'kind': 'modded'},
 'PSP (CFW)': {'extensions': ['.txt'],
               'subdir': 'MODDED/PSP/cheats',
               'filename_hint': '<Game>',
               'notes': 'Modded console export (paths vary). Use Emulator Paths override to point to your SD '
                        'card/homebrew folder.',
               'kind': 'modded'},
 'Wii (Homebrew)': {'extensions': ['.txt'],
                    'subdir': 'MODDED/WII/cheats',
                    'filename_hint': '<Game>',
                    'notes': 'Modded console export (paths vary). Use Emulator Paths override to point to your SD '
                             'card/homebrew folder.',
                    'kind': 'modded'},
 'Wii U (CFW)': {'extensions': ['.txt'],
                 'subdir': 'MODDED/WIIU/cheats',
                 'filename_hint': '<Game>',
                 'notes': 'Modded console export (paths vary). Use Emulator Paths override to point to your SD '
                          'card/homebrew folder.',
                 'kind': 'modded'}}

DEFAULT_BUTTON_COLORS = {
    "header": "#c62828",
    "primary": "#c62828",
    "secondary": "#ffffff",
    "toolbar": "#ffffff",
    "danger": "#c62828",
    "neutral": "#3a3a3a",
}

DEFAULT_THEME_DARK = {
    "bg": "#0e1624",
    "panel": "#111c2e",
    "panel2": "#0b1220",
    "text": "#e6eefc",
    "muted": "#b7c2d6",
    "entry": "#0b1220",
    "border": "#24324a",
    "editor_bg": "#0b1220",
    "editor_fg": "#e6eefc",
}

DEFAULT_THEME_LIGHT = {
    "bg": "#f5f7fb",
    "panel": "#ffffff",
    "panel2": "#f0f2f7",
    "text": "#1a1a1a",
    "muted": "#4a5568",
    "entry": "#ffffff",
    "border": "#c8d2e1",
    "editor_bg": "#ffffff",
    "editor_fg": "#1a1a1a",
}

DEFAULT_PREFS: dict = {
    "mode": "light",
    "wrap": True,
    "editor_font_size": 11,
    "help_links": list(DEFAULT_HELP_LINKS),
    "custom_theme_enabled": False,
    "custom_theme": dict(DEFAULT_THEME_DARK),
    "button_colors": dict(DEFAULT_BUTTON_COLORS),
    "templates_default": {},
    "retroarch_cores": list(DEFAULT_RETROARCH_CORES),
    "retroarch_core": DEFAULT_RETROARCH_CORES[0],
    "emulator_paths": {},
    "custom_profiles": {},
    "profile_sort": "default",
    "window_remember": True,
    "window_geometry": "",
    "window_asked_once": False,
}

def load_prefs() -> dict:
    data = {}
    if PREFS_FILE.exists():
        try:
            data = json.loads(PREFS_FILE.read_text(encoding="utf-8"))
        except Exception:
            data = {}
    prefs = dict(DEFAULT_PREFS)
    prefs.update(data)
    prefs.setdefault("help_links", list(DEFAULT_HELP_LINKS))
    # Ensure button colour keys include new defaults (merge, do not wipe user values)
    _bc = dict(DEFAULT_BUTTON_COLORS)
    _bc.update(prefs.get("button_colors", {}) or {})
    prefs["button_colors"] = _bc
    prefs.setdefault("custom_theme", dict(DEFAULT_THEME_DARK))
    prefs.setdefault("retroarch_cores", list(DEFAULT_RETROARCH_CORES))
    if not prefs.get("retroarch_cores"):
        prefs["retroarch_cores"] = list(DEFAULT_RETROARCH_CORES)

    # Merge newly-added default cores into the saved list (keeps user order; no duplicates).
    try:
        default_label = "Default (no subfolder)"

        def _norm(x: str) -> str:
            return (x or "").strip()

        def _uniq_preserve(seq):
            out = []
            seen = set()
            for s in seq:
                s = _norm(s)
                if not s:
                    continue
                k = s.casefold()
                if k in seen:
                    continue
                seen.add(k)
                out.append(s)
            return out

        existing = _uniq_preserve(prefs.get("retroarch_cores") or [])
        defaults = _uniq_preserve(list(DEFAULT_RETROARCH_CORES))

        merged = []
        seen = set()

        # Keep the Default option first if it exists anywhere.
        if any(x.casefold() == default_label.casefold() for x in (existing + defaults)):
            merged.append(default_label)
            seen.add(default_label.casefold())

        # Keep user-defined order next.
        for s in existing:
            k = s.casefold()
            if k in seen:
                continue
            merged.append(s)
            seen.add(k)

        # Append any new defaults at the end.
        for s in defaults:
            k = s.casefold()
            if k in seen:
                continue
            merged.append(s)
            seen.add(k)

        prefs["retroarch_cores"] = merged
    except Exception:
        pass

    prefs.setdefault("retroarch_core", prefs["retroarch_cores"][0])
    prefs.setdefault("templates_default", {})
    prefs.setdefault("emulator_paths", {})
    prefs.setdefault("custom_profiles", {})
    prefs.setdefault("profile_sort", "default")
    # Migration: profile-level export_root removed (Advanced overrides only)
    try:
        cps = prefs.get("custom_profiles") or {}
        changed = False
        for k, v in list(cps.items()):
            if isinstance(v, dict) and "export_root" in v:
                vv = dict(v)
                vv.pop("export_root", None)
                cps[k] = vv
                changed = True
        if changed:
            prefs["custom_profiles"] = cps
    except Exception:
        pass
    return prefs

def save_prefs(prefs: dict) -> None:
    PREFS_FILE.write_text(json.dumps(prefs, indent=2, ensure_ascii=False), encoding="utf-8")

class Scrollable(ttk.Frame):
    """A scrollable container that auto-hides scrollbars when not needed."""

    def __init__(self, parent):
        super().__init__(parent)

        # Use a tk.Canvas so we can scroll any Tk/ttk widgets placed inside.
        self.canvas = tk.Canvas(self, highlightthickness=0)
        self.v = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.h = ttk.Scrollbar(self, orient="horizontal", command=self.canvas.xview)

        self.inner = ttk.Frame(self.canvas)
        self.inner_id = self.canvas.create_window((0, 0), window=self.inner, anchor="nw")

        self.canvas.configure(yscrollcommand=self.v.set, xscrollcommand=self.h.set)

        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.v.grid(row=0, column=1, sticky="ns")
        self.h.grid(row=1, column=0, sticky="ew")

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        self.inner.bind("<Configure>", self._on_inner_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)

        # initial hide until we know content size
        self.v.grid_remove()
        self.h.grid_remove()

    def set_canvas_bg(self, bg: str):
        """Set canvas background (used by theming)."""
        try:
            self.canvas.configure(bg=bg)
        except Exception:
            pass

    def _update_scrollbars(self):
        bbox = self.canvas.bbox("all")
        if not bbox:
            return
        x0, y0, x1, y1 = bbox
        cw = max(1, self.canvas.winfo_width())
        ch = max(1, self.canvas.winfo_height())
        need_h = (x1 - x0) > (cw + 2)
        need_v = (y1 - y0) > (ch + 2)

        if need_v:
            self.v.grid()
        else:
            self.v.grid_remove()

        if need_h:
            self.h.grid()
        else:
            self.h.grid_remove()

    def _on_inner_configure(self, _e=None):
        try:
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        except Exception:
            pass
        self._update_scrollbars()

    def _on_canvas_configure(self, e=None):
        # Match inner width to canvas width so content reflows
        try:
            w = max(1, self.canvas.winfo_width() if e is None else e.width)
            self.canvas.itemconfigure(self.inner_id, width=w)
        except Exception:
            pass
        self._update_scrollbars()

def _safe_name(name: str) -> str:
    return "".join(ch for ch in name if ch not in r'\/:*?"<>|').strip()

def profile_templates_dir(profile: str) -> Path:
    d = TEMPLATES_DIR / _safe_name(profile)
    d.mkdir(parents=True, exist_ok=True)
    return d

def list_templates(profile: str) -> List[str]:
    d = profile_templates_dir(profile)
    names = [p.stem for p in sorted(d.glob("*.txt"))]
    if "Blank" not in names:
        names.insert(0, "Blank")
    return names

def read_template(profile: str, name: str) -> str:
    if name == "Blank":
        return ""
    p = profile_templates_dir(profile) / f"{_safe_name(name)}.txt"
    if p.exists():
        return p.read_text(encoding="utf-8", errors="replace")
    return ""

def write_template(profile: str, name: str, content: str) -> None:
    if name == "Blank":
        return
    p = profile_templates_dir(profile) / f"{_safe_name(name)}.txt"
    p.write_text(content, encoding="utf-8")

def ensure_demo_templates():
    demo = (
        "# Cheat template (example)\n"
        "# Add your cheat name in brackets, then codes below.\n\n"
        "[Example Cheat]\n"
        "00000000 00000000\n\n"
        "# Notes:\n"
        "# - Keep this file plain text.\n"
        "# - Use Templates to reuse snippets.\n"
    )
    for prof in DEFAULT_PROFILES.keys():
        folder = profile_templates_dir(prof)
        if not any(folder.glob("*.txt")):
            write_template(prof, "Simple (Code + Notes)", demo)

def ask_text(parent, title: str, label: str) -> Optional[str]:
    win = tk.Toplevel(parent)
    win.title(title)
    win.transient(parent)
    win.grab_set()
    win.resizable(False, False)
    ttk.Label(win, text=label).pack(anchor="w", padx=12, pady=(12, 6))
    var = tk.StringVar()
    ent = ttk.Entry(win, textvariable=var, width=48)
    ent.pack(fill="x", padx=12, pady=(0, 10))
    ent.focus_set()
    out = {"v": None}
    def ok():
        out["v"] = var.get().strip()
        win.destroy()
    row = ttk.Frame(win)
    row.pack(fill="x", padx=12, pady=(0, 12))
    ttk.Button(row, text="OK", command=ok).pack(side="left")
    ttk.Button(row, text="Cancel", command=win.destroy).pack(side="left", padx=(8, 0))
    win.wait_window()
    return out["v"]

class App:
    def __init__(self):
        ensure_demo_templates()
        self.prefs = load_prefs()
        self._audit_retroarch_cores()
        self.root = (TkinterDnD.Tk() if _HAS_DND else tk.Tk())
        self.root.title(f"{APP_NAME} — {APP_VERSION}")
        self.root.geometry("1200x820")

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

        self.header = tk.Frame(self.root, bg=self.prefs.get("button_colors", DEFAULT_BUTTON_COLORS).get("header", DEFAULT_BUTTON_COLORS["header"]))
        self.header.pack(fill="x")
        tk.Label(self.header, text=APP_NAME, bg=self.header["bg"], fg="#ffffff", font=("Segoe UI", 14, "bold")).pack(side="left", padx=12, pady=10)

        self.btn_dark = tk.Button(self.header, text="Dark Mode", command=self.toggle_mode, bg=self.header["bg"], fg="#ffffff", relief="flat", activebackground=self.header["bg"], activeforeground="#ffffff")
        self.btn_templates = tk.Button(self.header, text="Templates…", command=self.open_templates, bg=self.header["bg"], fg="#ffffff", relief="flat", activebackground=self.header["bg"], activeforeground="#ffffff")
        self.btn_links = tk.Button(self.header, text="Help Links", command=self.open_help_links, bg=self.header["bg"], fg="#ffffff", relief="flat", activebackground=self.header["bg"], activeforeground="#ffffff")
        self.btn_settings = tk.Button(self.header, text="Settings", command=self.open_settings, bg=self.header["bg"], fg="#ffffff", relief="flat", activebackground=self.header["bg"], activeforeground="#ffffff")
        for b in (self.btn_settings, self.btn_links, self.btn_templates, self.btn_dark):
            b.pack(side="right", padx=8, pady=6)

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
        self.info_var = tk.StringVar(value="Quick Export builds the correct folder structure automatically. Convert & Save lets you choose any location or extension.")
        ttk.Label(self.body.inner, textvariable=self.info_var).pack(anchor="w", padx=10, pady=(0, 10))

        self.helper = ttk.LabelFrame(self.body.inner, text="Helper")
        self.helper.pack(fill="x", padx=10, pady=(0, 10))

        self.helper_text = tk.StringVar(value="Select an emulator to see helper info.")

        # Helper display: constrained-height, read-only text area so long notes don't bloat the UI.
        # (Keeps the Helper section neat when the window is maximized.)
        self._helper_display = tk.Text(self.helper, height=4, wrap="word", relief="flat", borderwidth=0, highlightthickness=0)
        self._helper_display.configure(state="disabled")
        self._helper_display_v = ttk.Scrollbar(self.helper, orient="vertical", command=self._helper_display.yview)
        self._helper_display.configure(yscrollcommand=self._helper_display_v.set)

        # Grid: text takes the row; scrollbar sits to the right.
        self._helper_display.grid(row=0, column=0, columnspan=9, sticky="nsew", padx=10, pady=(8, 6))
        self._helper_display_v.grid(row=0, column=9, sticky="ns", padx=(0, 10), pady=(8, 6))

        # Allow the helper text to expand horizontally, but keep its height controlled by "height".
        try:
            self.helper.columnconfigure(0, weight=1)
        except Exception:
            pass

        self._set_helper_display(self.helper_text.get())

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

        self._tid_label = ttk.Label(self.helper, text="TitleID (TID):")
        # Keep helper inputs a sensible width so they don't look stretched into the right side.
        self._tid_entry = ttk.Entry(self.helper, textvariable=self.tid_var, width=18)
        self._bid_label = ttk.Label(self.helper, text="BuildID(s) (BID):")
        self._bid_entry = ttk.Entry(self.helper, textvariable=self.bid_var, width=28)
        self._tid_label.grid(row=1, column=0, sticky="w", padx=10, pady=4)
        self._tid_entry.grid(row=1, column=1, sticky="w", padx=(0, 10), pady=4)
        self._bid_label.grid(row=1, column=2, sticky="w", padx=(14, 0), pady=4)
        self._bid_entry.grid(row=1, column=3, sticky="w", padx=(0, 10), pady=4)

        self._core_label = ttk.Label(self.helper, text="RetroArch Core:")
        self._core_cb = ttk.Combobox(self.helper, textvariable=self.core_var, values=self.prefs.get("retroarch_cores", DEFAULT_RETROARCH_CORES), state="readonly", width=18)
        self._core_manage = ttk.Button(self.helper, text="Manage Cores…", command=self.manage_retroarch_cores)
        self._core_label.grid(row=1, column=4, sticky="w", padx=(14, 0), pady=4)
        self._core_cb.grid(row=1, column=5, sticky="w", padx=(0, 10), pady=4)
        self._core_cb.bind("<<ComboboxSelected>>", lambda _e: self._save_retroarch_core())
        self._core_manage.grid(row=1, column=6, sticky="w", padx=(10, 0), pady=4)

        self.path_preview = tk.StringVar(value="")
        ttk.Label(self.helper, textvariable=self.path_preview).grid(row=2, column=0, columnspan=10, sticky="w", padx=10, pady=(0, 8))

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

    def _tt(self, widget, text: str):
        # Keep a reference so tooltips are not garbage-collected.
        if not hasattr(self, "_tooltips"):
            self._tooltips = []
        self._tooltips.append(ToolTip(widget, text))

    def _set_helper_display(self, txt: str) -> None:
        """Update the Helper display (read-only) without letting it resize the whole UI."""
        self.helper_text.set(txt or "")
        try:
            self._helper_display.configure(state="normal")
            self._helper_display.delete("1.0", tk.END)
            self._helper_display.insert("1.0", (txt or "").strip())
            self._helper_display.configure(state="disabled")
            self._helper_display.yview_moveto(0)
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
            m.configure(
                bg=c["panel"],
                fg=c["text"],
                activebackground=c["panel2"],
                activeforeground=c["text"],
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
        base = dict(DEFAULT_THEME_DARK if self.prefs.get("mode") == "dark" else DEFAULT_THEME_LIGHT)
        if self.prefs.get("custom_theme_enabled"):
            base.update(self.prefs.get("custom_theme", {}))
        return base

    def toggle_mode(self):
        # Block quick toggle while in Custom mode
        if self.prefs.get("custom_theme_enabled"):
            self.status.set(
                "Quick theme toggle disabled while Custom mode is active. "
                "Go to Settings → Appearance to switch to Dark or Light."
            )
            return

        # Normal Dark / Light toggle
        self.prefs["mode"] = "dark" if self.prefs.get("mode") == "light" else "light"
        save_prefs(self.prefs)
        self.apply_theme()
        self.status.set(f"Theme set to: {self.prefs['mode'].title()}")

    def apply_theme(self):
        c = self.effective_colors()
        btn = dict(DEFAULT_BUTTON_COLORS)
        btn.update(self.prefs.get("button_colors", {}))
        style = ttk.Style(self.root)
        style.configure(".", background=c["bg"], foreground=c["text"])
        style.configure("TFrame", background=c["bg"])
        style.configure("TLabel", background=c["bg"], foreground=c["text"])
        style.configure("TLabelframe", background=c["bg"], foreground=c["text"])
        style.configure("TLabelframe.Label", background=c["bg"], foreground=c["text"])
        style.configure("TEntry", fieldbackground=c["entry"], foreground=c["text"])

        # Comboboxes (keep the drop-arrow visible in both script and packaged builds)
        style.configure(
            "TCombobox",
            fieldbackground=c["entry"],
            background=c["entry"],
            foreground=c["text"],
        )
        style.map(
            "TCombobox",
            fieldbackground=[("readonly", c["entry"])],
            foreground=[("readonly", c["text"])],
        )
        # Some themes support 'arrowcolor' (Tk 8.6+). If available, force it to match text.
        try:
            style.configure("TCombobox", arrowcolor=c["text"], arrowsize=12)
            style.configure("Profile.TCombobox", arrowcolor=c["text"], arrowsize=12)
            style.map("TCombobox", arrowcolor=[("readonly", c["text"])])
        except Exception:
            pass

        style.configure("TSpinbox", fieldbackground=c["entry"], foreground=c["text"])

        # Combobox dropdown list + Treeview styling (dark mode readability)
        try:
            self.root.option_add("*TCombobox*Listbox.background", c["entry"])
            self.root.option_add("*TCombobox*Listbox.foreground", c["text"])
            self.root.option_add("*TCombobox*Listbox.selectBackground", c.get("accent", "#c62828"))
            self.root.option_add("*TCombobox*Listbox.selectForeground", "#ffffff")
        except Exception:
            pass

        style.configure("Treeview",
                        background=c["entry"],
                        fieldbackground=c["entry"],
                        foreground=c["text"],
                        bordercolor=c.get("border", c["panel2"]))
        style.configure("Treeview.Heading", background=c["panel2"], foreground=c["text"])
        style.map("Treeview", background=[("selected", c.get("accent", "#c62828"))],
                  foreground=[("selected", "#ffffff")])
        sec_bg = btn.get("secondary", c["panel"])
        if self.prefs.get("mode") == "dark" and (sec_bg or "").lower() in ("#ffffff", "white"):
            sec_bg = c["panel"]
        style.configure("TButton", background=sec_bg, foreground=c["text"])
        style.map("TButton", background=[("active", c["panel2"])])
        # Toolbar buttons (Heading / Bold / Undo / Redo) can have their own colour.
        toolbar_bg = btn.get("toolbar", sec_bg)
        if self.prefs.get("mode") == "dark" and (toolbar_bg or "").lower() in ("#ffffff", "white"):
            toolbar_bg = c["panel"]
        style.configure("Toolbar.TButton", background=toolbar_bg, foreground=c["text"])
        style.map("Toolbar.TButton", background=[("active", c["panel2"])])
        style.configure("Primary.TButton", background=btn.get("primary", DEFAULT_BUTTON_COLORS["primary"]), foreground="#ffffff")
        style.map("Primary.TButton", background=[("active", btn.get("primary", DEFAULT_BUTTON_COLORS["primary"]))])
        style.configure("Danger.TButton", background=btn.get("danger", DEFAULT_BUTTON_COLORS["danger"]), foreground="#ffffff")
        style.map("Danger.TButton", background=[("active", btn.get("danger", DEFAULT_BUTTON_COLORS["danger"]))])
        style.configure("TNotebook", background=c["bg"])
        # Notebook tabs (Settings tabs etc.) need explicit state maps for dark mode readability.
        tab_fg = c["text"]
        if self.prefs.get("mode") == "dark":
            tab_fg = "#ffffff"
        style.configure("TNotebook.Tab", background=c["panel"], foreground=tab_fg)
        style.map(
            "TNotebook.Tab",
            foreground=[("selected", tab_fg), ("active", tab_fg)],
            background=[("selected", c["panel2"]), ("active", c["panel2"])],
        )
        self.root.configure(bg=c["bg"])
        self.body.set_canvas_bg(c["bg"])
        header_bg = btn.get("header", btn.get("primary", DEFAULT_BUTTON_COLORS["header"]))
        self.header.configure(bg=header_bg)
        for w in (self.btn_dark, self.btn_templates, self.btn_links, self.btn_settings):
            w.configure(bg=header_bg, activebackground=header_bg)
        self.btn_dark.configure(text=("Light Mode" if self.prefs.get("mode") == "dark" else "Dark Mode"))
        self.editor.configure(
            bg=c["editor_bg"],
            fg=c["editor_fg"],
            insertbackground=c["editor_fg"],
            selectbackground=btn.get("primary", DEFAULT_BUTTON_COLORS["primary"]),
            selectforeground="#ffffff",
            font=("Consolas", int(self.prefs.get("editor_font_size", 11) or 11)),
        )

        # Helper display (read-only Text) should match the editor palette for readability.
        try:
            self._helper_display.configure(
                bg=c["editor_bg"],
                fg=c["editor_fg"],
                insertbackground=c["editor_fg"],
                selectbackground=btn.get("primary", DEFAULT_BUTTON_COLORS["primary"]),
                selectforeground="#ffffff",
            )
        except Exception:
            pass


    def _show_tid_bid(self, show: bool):
        for w in (self._tid_label, self._tid_entry, self._bid_label, self._bid_entry):
            (w.grid if show else w.grid_remove)()

    def _show_core(self, show: bool):
        for w in (self._core_label, self._core_cb, self._core_manage):
            (w.grid if show else w.grid_remove)()

    def refresh_profile_info(self):
        prof = self.profile_var.get()
        info = self.get_profile_info(prof)
        kind = info.get("kind", "generic")
        if kind == "switch":
            self._show_tid_bid(True); self._show_core(False)
        elif kind == "retroarch":
            self._show_tid_bid(False); self._show_core(True)
        else:
            self._show_tid_bid(False); self._show_core(False)

        notes = (info.get("notes") or "").strip()
        if notes:
            base = notes
        else:
            if prof.startswith("Atmosphère (Switch)"):
                base = "Switch cheats: enter TitleID + BuildID(s). BuildID changes when the game updates."
            elif kind == "switch":
                base = "Switch cheats: enter TitleID + (optional) BuildID(s) if needed."
            elif kind == "retroarch":
                base = "RetroArch: choose a Core, then export to cheats/<Core Name>/<Game>.cht"
            else:
                base = "Ready."

        exts = info.get("extensions", [".txt"]) or [".txt"]
        ext_line = "Expected file types: " + " ".join(exts)
        tip_line = "Tip: Convert & Save lets you pick the extension first."

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


        # RetroArch: .../cheats/<core>/<game>.cht  (core folder matters for auto-load)
        if "/cheats/" in sl:
            try:
                # Smarter detection:
                # - Works for different RetroArch install roots (Android/PC) as long as it contains /cheats/<core>/
                # - Keeps user's core list unchanged (no auto-adding unknown cores)
                parts_orig = s.replace("\\", "/").split("/")
                parts_low = [p.lower() for p in parts_orig]

                core_folder = ""
                if "cheats" in parts_low:
                    i = len(parts_low) - 1 - parts_low[::-1].index("cheats")  # last occurrence
                    if i + 1 < len(parts_orig):
                        core_folder = (parts_orig[i + 1] or "").strip()

                def _norm_core(x: str) -> str:
                    x = (x or "").strip().casefold()
                    # treat hyphen/underscore/multiple spaces as equivalent
                    x = re.sub(r"[-_]+", " ", x)
                    x = re.sub(r"\s+", " ", x).strip()
                    return x

                if core_folder:
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
                    else:
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
            tid_now = _clean_hex(self.tid_var.get())
            bid_now = _clean_hex(self.bid_var.get())
            if len(tid_now) != 16 or (len(bid_now) not in (16, 32)):
                head = "\n".join(text.splitlines()[:50])
                # Accept forms like: TID=..., TitleID=..., BID=..., BuildID=...
                m_tid = _re.search(r"(?:\bTID\b|\bTITLEID\b)\s*[:=]\s*([0-9A-Fa-f]{16})", head)
                m_bid = _re.search(r"(?:\bBID\b|\bBUILDID\b)\s*[:=]\s*([0-9A-Fa-f]{16}|[0-9A-Fa-f]{32})", head)
                if m_tid and len(_clean_hex(m_tid.group(1))) == 16:
                    self.tid_var.set(_clean_hex(m_tid.group(1)))
                if m_bid:
                    b = _clean_hex(m_bid.group(1))
                    if len(b) in (16, 32):
                        self.bid_var.set(b)

                # If we now have a Switch TID, prefer Atmosphère profile as a safe default.
                if len(_clean_hex(self.tid_var.get())) == 16:
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
            fname = p.name.lower()

            # PCSX2 (.pnach)
            if fname.endswith(".pnach") and "PCSX2 (PS2) - PC" in self.get_profile_values():
                self.profile_var.set("PCSX2 (PS2) - PC")

            # Dolphin GameSettings (.ini)
            if "/gamesettings/" in sl2 and fname.endswith(".ini") and "Dolphin (GC/Wii) - PC" in self.get_profile_values():
                self.profile_var.set("Dolphin (GC/Wii) - PC")

            # PPSSPP cheats (.ini) commonly in memstick/PSP/Cheats
            if ("/psp/cheats/" in sl2 or "/memstick/psp/cheats/" in sl2) and fname.endswith(".ini") and "PPSSPP (PSP) - PC" in self.get_profile_values():
                self.profile_var.set("PPSSPP (PSP) - PC")

            # DuckStation (.cht)
            if "/duckstation/" in sl2 and "/cheats/" in sl2 and fname.endswith(".cht") and "DuckStation (PS1) - PC" in self.get_profile_values():
                self.profile_var.set("DuckStation (PS1) - PC")

            # Xenia patches (.patch.toml)
            if "/patches/" in sl2 and fname.endswith(".patch.toml") and "Xenia (Xbox 360) - PC" in self.get_profile_values():
                self.profile_var.set("Xenia (Xbox 360) - PC")

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
        # TkDND formats: '{path with spaces}' or 'path'
        data = data.strip()
        if not data:
            return
        if data.startswith("{") and data.endswith("}"):
            data = data[1:-1]
        first = data.split()  # if multiple, first token
        filepath = first[0] if first else data
        self.load_file(filepath)

    def _split_bids(self, bids: str) -> List[str]:
        parts: List[str] = []
        for raw in bids.replace("\n", ",").replace(" ", ",").split(","):
            x = raw.strip()
            if x: parts.append(x)
        return parts

    def _derive_cheat_name(self) -> str:
        """Derive a safe label from the editor content for folders/filenames.

        Preference order:
          1) First '# ' heading line (without the '#')
          2) First non-empty line
          3) Fallback: 'Cheats'
        """
        text = self.editor.get("1.0", "end").splitlines()
        label = ""
        for ln in text:
            s = (ln or "").strip()
            if not s:
                continue
            if s.startswith("#"):
                label = s.lstrip("#").strip()
                if label:
                    break
            label = s
            break
        if not label:
            label = "Cheats"
        # filesystem-safe
        label = re.sub(r'[\\/:*?\\"<>|]+', "_", label)
        label = re.sub(r"\s+", " ", label).strip()
        return label[:64] if len(label) > 64 else label

    def _normalize_ext(self, ext: str) -> str:
        ext = (ext or "").strip()
        if not ext:
            return ".txt"
        if not ext.startswith("."):
            ext = "." + ext
        return ext

    def _sanitize_path_fragment(self, s: str) -> str:
        # Keep folder/file fragments safe across Windows/macOS/Linux
        s = (s or "").strip()
        if not s:
            return ""
        s = re.sub(r'[\/:*?\"<>|]+', "_", s)
        s = re.sub(r"\s+", " ", s).strip()
        return s

    def build_export_plan(self, prof: str) -> dict:
        """Single source of truth for Quick Export path + filenames (ALL profiles).

        Returns:
            {
              "profile": str,
              "kind": str,
              "root": Path,
              "out_dir": Path,
              "files": [Path, ...],
              "ext": ".txt",
            }
        """
        info = self.get_profile_info(prof)
        kind = info.get("kind", "generic")

        root = self._effective_export_root_for_profile(prof)
        subdir = (info.get("subdir", "") or "").strip()
        filename_hint = (info.get("filename_hint", "cheats") or "cheats").strip()

        exts = info.get("extensions", [".txt"]) or [".txt"]
        ext = self._normalize_ext(exts[0] if exts else ".txt")

        tid = (self.tid_var.get().strip() or "<TID>")
        bids = self._split_bids(self.bid_var.get()) or ["<BID>"]
        core = (self.core_var.get().strip() or "<Core Name>")
        cheat_name = self._derive_cheat_name()

        # Apply placeholders consistently
        def apply_placeholders(s: str, bid_val: str | None = None) -> str:
            out = (s or "")
            out = out.replace("<TID>", tid).replace("<TitleID>", tid)
            out = out.replace("<Core Name>", core)
            out = out.replace("<Cheat Name>", cheat_name)
            out = out.replace("<Pack Name>", cheat_name)
            out = out.replace("<Game>", cheat_name).replace("<GameID>", cheat_name)
            out = out.replace("<CRC>", cheat_name).replace("<SERIAL>", cheat_name)
            out = out.replace("<TitleID>", tid)
            if bid_val is not None:
                out = out.replace("<BID>", bid_val)
            return out

        export_sub = apply_placeholders(subdir)
        # keep angle brackets from leaking into filesystem
        export_sub = export_sub.replace("<", "_").replace(">", "_")
        out_dir = root / export_sub

        fixed_filename = info.get("fixed_filename")
        files = []

        if kind == "switch":
            for bid in bids:
                bid_clean = bid.strip() or "<BID>"
                name = apply_placeholders(filename_hint, bid_clean)
                name = name.replace("<", "_").replace(">", "_")
                files.append(out_dir / f"{name}{ext}")
        elif kind == "singlefile" and fixed_filename:
            files.append(out_dir / fixed_filename)
        else:
            name = apply_placeholders(filename_hint)
            name = name.replace("<", "_").replace(">", "_")
            files.append(out_dir / f"{name}{ext}")

        return {
            "profile": prof,
            "kind": kind,
            "root": root,
            "out_dir": out_dir,
            "files": files,
            "ext": ext,
        }

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
                # BID can be multiple; allow empty but warn
                if not bid_raw:
                    missing_bits.append("BID")

            if missing_bits:
                self.path_preview.set("Export preview: enter " + " + ".join(missing_bits) + " to see final output path.")
                return

            if not files:
                self.path_preview.set("Export preview: (no output)")
                return

            if len(files) == 1:
                self.path_preview.set(f"Export preview: {files[0]}")
                return

            # Multiple files: show folder + sample filenames
            names = [Path(f).name for f in files]
            show = names[:6]
            more = len(names) - len(show)
            lines = [f"Export preview: {out_dir}", "  " + "  ".join(show)]
            if more > 0:
                lines.append(f"  … +{more} more")
            self.path_preview.set("\n".join(lines))
        except Exception:
            try:
                self.path_preview.set("Export preview: (could not build preview)")
            except Exception:
                pass
    def quick_export(self):
        prof = self.profile_var.get()
        plan = self.build_export_plan(prof)

        # Ensure dirs exist
        try:
            plan["root"].mkdir(parents=True, exist_ok=True)
        except Exception:
            pass
        try:
            plan["out_dir"].mkdir(parents=True, exist_ok=True)
        except Exception:
            pass

        content = self.editor.get("1.0", tk.END)
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


    def _audit_retroarch_cores(self) -> None:
        """De-dupe and normalize RetroArch core list (keeps UI tidy, prevents mismatches).

        Rules:
          - Always include "Default (no subfolder)" as the first entry.
          - Remove blanks and duplicates (case-insensitive), preserving order.
        """
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

            # Ensure default is first
            default_name = "Default (no subfolder)"
            cleaned = [c for c in cleaned if c.casefold() != default_name.casefold()]
            cleaned.insert(0, default_name)

            self.prefs["retroarch_cores"] = cleaned
            # Keep selected core valid
            cur = (self.prefs.get("retroarch_core") or "").strip()
            if not cur or cur.casefold() not in {c.casefold() for c in cleaned}:
                self.prefs["retroarch_core"] = default_name
            save_prefs(self.prefs)
        except Exception:
            pass

    def _sync_core_dropdown(self):
        cores = self.prefs.get("retroarch_cores", list(DEFAULT_RETROARCH_CORES))
        self._core_cb.configure(values=cores)
        if self.core_var.get() not in cores:
            self.core_var.set(cores[0] if cores else "Default (no subfolder)")

    def manage_retroarch_cores(self):
        win = tk.Toplevel(self.root)
        win.title("RetroArch cores")
        win.geometry("640x460")
        win.transient(self.root)
        win.grab_set()
        sf = Scrollable(win); sf.pack(fill="both", expand=True)
        sf.set_canvas_bg(self.effective_colors()["bg"])
        ttk.Label(sf.inner, text="RetroArch cores", font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=12, pady=(12, 4))
        ttk.Label(sf.inner, text="Cores control the subfolder under cheats/. RetroArch is multi-platform.").pack(anchor="w", padx=12, pady=(0, 10))
        list_frame = ttk.Frame(sf.inner); list_frame.pack(fill="both", expand=True, padx=12, pady=(0, 10))
        lb = tk.Listbox(list_frame, activestyle="none")
        vsb = ttk.Scrollbar(list_frame, orient="vertical", command=lb.yview)
        lb.configure(yscrollcommand=vsb.set); lb.grid(row=0, column=0, sticky="nsew"); vsb.grid(row=0, column=1, sticky="ns")
        list_frame.columnconfigure(0, weight=1); list_frame.rowconfigure(0, weight=1)
        c = self.effective_colors(); btn = dict(DEFAULT_BUTTON_COLORS); btn.update(self.prefs.get("button_colors", {}))
        lb.configure(bg=c["panel2"], fg=c["text"], selectbackground=btn.get("primary", DEFAULT_BUTTON_COLORS["primary"]), selectforeground="#ffffff", highlightthickness=1, highlightbackground=c["border"])
        def refresh():
            lb.delete(0, tk.END)
            for item in self.prefs.get("retroarch_cores", []): lb.insert(tk.END, item)
        def selected() -> Optional[str]:
            sel = lb.curselection()
            return lb.get(sel[0]) if sel else None
        def add():
            name = ask_text(win, "Add core", "Core name (folder name):")
            if not name: return
            cores = self.prefs.get("retroarch_cores", [])
            if name not in cores: cores.append(name)
            self.prefs["retroarch_cores"] = cores; save_prefs(self.prefs); refresh(); self._sync_core_dropdown()
        def edit():
            cur = selected()
            if not cur: return
            name = ask_text(win, "Edit core", f"New name (current: {cur}):")
            if not name: return
            cores = self.prefs.get("retroarch_cores", [])
            if cur in cores:
                cores[cores.index(cur)] = name
            self.prefs["retroarch_cores"] = cores
            if self.prefs.get("retroarch_core") == cur:
                self.prefs["retroarch_core"] = name; self.core_var.set(name)
            save_prefs(self.prefs); refresh(); self._sync_core_dropdown()
        def remove():
            cur = selected()
            if not cur: return
            cores = [x for x in self.prefs.get("retroarch_cores", []) if x != cur]
            if not cores: cores = list(DEFAULT_RETROARCH_CORES)
            self.prefs["retroarch_cores"] = cores
            if self.prefs.get("retroarch_core") == cur:
                self.prefs["retroarch_core"] = cores[0]; self.core_var.set(cores[0])
            save_prefs(self.prefs); refresh(); self._sync_core_dropdown()
        btns = ttk.Frame(sf.inner); btns.pack(fill="x", padx=12, pady=(0, 12))
        ttk.Button(btns, text="Add", command=add).pack(side="left")
        ttk.Button(btns, text="Edit", command=edit).pack(side="left", padx=(8, 0))
        ttk.Button(btns, text="Remove", style="Danger.TButton", command=remove).pack(side="left", padx=(8, 0))
        ttk.Button(btns, text="Close", command=win.destroy).pack(side="right")
        refresh()

    def open_help_links(self):
        win = tk.Toplevel(self.root); win.title("Help Links"); win.geometry("900x560")
        win.transient(self.root); win.grab_set()
        sf = Scrollable(win); sf.pack(fill="both", expand=True); sf.set_canvas_bg(self.effective_colors()["bg"])
        ttk.Label(sf.inner, text="Help Links", font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=12, pady=(12, 4))
        ttk.Label(sf.inner, text="Quick links to cheat resources. You can edit these anytime.").pack(anchor="w", padx=12, pady=(0, 10))

        table_frame = ttk.Frame(sf.inner); table_frame.pack(fill="both", expand=True, padx=12, pady=(0, 10))
        tree = ttk.Treeview(table_frame, columns=("name", "url"), show="headings")
        tree.heading("name", text="Name"); tree.heading("url", text="URL")
        tree.column("name", width=240, anchor="w"); tree.column("url", width=620, anchor="w")
        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
        hsb = ttk.Scrollbar(table_frame, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        tree.grid(row=0, column=0, sticky="nsew"); vsb.grid(row=0, column=1, sticky="ns"); hsb.grid(row=1, column=0, sticky="ew")
        table_frame.columnconfigure(0, weight=1); table_frame.rowconfigure(0, weight=1)

        def refresh(select_idx: Optional[int] = None):
            for i in tree.get_children():
                tree.delete(i)
            for idx, item in enumerate(self.prefs.get("help_links", [])):
                tree.insert("", "end", iid=str(idx), values=(item.get("name",""), item.get("url","")))
            if select_idx is not None:
                try:
                    iid = str(max(0, min(select_idx, len(self.prefs.get("help_links", [])) - 1)))
                    tree.selection_set(iid)
                    tree.see(iid)
                except Exception:
                    pass

        def sel_idx() -> Optional[int]:
            sel = tree.selection()
            if not sel: return None
            try: return int(sel[0])
            except Exception: return None

        def open_link():
            i = sel_idx()
            if i is None: return
            url = self.prefs["help_links"][i].get("url","")
            if url: webbrowser.open(url)

        def _normalize_url(u: str) -> str:
            u = (u or "").strip()
            if not u:
                return ""
            if not (u.startswith("http://") or u.startswith("https://")):
                u = "https://" + u
            return u

        def _guess_name_from_url(u: str) -> str:
            try:
                from urllib.parse import urlparse
                host = urlparse(u).netloc or ""
                host = host.lower()
                if host.startswith("www."):
                    host = host[4:]
                # take first label
                if host:
                    label = host.split(".")[0]
                    return (label[:1].upper() + label[1:]) if label else "Link"
            except Exception:
                pass
            return "Link"

        def add_link():
            name = ask_text(win, "Add link", "Link name:")
            if not name: return
            url = ask_text(win, "Add link", "URL:")
            if not url: return
            url = _normalize_url(url)
            self.prefs.setdefault("help_links", []).append({"name": name, "url": url})
            save_prefs(self.prefs); refresh(len(self.prefs.get("help_links", [])) - 1)

        def add_multiple():
            dlg = tk.Toplevel(win)
            dlg.title("Add multiple links")
            dlg.transient(win); dlg.grab_set()
            dlg.geometry("720x520")

            ttk.Label(dlg, text="Paste links (one per line)", font=("Segoe UI", 11, "bold")).pack(anchor="w", padx=12, pady=(12, 4))
            ttk.Label(
                dlg,
                text=("Formats supported:\n"
                     "• Name | https://example.com\n"
                     "• Name - https://example.com\n"
                     "• https://example.com  (name will be guessed)"),
                justify="left"
            ).pack(anchor="w", padx=12, pady=(0, 10))

            box = ttk.Frame(dlg); box.pack(fill="both", expand=True, padx=12, pady=(0, 10))
            box.columnconfigure(0, weight=1); box.rowconfigure(0, weight=1)
            txt = tk.Text(box, wrap="none", height=12)
            v = ttk.Scrollbar(box, orient="vertical", command=txt.yview)
            txt.configure(yscrollcommand=v.set)
            txt.grid(row=0, column=0, sticky="nsew")
            v.grid(row=0, column=1, sticky="ns")

            # Theme editor-ish
            c = self.effective_colors()
            btn = dict(DEFAULT_BUTTON_COLORS); btn.update(self.prefs.get("button_colors", {}))
            try:
                txt.configure(
                    bg=c.get("editor_bg", c.get("panel2", "#ffffff")),
                    fg=c.get("editor_fg", c.get("text", "#000000")),
                    insertbackground=c.get("editor_fg", c.get("text", "#000000")),
                    selectbackground=btn.get("primary", DEFAULT_BUTTON_COLORS["primary"]),
                    selectforeground="#ffffff",
                )
            except Exception:
                pass

            def parse_lines(raw: str):
                out = []
                for ln in (raw or "").splitlines():
                    s = ln.strip()
                    if not s:
                        continue
                    name = ""
                    url = ""
                    if "|" in s:
                        left, right = s.split("|", 1)
                        name = left.strip()
                        url = right.strip()
                    elif " - " in s:
                        left, right = s.split(" - ", 1)
                        name = left.strip()
                        url = right.strip()
                    elif "	" in s:
                        left, right = s.split("	", 1)
                        name = left.strip()
                        url = right.strip()
                    else:
                        # url only
                        url = s.strip()
                        name = ""
                    url = _normalize_url(url)
                    if not url:
                        continue
                    if not name:
                        name = _guess_name_from_url(url)
                    out.append({"name": name, "url": url})
                return out

            def add_all():
                raw = txt.get("1.0", "end-1c")
                items = parse_lines(raw)

                if not items:
                    messagebox.showinfo("Add multiple", "No valid links found.", parent=dlg)
                    return

                # de-dupe by URL (case-insensitive)
                existing = {(x.get("url","").strip().lower()) for x in (self.prefs.get("help_links", []) or [])}
                added = 0
                for it in items:
                    u = it.get("url","").strip().lower()
                    if not u or u in existing:
                        continue
                    self.prefs.setdefault("help_links", []).append(it)
                    existing.add(u)
                    added += 1

                save_prefs(self.prefs)
                refresh(len(self.prefs.get("help_links", [])) - 1)
                self.status.set(f"Added {added} link(s).")
                dlg.destroy()

            br = ttk.Frame(dlg); br.pack(fill="x", padx=12, pady=(0, 12))
            ttk.Button(br, text="Add All", style="Primary.TButton", command=add_all).pack(side="left")
            ttk.Button(br, text="Cancel", command=dlg.destroy).pack(side="left", padx=(8, 0))

        def edit_link():
            i = sel_idx()
            if i is None: return
            cur = self.prefs["help_links"][i]
            name = ask_text(win, "Edit link", f"Name (current: {cur.get('name','')}):") or cur.get("name","")
            url = ask_text(win, "Edit link", f"URL (current: {cur.get('url','')}):") or cur.get("url","")
            url = _normalize_url(url)
            self.prefs["help_links"][i] = {"name": name, "url": url}
            save_prefs(self.prefs); refresh(i)

        def remove_link():
            i = sel_idx()
            if i is None: return
            self.prefs["help_links"].pop(i); save_prefs(self.prefs); refresh(max(i-1, 0))

        def move_up():
            i = sel_idx()
            if i is None or i <= 0: return
            links = self.prefs.get("help_links", [])
            links[i-1], links[i] = links[i], links[i-1]
            self.prefs["help_links"] = links
            save_prefs(self.prefs); refresh(i-1)

        def move_down():
            i = sel_idx()
            links = self.prefs.get("help_links", [])
            if i is None or i >= len(links)-1: return
            links[i+1], links[i] = links[i], links[i+1]
            self.prefs["help_links"] = links
            save_prefs(self.prefs); refresh(i+1)

        def sort_az():
            links = list(self.prefs.get("help_links", []) or [])
            links.sort(key=lambda d: (d.get("name","") or "").casefold())
            self.prefs["help_links"] = links
            save_prefs(self.prefs); refresh(0)

        btns = ttk.Frame(sf.inner); btns.pack(fill="x", padx=12, pady=(0, 12))
        ttk.Button(btns, text="Open", command=open_link).pack(side="left")
        ttk.Button(btns, text="Add", command=add_link).pack(side="left", padx=(8, 0))
        ttk.Button(btns, text="Add Multiple…", command=add_multiple).pack(side="left", padx=(8, 0))
        ttk.Button(btns, text="Edit", command=edit_link).pack(side="left", padx=(8, 0))
        ttk.Button(btns, text="Remove", style="Danger.TButton", command=remove_link).pack(side="left", padx=(8, 0))

        ttk.Separator(sf.inner).pack(fill="x", padx=12, pady=(0, 10))

        ord_row = ttk.Frame(sf.inner); ord_row.pack(fill="x", padx=12, pady=(0, 12))
        ttk.Label(ord_row, text="Order:").pack(side="left")
        ttk.Button(ord_row, text="Move Up", command=move_up).pack(side="left", padx=(8, 0))
        ttk.Button(ord_row, text="Move Down", command=move_down).pack(side="left", padx=(8, 0))
        ttk.Button(ord_row, text="Sort A–Z", command=sort_az).pack(side="left", padx=(8, 0))
        ttk.Button(ord_row, text="Close", command=win.destroy).pack(side="right")

        # Double-click to open
        tree.bind("<Double-1>", lambda _e: open_link())

        refresh()


    def open_templates(self):
        prof = self.profile_var.get()
        tpls = list_templates(prof)
        win = tk.Toplevel(self.root); win.title(f"Templates — {prof}"); win.geometry("980x640")
        win.transient(self.root); win.grab_set()
        sf = Scrollable(win); sf.pack(fill="both", expand=True); sf.set_canvas_bg(self.effective_colors()["bg"])
        ttk.Label(sf.inner, text="Templates", font=("Segoe UI", 13, "bold")).pack(anchor="w", padx=12, pady=(12, 2))
        ttk.Label(sf.inner, text="Templates are saved starting points for this emulator.\nChoose a template to preview it, then apply it to your editor.").pack(anchor="w", padx=12, pady=(0, 10))
        main = ttk.Frame(sf.inner); main.pack(fill="both", expand=True, padx=12, pady=(0, 10))
        main.columnconfigure(0, weight=1, uniform="cols"); main.columnconfigure(1, weight=2, uniform="cols"); main.rowconfigure(0, weight=1)
        left = ttk.Frame(main); left.grid(row=0, column=0, sticky="nsew", padx=(0, 10)); left.columnconfigure(0, weight=1); left.rowconfigure(2, weight=1)
        ttk.Label(left, text="Template list", font=("Segoe UI", 10, "bold")).grid(row=0, column=0, sticky="w")
        ttk.Label(left, text="Double-click a template to Load & replace.").grid(row=1, column=0, sticky="w", pady=(2, 8))
        lb = tk.Listbox(left, activestyle="none"); vsb = ttk.Scrollbar(left, orient="vertical", command=lb.yview)
        lb.configure(yscrollcommand=vsb.set); lb.grid(row=2, column=0, sticky="nsew"); vsb.grid(row=2, column=1, sticky="ns")
        c = self.effective_colors(); btn = dict(DEFAULT_BUTTON_COLORS); btn.update(self.prefs.get("button_colors", {}))
        lb.configure(bg=c["panel2"], fg=c["text"], selectbackground=btn.get("primary", DEFAULT_BUTTON_COLORS["primary"]), selectforeground="#ffffff", highlightthickness=1, highlightbackground=c["border"])
        for t in tpls: lb.insert(tk.END, t)
        right = ttk.Frame(main); right.grid(row=0, column=1, sticky="nsew"); right.columnconfigure(0, weight=1); right.rowconfigure(2, weight=1)
        ttk.Label(right, text="Preview (read-only)", font=("Segoe UI", 10, "bold")).grid(row=0, column=0, sticky="w")
        ttk.Label(right, text="This will not change your editor until you click a button below.").grid(row=1, column=0, sticky="w", pady=(2, 8))
        preview = tk.Text(right, wrap=tk.NONE, height=16)
        pvsb = ttk.Scrollbar(right, orient="vertical", command=preview.yview)
        phsb = ttk.Scrollbar(right, orient="horizontal", command=preview.xview)
        preview.configure(yscrollcommand=pvsb.set, xscrollcommand=phsb.set)
        preview.grid(row=2, column=0, sticky="nsew"); pvsb.grid(row=2, column=1, sticky="ns"); phsb.grid(row=3, column=0, sticky="ew")
        preview.configure(bg=c["editor_bg"], fg=c["editor_fg"], insertbackground=c["editor_fg"], selectbackground=btn.get("primary", DEFAULT_BUTTON_COLORS["primary"]), selectforeground="#ffffff")
        def selected_name() -> str:
            sel = lb.curselection()
            return tpls[sel[0]] if sel else (tpls[0] if tpls else "Blank")
        def refresh_preview(*_):
            preview.delete("1.0", tk.END); preview.insert("1.0", read_template(prof, selected_name()))
        def do_load_replace():
            try: self.editor.edit_separator()
            except Exception: pass
            self.editor.delete("1.0", tk.END); self.editor.insert("1.0", read_template(prof, selected_name())); win.destroy()
        lb.bind("<<ListboxSelect>>", refresh_preview)
        lb.bind("<Double-Button-1>", lambda _e: do_load_replace())
        default_name = self.prefs.get("templates_default", {}).get(prof, "Blank")
        if default_name in tpls:
            i = tpls.index(default_name); lb.selection_set(i); lb.see(i)
        elif tpls:
            lb.selection_set(0)
        refresh_preview()
        def do_insert():
            self.editor.insert(tk.INSERT, read_template(prof, selected_name())); win.destroy()
        def do_save_current():
            name = ask_text(win, "Save Template", "Template name (saved for this emulator):")
            if not name: return
            write_template(prof, name, self.editor.get("1.0", tk.END)); self.status.set(f"Template saved: {name}"); win.destroy()
        def do_set_default():
            self.prefs.setdefault("templates_default", {})[prof] = selected_name(); save_prefs(self.prefs); self.status.set(f"Default template set: {selected_name()}"); win.destroy()
        def do_open_folder():
            folder = profile_templates_dir(prof)
            try: os.startfile(folder)  # type: ignore[attr-defined]
            except Exception: messagebox.showinfo("Templates folder", str(folder))
        def do_reset_files():
            folder = profile_templates_dir(prof)
            for fp in folder.glob("*.txt"):
                try: fp.unlink()
                except Exception: pass
            self.status.set("Templates reset."); win.destroy()
        def do_insert_helper():
            kind = self.get_profile_info(prof).get("kind", "generic")
            if kind == "switch":
                snippet = "# Switch helper\n# TitleID stays the same.\n# BuildID changes with updates.\n# Atmosphère path: atmosphere/contents/<TID>/cheats/<BID>.txt\n\n"
            elif kind == "retroarch":
                snippet = "# RetroArch helper (multi-platform)\n# Path: RetroArch/cheats/<Core Name>/<Game>.cht\n# Pick your core in the Helper panel.\n\n"
            else:
                snippet = "# Helper snippet\n# Safe starting structure for this emulator.\n\n"
            self.editor.insert(tk.INSERT, snippet); win.destroy()
        ttk.Separator(sf.inner).pack(fill="x", padx=12, pady=(0, 10))
        br = ttk.Frame(sf.inner); br.pack(fill="x", padx=12, pady=(0, 6))
        ttk.Label(br, text="Apply template to editor:").pack(side="left")
        ttk.Button(br, text="Insert", command=do_insert).pack(side="left", padx=(10, 0))
        ttk.Button(br, text="Load & replace", command=do_load_replace).pack(side="left", padx=(8, 0))
        ttk.Button(br, text="Close", command=win.destroy).pack(side="right")
        ttk.Label(sf.inner, text="Insert keeps your existing text. Load & replace starts the editor from the template.").pack(anchor="w", padx=12, pady=(0, 8))
        adv_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(sf.inner, text="Show advanced options", variable=adv_var).pack(anchor="w", padx=12, pady=(0, 6))
        adv_panel = ttk.LabelFrame(sf.inner, text="Advanced (template management)")
        adv_row = ttk.Frame(adv_panel); adv_row.pack(fill="x", padx=10, pady=10)
        ttk.Button(adv_row, text="Save editor as template", command=do_save_current).pack(side="left")
        ttk.Button(adv_row, text="Set as default", command=do_set_default).pack(side="left", padx=(8, 0))
        ttk.Button(adv_row, text="Open template folder", command=do_open_folder).pack(side="left", padx=(8, 0))
        ttk.Button(adv_row, text="Reset templates (files)", style="Danger.TButton", command=do_reset_files).pack(side="left", padx=(8, 0))
        ttk.Button(adv_row, text="Insert helper snippet", command=do_insert_helper).pack(side="left", padx=(8, 0))
        ttk.Label(adv_panel, text="Advanced is optional. Most users only need Insert / Load.").pack(anchor="w", padx=10, pady=(0, 10))
        def sync_adv(*_):
            if adv_var.get(): adv_panel.pack(fill="x", padx=12, pady=(0, 12))
            else: adv_panel.pack_forget()
        adv_var.trace_add("write", sync_adv); sync_adv()

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
            notes_vsb = ttk.Scrollbar(notes_frame, orient="vertical", command=notes.yview)
            notes.configure(yscrollcommand=notes_vsb.set)
            notes.grid(row=0, column=0, sticky="nsew")
            notes_vsb.grid(row=0, column=1, sticky="ns")
            notes_frame.columnconfigure(0, weight=1)
            notes_frame.rowconfigure(0, weight=1)

            # Allow the helper text area to expand inside this dialog.
            frm.rowconfigure(5, weight=1)

            notes.insert("1.0", existing.get("notes", ""))

            counter_var = tk.StringVar(value="")
            counter_lbl = ttk.Label(help_wrap, textvariable=counter_var)
            counter_lbl.pack(anchor="w", pady=(6, 0))

            def update_counter():
                txt = notes.get("1.0", "end-1c")
                chars = len(txt)
                approx_visible = self._estimate_helper_visible_chars()
                overflow = chars - approx_visible
                if overflow > 0:
                    counter_var.set(f"Characters: {chars}   |   Fits in Helper: ~{approx_visible}   |   Over by: {overflow}")
                else:
                    counter_var.set(f"Characters: {chars}   |   Fits in Helper: ~{approx_visible}")

            notes.bind("<KeyRelease>", lambda e: update_counter())
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

                info = {
                    "subdir": subdir_var.get().strip(),
                    "filename_hint": fname_var.get().strip(),
                    "extensions": exts,
                    "notes": notes.get("1.0", "end-1c").strip(),
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

        mode_row = ttk.Frame(app_sf.inner); mode_row.pack(fill="x", padx=12, pady=(0, 10))
        ttk.Label(mode_row, text="Mode:").pack(side="left")
        ttk.Radiobutton(mode_row, text="Dark (Default)", value="dark", variable=mode_var).pack(side="left", padx=(12,0))
        ttk.Radiobutton(mode_row, text="Light", value="light", variable=mode_var).pack(side="left", padx=(12,0))
        ttk.Radiobutton(mode_row, text="Custom", value="custom", variable=mode_var).pack(side="left", padx=(12,0))

        ttk.Label(app_sf.inner, text="Custom colours only apply when Mode is set to Custom.", wraplength=900).pack(anchor="w", padx=12, pady=(0, 10))

        # Editor font size (applies after Apply)
        row = ttk.Frame(app_sf.inner); row.pack(fill="x", padx=12, pady=(0, 10))
        ttk.Label(row, text="Editor font size:").pack(side="left")
        font_var = tk.IntVar(value=int(self.prefs.get("editor_font_size", 11) or 11))
        ttk.Spinbox(row, from_=8, to=24, textvariable=font_var, width=6).pack(side="left", padx=(8, 0))
        ttk.Label(row, text="(applies after Apply)").pack(side="left", padx=(8, 0))

        ttk.Separator(app_sf.inner).pack(fill="x", padx=12, pady=10)

        # Theme colours (Custom mode)
        ttk.Label(app_sf.inner, text="Theme colours", font=("Segoe UI", 11, "bold")).pack(anchor="w", padx=12, pady=(0, 6))
        ttk.Label(app_sf.inner, text="Custom mode only. These control UI + editor colours.", wraplength=900).pack(anchor="w", padx=12, pady=(0, 8))

        fields = [("bg","Window background"),("panel","Panel background"),("panel2","Secondary panel"),("text","Main text"),("muted","Muted text"),("entry","Entry/dropdown background"),("border","Borders"),("editor_bg","Editor background"),("editor_fg","Editor text")]
        color_vars: Dict[str, tk.StringVar] = {}
        cur_theme = dict(DEFAULT_THEME_DARK if self.prefs.get("mode")=="dark" else DEFAULT_THEME_LIGHT); cur_theme.update(self.prefs.get("custom_theme", {}))
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
            ("neutral","Neutral accents"),
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
        _sync_custom_controls()

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
        overrides_group = ttk.LabelFrame(tab_adv, text="Export Root Overrides (built-in profiles)")
        overrides_group.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        tab_paths = overrides_group


        ttk.Label(tab_adv, text="Advanced", font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=12, pady=(12, 6))
        ttk.Label(tab_adv, text="Window size memory and other power options.",).pack(anchor="w", padx=12, pady=(0, 12))

        remember_var = tk.BooleanVar(value=bool(self.prefs.get("window_remember", True)))
        ttk.Checkbutton(tab_adv, text="Remember window size & position", variable=remember_var).pack(anchor="w", padx=12, pady=(0, 10))

        adv_btns = ttk.Frame(tab_adv); adv_btns.pack(fill="x", padx=12, pady=(0, 12))
        ttk.Button(adv_btns, text="Save current size as default", command=self.save_current_window_size).pack(side="left")
        ttk.Button(adv_btns, text="Clear saved window size", command=self.clear_saved_window_size).pack(side="left", padx=(8, 0))

        def _apply_adv():
            self.prefs["window_remember"] = bool(remember_var.get())
            save_prefs(self.prefs)
            self.status.set("Advanced settings saved.")
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
            if mode_var.get() in ("dark","light"):
                self.prefs["mode"] = mode_var.get()
            self.prefs["editor_font_size"]=int(font_var.get())
            self.prefs["custom_theme"]={k:v.get().strip() for k,v in color_vars.items()}
            self.prefs["button_colors"]={k:v.get().strip() for k,v in btn_vars.items()}
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

if __name__ == "__main__":
    App().run()
