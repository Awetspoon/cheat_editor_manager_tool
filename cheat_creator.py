import json
import os
import re
import sys
import subprocess
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

APP_TITLE = "Cheat File Creator"
PROFILES_FILENAME = "profiles.json"
PREFS_FILENAME = "user_prefs.json"

# Theme colors
ACCENT_COLOR = "#7C3AED"
DANGER_COLOR = "#DC2626"
BG_COLOR = "#0B1220"
CARD_COLOR = "#111A2E"
TEXT_BG = "#0F172A"
TEXT_FG = "#E5E7EB"
MUTED_FG = "#9CA3AF"


# ------------------ HELPERS ------------------

def app_base_dir():
    """
    Folder where the app should read/write its JSON files:
    - when built (.exe): the folder containing the .exe (dist)
    - when running (.py): the folder containing this .py file
    """
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def load_json(path):
    if not os.path.exists(path):
        # Create an empty JSON file so the EXE can always find it next to itself (first run)
        try:
            save_json(path, {})
        except Exception:
            return {}
        return {}

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def normalize_ext(ext):
    ext = (ext or "").strip().lower()
    if not ext:
        return ""
    return ext if ext.startswith(".") else "." + ext


def safe_filename(name, fallback="file"):
    s = (name or "").strip()
    s = re.sub(r"\s+", " ", s)
    s = re.sub(r'[\\/:*?"<>|]+', "_", s)
    s = s.strip(" .")
    return s if s else fallback


def load_profiles(path):
    if not os.path.exists(path):
        raise FileNotFoundError("profiles.json not found")

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    profiles = data.get("profiles", [])
    if not isinstance(profiles, list) or not profiles:
        raise ValueError("profiles.json must contain a non-empty 'profiles' list")

    for p in profiles:
        if "id" not in p or "name" not in p:
            raise ValueError("Each profile must include 'id' and 'name'")
        if "extensions" not in p or not isinstance(p["extensions"], list) or not p["extensions"]:
            raise ValueError("Each profile must include a non-empty 'extensions' list")
        if "default_extension" not in p:
            raise ValueError("Each profile must include 'default_extension'")
        if "templates" in p and not isinstance(p["templates"], list):
            raise ValueError("If present, 'templates' must be a list")

    return profiles


def get_platform_default_export_root():
    android_root = "/storage/emulated/0"
    if os.path.isdir(android_root):
        return os.path.join(android_root, "CheatCreator")

    home = os.path.expanduser("~")
    docs = os.path.join(home, "Documents")
    if os.path.isdir(docs):
        return os.path.join(docs, "CheatCreator")

    return os.path.join(home, "CheatCreator")


def try_open_folder(path):
    if not path or not os.path.isdir(path):
        return False, "Export Root folder is missing or invalid."
    try:
        if sys.platform.startswith("win"):
            os.startfile(path)  # type: ignore[attr-defined]
            return True, ""
        if sys.platform == "darwin":
            subprocess.run(["open", path], check=False)
            return True, ""
        subprocess.run(["xdg-open", path], check=False)
        return True, ""
    except Exception as e:
        return False, str(e)


# ------------------ CHEAT HELPER DIALOG ------------------

class AddCheatDialog(tk.Toplevel):
    def __init__(self, parent, on_insert):
        super().__init__(parent)
        self.title("Add Cheat (Helper)")
        self.configure(bg=BG_COLOR)
        self.resizable(False, False)
        self.on_insert = on_insert

        self.desc_var = tk.StringVar()
        self.enabled_var = tk.BooleanVar(value=False)

        frm = ttk.Frame(self, padding=12)
        frm.pack(fill="both", expand=True)

        ttk.Label(frm, text="Cheat Description / Name:").grid(row=0, column=0, sticky="w")
        desc_entry = ttk.Entry(frm, textvariable=self.desc_var, width=50)
        desc_entry.grid(row=1, column=0, sticky="we", pady=(4, 10))

        ttk.Label(frm, text="Cheat Codes (one per line):").grid(row=2, column=0, sticky="w")
        self.codes_text = tk.Text(frm, width=60, height=8, bg=TEXT_BG, fg=TEXT_FG, insertbackground=TEXT_FG)
        self.codes_text.grid(row=3, column=0, sticky="we", pady=(4, 10))

        ttk.Checkbutton(frm, text="Enabled by default (used by RetroArch helper)", variable=self.enabled_var)\
            .grid(row=4, column=0, sticky="w", pady=(0, 10))

        btns = ttk.Frame(frm)
        btns.grid(row=5, column=0, sticky="e")

        ttk.Button(btns, text="Cancel", command=self.destroy).grid(row=0, column=0, padx=(0, 8))
        ttk.Button(btns, text="Insert", style="Accent.TButton", command=self._insert).grid(row=0, column=1)

        self.grab_set()
        self.transient(parent)
        desc_entry.focus_set()

    def _insert(self):
        desc = (self.desc_var.get() or "").strip()
        codes_raw = self.codes_text.get("1.0", "end").strip("\n")

        codes = []
        for line in codes_raw.splitlines():
            s = line.strip()
            if s:
                codes.append(s)

        if not desc:
            messagebox.showerror("Missing info", "Please enter a cheat description/name.")
            return
        if not codes:
            messagebox.showerror("Missing info", "Please enter at least one cheat code line.")
            return

        self.on_insert(desc, codes, bool(self.enabled_var.get()))
        self.destroy()


# ------------------ APP ------------------

class CheatCreatorApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.minsize(980, 860)
        self.configure(bg=BG_COLOR)

        # IMPORTANT FIX: use exe folder when frozen, script folder when running .py
        self.base_dir = app_base_dir()
        self.profiles_path = os.path.join(self.base_dir, PROFILES_FILENAME)
        self.prefs_path = os.path.join(self.base_dir, PREFS_FILENAME)

        # prefs:
        # {
        #   "export_root": "...",
        #   "template_defaults": { "<profile_id>": "<template_id>" }
        # }
        self.prefs = load_json(self.prefs_path)
        self.prefs.setdefault("export_root", "")
        self.prefs.setdefault("template_defaults", {})

        self.profiles = []
        self.profile_by_name = {}

        self.profile_name_var = tk.StringVar()
        self.filename_var = tk.StringVar(value="cheats")

        # RetroArch fields
        self.ra_core_var = tk.StringVar()
        self.ra_rom_var = tk.StringVar()

        # PPSSPP field
        self.ppsspp_game_id_var = tk.StringVar()

        # Dolphin field
        self.dolphin_game_id_var = tk.StringVar()

        # PCSX2 field
        self.pcsx2_crc_var = tk.StringVar()

        # Switch fields
        self.switch_tid_var = tk.StringVar()
        self.switch_bid_var = tk.StringVar()

        # RetroArch Citra field
        self.citra_game_id_var = tk.StringVar()

        # Templates
        self.template_choice_var = tk.StringVar()
        self.template_id_by_display = {}

        self._apply_theme()
        self._build_ui()

        self.reload_profiles()
        self.ensure_export_root()

    # ------------------ THEME ------------------

    def _apply_theme(self):
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except Exception:
            pass

        style.configure(".", background=BG_COLOR, foreground=TEXT_FG)
        style.configure("TFrame", background=BG_COLOR)
        style.configure("Card.TFrame", background=CARD_COLOR)
        style.configure("TLabel", background=BG_COLOR, foreground=TEXT_FG)
        style.configure("Muted.TLabel", background=BG_COLOR, foreground=MUTED_FG)

        style.configure("TEntry", fieldbackground=TEXT_BG, foreground=TEXT_FG)
        style.configure("TCombobox", fieldbackground=TEXT_BG, foreground=TEXT_FG)

        style.configure("Accent.TButton", background=ACCENT_COLOR, foreground="white")
        style.configure("Danger.TButton", background=DANGER_COLOR, foreground="white")

    # ------------------ UI ------------------

    def _build_ui(self):
        header = tk.Frame(self, bg=ACCENT_COLOR)
        header.pack(fill="x")

        tk.Label(
            header,
            text="Cheat File Creator",
            bg=ACCENT_COLOR,
            fg="white",
            font=("Segoe UI", 14, "bold"),
            padx=12,
            pady=10
        ).pack(side="left")

        root = ttk.Frame(self, style="Card.TFrame", padding=12)
        root.pack(fill="both", expand=True, padx=12, pady=12)
        root.grid_columnconfigure(0, weight=1)

        row = 0

        # Export root row
        self.export_root_var = tk.StringVar(value=self.prefs.get("export_root", ""))

        er = ttk.Frame(root)
        er.grid(row=row, column=0, sticky="we", pady=8)
        er.grid_columnconfigure(1, weight=1)

        ttk.Label(er, text="Export Root:").grid(row=0, column=0, sticky="w")
        ttk.Entry(er, textvariable=self.export_root_var, state="readonly").grid(row=0, column=1, sticky="we")
        ttk.Button(er, text="Open Folder", command=self.open_export_root).grid(row=0, column=2, padx=6)
        ttk.Button(er, text="Change…", command=self.change_export_root).grid(row=0, column=3, padx=6)
        ttk.Button(er, text="Reset Default", command=self.reset_export_root_default).grid(row=0, column=4, padx=6)

        row += 1

        # Emulator selector
        ttk.Label(root, text="Emulator / Console:").grid(row=row, column=0, sticky="w")
        row += 1

        emu_row = ttk.Frame(root)
        emu_row.grid(row=row, column=0, sticky="we", pady=6)
        emu_row.grid_columnconfigure(0, weight=1)

        self.profile_combo = ttk.Combobox(emu_row, textvariable=self.profile_name_var, state="readonly")
        self.profile_combo.grid(row=0, column=0, sticky="we")
        self.profile_combo.bind("<<ComboboxSelected>>", lambda e: self.on_profile_change())

        ttk.Button(emu_row, text="Reload profiles", command=self.reload_profiles).grid(row=0, column=1, padx=6)
        row += 1

        # Template row + helper
        tpl_row = ttk.Frame(root)
        tpl_row.grid(row=row, column=0, sticky="we", pady=(6, 10))
        tpl_row.grid_columnconfigure(1, weight=1)

        ttk.Label(tpl_row, text="Template:").grid(row=0, column=0, sticky="w")
        self.template_combo = ttk.Combobox(tpl_row, textvariable=self.template_choice_var, state="readonly")
        self.template_combo.grid(row=0, column=1, sticky="we", padx=6)

        ttk.Button(tpl_row, text="Open Template", style="Accent.TButton", command=self.open_template)\
            .grid(row=0, column=2, padx=6)
        ttk.Button(tpl_row, text="Add Cheat (Helper)", style="Accent.TButton", command=self.open_add_cheat)\
            .grid(row=0, column=3, padx=6)
        ttk.Button(tpl_row, text="Reset Default Template", style="Danger.TButton", command=self.reset_default_template)\
            .grid(row=0, column=4, padx=6)
        ttk.Button(tpl_row, text="Reset ALL Defaults", style="Danger.TButton", command=self.reset_all_default_templates)\
            .grid(row=0, column=5, padx=6)

        row += 1

        ttk.Label(
            root,
            text="Quick Export builds the right folder structure for supported emulators. Convert & Save lets you choose any location/extension.",
            style="Muted.TLabel"
        ).grid(row=row, column=0, sticky="w", pady=(0, 10))
        row += 1

        # Quick Export frames
        self.ra_frame = ttk.LabelFrame(root, text="RetroArch Quick Export")
        self.ra_frame.grid(row=row, column=0, sticky="we", pady=6)
        self.ra_frame.grid_columnconfigure(1, weight=1)
        ttk.Label(self.ra_frame, text="Core Name:").grid(row=0, column=0, sticky="w")
        ttk.Entry(self.ra_frame, textvariable=self.ra_core_var).grid(row=0, column=1, sticky="we")
        ttk.Label(self.ra_frame, text="ROM Name (no extension):").grid(row=1, column=0, sticky="w")
        ttk.Entry(self.ra_frame, textvariable=self.ra_rom_var).grid(row=1, column=1, sticky="we")
        ttk.Label(self.ra_frame, text="Path: ExportRoot/RetroArch/cheats/<Core>/<ROM>.cht", style="Muted.TLabel").grid(
            row=2, column=0, columnspan=2, sticky="w", pady=(4, 0)
        )
        row += 1

        self.ppsspp_frame = ttk.LabelFrame(root, text="PPSSPP Quick Export")
        self.ppsspp_frame.grid(row=row, column=0, sticky="we", pady=6)
        self.ppsspp_frame.grid_columnconfigure(1, weight=1)
        ttk.Label(self.ppsspp_frame, text="Game ID (ex: ULUS12345):").grid(row=0, column=0, sticky="w")
        ttk.Entry(self.ppsspp_frame, textvariable=self.ppsspp_game_id_var).grid(row=0, column=1, sticky="we")
        ttk.Label(self.ppsspp_frame, text="Path: ExportRoot/PPSSPP/PSP/Cheats/<GAME_ID>.ini", style="Muted.TLabel").grid(
            row=1, column=0, columnspan=2, sticky="w", pady=(4, 0)
        )
        row += 1

        self.dolphin_frame = ttk.LabelFrame(root, text="Dolphin Quick Export")
        self.dolphin_frame.grid(row=row, column=0, sticky="we", pady=6)
        self.dolphin_frame.grid_columnconfigure(1, weight=1)
        ttk.Label(self.dolphin_frame, text="Game ID (ex: GMSE01):").grid(row=0, column=0, sticky="w")
        ttk.Entry(self.dolphin_frame, textvariable=self.dolphin_game_id_var).grid(row=0, column=1, sticky="we")
        ttk.Label(self.dolphin_frame, text="Path: ExportRoot/Dolphin/GameSettings/<GAME_ID>.ini", style="Muted.TLabel").grid(
            row=1, column=0, columnspan=2, sticky="w", pady=(4, 0)
        )
        row += 1

        self.pcsx2_frame = ttk.LabelFrame(root, text="PCSX2 Quick Export")
        self.pcsx2_frame.grid(row=row, column=0, sticky="we", pady=6)
        self.pcsx2_frame.grid_columnconfigure(1, weight=1)
        ttk.Label(self.pcsx2_frame, text="CRC (8 hex, ex: A1B2C3D4):").grid(row=0, column=0, sticky="w")
        ttk.Entry(self.pcsx2_frame, textvariable=self.pcsx2_crc_var).grid(row=0, column=1, sticky="we")
        ttk.Label(self.pcsx2_frame, text="Path: ExportRoot/PCSX2/cheats/<CRC>.pnach", style="Muted.TLabel").grid(
            row=1, column=0, columnspan=2, sticky="w", pady=(4, 0)
        )
        row += 1

        self.switch_frame = ttk.LabelFrame(root, text="Nintendo Switch (Atmosphère) Quick Export")
        self.switch_frame.grid(row=row, column=0, sticky="we", pady=6)
        self.switch_frame.grid_columnconfigure(1, weight=1)
        ttk.Label(self.switch_frame, text="TID (16 hex):").grid(row=0, column=0, sticky="w")
        ttk.Entry(self.switch_frame, textvariable=self.switch_tid_var).grid(row=0, column=1, sticky="we")
        ttk.Label(self.switch_frame, text="BID (16 hex):").grid(row=1, column=0, sticky="w")
        ttk.Entry(self.switch_frame, textvariable=self.switch_bid_var).grid(row=1, column=1, sticky="we")
        ttk.Label(self.switch_frame, text="Path: ExportRoot/Switch/atmosphere/contents/<TID>/cheats/<BID>.txt", style="Muted.TLabel").grid(
            row=2, column=0, columnspan=2, sticky="w", pady=(4, 0)
        )
        row += 1

        self.citra_frame = ttk.LabelFrame(root, text="RetroArch - Citra Core Quick Export")
        self.citra_frame.grid(row=row, column=0, sticky="we", pady=6)
        self.citra_frame.grid_columnconfigure(1, weight=1)
        ttk.Label(self.citra_frame, text="3DS Game ID (hex):").grid(row=0, column=0, sticky="w")
        ttk.Entry(self.citra_frame, textvariable=self.citra_game_id_var).grid(row=0, column=1, sticky="we")
        ttk.Label(self.citra_frame, text="Path: ExportRoot/RetroArch/saves/Citra/cheats/<game_id>.txt", style="Muted.TLabel").grid(
            row=1, column=0, columnspan=2, sticky="w", pady=(4, 0)
        )
        row += 1

        # Default file name
        file_row = ttk.Frame(root)
        file_row.grid(row=row, column=0, sticky="we", pady=(10, 4))
        file_row.grid_columnconfigure(1, weight=1)

        ttk.Label(file_row, text="Default file name (no extension):").grid(row=0, column=0, sticky="w")
        ttk.Entry(file_row, textvariable=self.filename_var).grid(row=0, column=1, sticky="we")
        row += 1

        # Editor
        ttk.Label(root, text="Cheat text editor:").grid(row=row, column=0, sticky="w", pady=(10, 4))
        row += 1

        self.text = tk.Text(root, bg=TEXT_BG, fg=TEXT_FG, insertbackground=TEXT_FG, undo=True)
        self.text.grid(row=row, column=0, sticky="nsew")
        root.grid_rowconfigure(row, weight=1)
        row += 1

        # Buttons row
        br = ttk.Frame(root)
        br.grid(row=row, column=0, sticky="we", pady=10)
        br.grid_columnconfigure(4, weight=1)

        ttk.Button(br, text="Open File…", command=self.open_file).grid(row=0, column=0)
        ttk.Button(br, text="Save As…", command=self.save_as).grid(row=0, column=1, padx=6)
        ttk.Button(br, text="Quick Export", style="Accent.TButton", command=self.quick_export).grid(row=0, column=2, padx=6)
        ttk.Button(br, text="Convert & Save", command=self.convert_and_save).grid(row=0, column=3)

        self.status = tk.StringVar(value="Ready.")
        ttk.Label(br, textvariable=self.status, style="Muted.TLabel").grid(row=0, column=4, sticky="e")

        # Hide quick-export frames at start (only show when profile selected)
        self.ra_frame.grid_remove()
        self.ppsspp_frame.grid_remove()
        self.dolphin_frame.grid_remove()
        self.pcsx2_frame.grid_remove()
        self.switch_frame.grid_remove()
        self.citra_frame.grid_remove()

    # ------------------ PROFILES ------------------

    def reload_profiles(self):
        try:
            self.profiles = load_profiles(self.profiles_path)
        except Exception as e:
            messagebox.showerror("Error", str(e))
            return

        self.profile_by_name = {p["name"]: p for p in self.profiles}
        names = list(self.profile_by_name.keys())
        self.profile_combo["values"] = names

        if names:
            current = self.profile_name_var.get()
            self.profile_name_var.set(current if current in self.profile_by_name else names[0])

        self.on_profile_change()
        self.status.set("Profiles loaded ✅")

    def current_profile(self):
        return self.profile_by_name.get(self.profile_name_var.get())

    def on_profile_change(self):
        p = self.current_profile()
        self.ra_frame.grid_remove()
        self.ppsspp_frame.grid_remove()
        self.dolphin_frame.grid_remove()
        self.pcsx2_frame.grid_remove()
        self.switch_frame.grid_remove()
        self.citra_frame.grid_remove()

        if not p:
            self._refresh_templates(None)
            return

        pid = p.get("id")
        if pid == "retroarch":
            self.ra_frame.grid()
        elif pid == "ppsspp":
            self.ppsspp_frame.grid()
        elif pid == "dolphin":
            self.dolphin_frame.grid()
        elif pid == "pcsx2":
            self.pcsx2_frame.grid()
        elif pid == "switch_atmosphere":
            self.switch_frame.grid()
        elif pid == "retroarch_citra":
            self.citra_frame.grid()

        self._refresh_templates(p)
        self.status.set("Selected: " + p.get("name", ""))

    def detect_profile_for_path(self, filepath):
        fname = os.path.basename(filepath).lower()
        best = None
        best_len = -1

        for p in self.profiles:
            for e in p.get("extensions", []):
                ext = normalize_ext(e.get("extension", "")).lower()
                if ext and fname.endswith(ext) and len(ext) > best_len:
                    best = p
                    best_len = len(ext)

        if best:
            self.profile_name_var.set(best["name"])
            self.on_profile_change()
            return best
        return None

    # ------------------ TEMPLATES ------------------

    def _get_templates(self, profile):
        templates = profile.get("templates", [])
        return templates if isinstance(templates, list) else []

    def _refresh_templates(self, profile):
        self.template_id_by_display = {}
        self.template_combo["values"] = []
        self.template_choice_var.set("")

        if not profile:
            self.template_combo["values"] = ["(No profile)"]
            self.template_choice_var.set("(No profile)")
            return

        templates = self._get_templates(profile)
        if not templates:
            self.template_combo["values"] = ["(No templates)"]
            self.template_choice_var.set("(No templates)")
            return

        values = []
        for t in templates:
            tid = str(t.get("id", "")).strip()
            name = str(t.get("name", tid)).strip() or tid
            values.append(name)
            self.template_id_by_display[name] = tid

        self.template_combo["values"] = values

        profile_id = str(profile.get("id", "")).strip()
        pref_default = self.prefs.get("template_defaults", {}).get(profile_id)
        profile_default = profile.get("default_template_id")
        chosen_id = pref_default or profile_default or str(templates[0].get("id", "")).strip()

        chosen_display = None
        for disp, tid in self.template_id_by_display.items():
            if tid == chosen_id:
                chosen_display = disp
                break

        self.template_choice_var.set(chosen_display or values[0])

    def _selected_template_obj(self, profile):
        templates = self._get_templates(profile)
        if not templates:
            return None
        display = self.template_choice_var.get()
        tid = self.template_id_by_display.get(display)
        for t in templates:
            if str(t.get("id", "")).strip() == str(tid):
                return t
        return templates[0]

    def open_template(self):
        profile = self.current_profile()
        if not profile:
            return

        t = self._selected_template_obj(profile)
        if not t:
            messagebox.showinfo("Templates", "No templates found for this profile.")
            return

        content = str(t.get("content") or "")
        existing = self.text.get("1.0", "end").strip()

        if not existing:
            self.text.insert("1.0", content + ("\n" if content and not content.endswith("\n") else ""))
        else:
            choice = messagebox.askyesnocancel(
                "Open Template",
                "Replace the editor text?\n\nYes = Replace\nNo = Append\nCancel = Do nothing"
            )
            if choice is None:
                return
            if choice is True:
                self.text.delete("1.0", "end")
                self.text.insert("1.0", content + ("\n" if content and not content.endswith("\n") else ""))
            else:
                self.text.insert("end", ("\n" if not existing.endswith("\n") else "") + content)
                if content and not content.endswith("\n"):
                    self.text.insert("end", "\n")

        self.status.set("Template loaded ✅")

        profile_id = str(profile.get("id", "")).strip()
        template_id = str(t.get("id", "")).strip()
        if profile_id and template_id:
            if messagebox.askyesno("Set Default Template", "Set this template as the default for this console?"):
                self.prefs.setdefault("template_defaults", {})
                self.prefs["template_defaults"][profile_id] = template_id
                save_json(self.prefs_path, self.prefs)
                self.status.set("Default template saved ✅")

    def reset_default_template(self):
        profile = self.current_profile()
        if not profile:
            return

        profile_id = str(profile.get("id", "")).strip()
        defaults = self.prefs.setdefault("template_defaults", {})

        if profile_id not in defaults:
            messagebox.showinfo("Reset Default Template", "No custom default template is set for this console.")
            return

        if not messagebox.askyesno("Reset Default Template", "Remove your saved default template for this console?"):
            return

        del defaults[profile_id]
        save_json(self.prefs_path, self.prefs)
        self._refresh_templates(profile)
        self.status.set("Default template reset ✅")

    def reset_all_default_templates(self):
        defaults = self.prefs.setdefault("template_defaults", {})
        if not defaults:
            messagebox.showinfo("Reset ALL Defaults", "No saved defaults exist yet.")
            return

        if not messagebox.askyesno(
            "Reset ALL Defaults",
            "This will remove your saved default templates for EVERY console.\n\nContinue?"
        ):
            return

        self.prefs["template_defaults"] = {}
        save_json(self.prefs_path, self.prefs)

        profile = self.current_profile()
        if profile:
            self._refresh_templates(profile)

        self.status.set("All default templates reset ✅")

    # ------------------ ADD CHEAT HELPER ------------------

    def open_add_cheat(self):
        AddCheatDialog(self, self.insert_cheat_from_helper)

    def insert_cheat_from_helper(self, desc, code_lines, enabled):
        profile = self.current_profile()
        pid = profile.get("id") if profile else ""

        if pid == "retroarch":
            self._insert_retroarch_cht(desc, code_lines, enabled)
            return

        if pid == "switch_atmosphere":
            self._insert_switch_block(desc, code_lines)
            return

        # generic fallback for unknown formats
        block = []
        block.append("# Cheat Helper (generic)")
        block.append("# Description: " + desc)
        block.append("# Codes:")
        for c in code_lines:
            block.append("#   " + c)
        block.append("# Note: Some emulators require a very specific structure. Use templates as your base.")
        block.append("")
        self._append_to_editor("\n".join(block))
        self.status.set("Cheat helper inserted (generic) ✅")

    def _append_to_editor(self, text_block):
        existing = self.text.get("1.0", "end").rstrip("\n")
        if existing.strip():
            self.text.insert("end", "\n" + text_block + "\n")
        else:
            self.text.insert("1.0", text_block + "\n")

    def _insert_switch_block(self, desc, code_lines):
        # Atmosphère cheat blocks commonly look like:
        # [Cheat Name]
        # 04000000 XXXXXXXX YYYYYYYY
        # ...
        block = []
        block.append(f"[{desc}]")
        for c in code_lines:
            block.append(c.strip())
        block.append("")  # blank line after each cheat block
        self._append_to_editor("\n".join(block))
        self.status.set("Switch cheat block inserted ✅")

    def _insert_retroarch_cht(self, desc, code_lines, enabled):
        raw = self.text.get("1.0", "end").rstrip("\n")

        max_idx = -1
        for m in re.finditer(r"\bcheat(\d+)_desc\b", raw):
            try:
                max_idx = max(max_idx, int(m.group(1)))
            except Exception:
                pass
        next_idx = max_idx + 1

        joined_codes = "+".join([c.strip() for c in code_lines if c.strip()])
        snippet = "\n".join([
            f'cheat{next_idx}_desc = "{desc}"',
            f'cheat{next_idx}_code = "{joined_codes}"',
            f"cheat{next_idx}_enable = {'true' if enabled else 'false'}",
            ""
        ])

        if re.search(r"^\s*cheats\s*=", raw, flags=re.MULTILINE):
            def repl(m):
                return m.group(1) + str(next_idx + 1)
            raw2 = re.sub(r"^(\s*cheats\s*=\s*)\d+\s*$", repl, raw, flags=re.MULTILINE)
        else:
            raw2 = f"cheats = {next_idx + 1}\n\n" + raw

        raw2 = raw2.rstrip("\n") + "\n\n" + snippet if raw2.strip() else raw2 + snippet

        self.text.delete("1.0", "end")
        self.text.insert("1.0", raw2 + "\n")
        self.status.set(f"RetroArch cheat{next_idx} added ✅")

    # ------------------ FILE OPEN / SAVE AS ------------------

    def open_file(self):
        patterns = []
        seen = set()
        for p in self.profiles:
            for e in p.get("extensions", []):
                lab = e.get("label", "File")
                pat = e.get("pattern", "*.*")
                key = (lab, pat)
                if key not in seen:
                    patterns.append(key)
                    seen.add(key)
        patterns.append(("All files", "*.*"))

        path = filedialog.askopenfilename(title="Open cheat file", filetypes=patterns)
        if not path:
            return

        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
        except Exception as e:
            messagebox.showerror("Open failed", f"Could not read:\n{path}\n\n{e}")
            return

        self.detect_profile_for_path(path)

        base = os.path.basename(path)
        prof = self.current_profile()
        stripped = base
        if prof:
            best_ext = ""
            for e in prof.get("extensions", []):
                ext = normalize_ext(e.get("extension", "")).lower()
                if ext and base.lower().endswith(ext) and len(ext) > len(best_ext):
                    best_ext = ext
            if best_ext:
                stripped = base[: -len(best_ext)]
        if stripped == base:
            stripped = os.path.splitext(base)[0]
        self.filename_var.set(stripped or "cheats")

        self.text.delete("1.0", "end")
        self.text.insert("1.0", content)
        self.status.set("File opened ✅")

    def save_as(self):
        self.convert_and_save()

    # ------------------ EXPORT ROOT ------------------

    def ensure_export_root(self):
        root = (self.prefs.get("export_root") or "").strip()
        if root and os.path.isdir(root):
            self.export_root_var.set(root)
            return

        default_root = get_platform_default_export_root()
        try:
            os.makedirs(default_root, exist_ok=True)
            self.prefs["export_root"] = default_root
            save_json(self.prefs_path, self.prefs)
            self.export_root_var.set(default_root)
            self.status.set("Export Root set to default ✅")
        except Exception:
            messagebox.showinfo("Export Root", "Choose a folder where Cheat Creator will store exports.")
            self.change_export_root()

    def change_export_root(self):
        current = (self.prefs.get("export_root") or "").strip()
        default_root = get_platform_default_export_root()

        start_dir = current if current and os.path.isdir(current) else os.path.dirname(default_root)
        if not os.path.isdir(start_dir):
            start_dir = os.path.expanduser("~")

        path = filedialog.askdirectory(initialdir=start_dir, title="Choose Export Root Folder")
        if not path:
            return

        try:
            os.makedirs(path, exist_ok=True)
        except Exception as e:
            messagebox.showerror("Export Root error", f"Could not use this folder:\n{path}\n\n{e}")
            return

        self.prefs["export_root"] = path
        save_json(self.prefs_path, self.prefs)
        self.export_root_var.set(path)
        self.status.set("Export Root updated ✅")

    def reset_export_root_default(self):
        default_root = get_platform_default_export_root()
        try:
            os.makedirs(default_root, exist_ok=True)
        except Exception as e:
            messagebox.showerror("Reset failed", f"Could not create default folder:\n{default_root}\n\n{e}")
            return

        self.prefs["export_root"] = default_root
        save_json(self.prefs_path, self.prefs)
        self.export_root_var.set(default_root)
        self.status.set("Export Root reset to default ✅")

    def open_export_root(self):
        root = (self.prefs.get("export_root") or "").strip()
        if not root:
            messagebox.showinfo("Open Folder", "Export Root is not set yet.")
            return
        ok, err = try_open_folder(root)
        if not ok:
            messagebox.showinfo("Open Folder", f"Could not auto-open folder.\n\nPath:\n{root}\n\n{err}")

    # ------------------ VALIDATION ------------------

    def _validate_switch_hex16(self, value, label):
        v = re.sub(r"\s+", "", (value or "")).lower()
        if not re.fullmatch(r"[0-9a-f]{16}", v):
            return v, f"{label} should be exactly 16 hex characters."
        return v, None

    def _warn_if_not(self, condition, title, message):
        if condition:
            return True
        return messagebox.askyesno(title, message + "\n\nContinue anyway?")

    # ------------------ EXPORT PATH BUILDING ------------------

    def build_export_path(self, profile):
        root = (self.prefs.get("export_root") or "").strip()
        if not root:
            return None

        pid = profile.get("id")

        if pid == "retroarch":
            core = safe_filename(self.ra_core_var.get(), "Core")
            rom = safe_filename(self.ra_rom_var.get(), "ROM")
            if not core or not rom:
                messagebox.showerror("Missing fields", "RetroArch Quick Export needs Core Name and ROM Name.")
                return None
            out_dir = os.path.join(root, "RetroArch", "cheats", core)
            os.makedirs(out_dir, exist_ok=True)
            return os.path.join(out_dir, rom + ".cht")

        if pid == "ppsspp":
            game_id = re.sub(r"\s+", "", (self.ppsspp_game_id_var.get() or "")).upper()
            self.ppsspp_game_id_var.set(game_id)
            if not game_id:
                messagebox.showerror("Missing fields", "PPSSPP Quick Export needs Game ID (e.g. ULUS12345).")
                return None
            ok = bool(re.fullmatch(r"[A-Z0-9]{9}", game_id))
            if not self._warn_if_not(ok, "Validation warning", "PPSSPP Game ID usually looks like ULUS12345 (9 letters/numbers)."):
                return None
            out_dir = os.path.join(root, "PPSSPP", "PSP", "Cheats")
            os.makedirs(out_dir, exist_ok=True)
            return os.path.join(out_dir, game_id + ".ini")

        if pid == "dolphin":
            game_id = re.sub(r"\s+", "", (self.dolphin_game_id_var.get() or "")).upper()
            self.dolphin_game_id_var.set(game_id)
            if not game_id:
                messagebox.showerror("Missing fields", "Dolphin Quick Export needs Game ID (e.g. GMSE01).")
                return None
            ok = bool(re.fullmatch(r"[A-Z0-9]{6}", game_id))
            if not self._warn_if_not(ok, "Validation warning", "Dolphin Game ID usually looks like GMSE01 (6 letters/numbers)."):
                return None
            out_dir = os.path.join(root, "Dolphin", "GameSettings")
            os.makedirs(out_dir, exist_ok=True)
            return os.path.join(out_dir, game_id + ".ini")

        if pid == "pcsx2":
            crc = re.sub(r"\s+", "", (self.pcsx2_crc_var.get() or "")).upper()
            self.pcsx2_crc_var.set(crc)
            if not crc:
                messagebox.showerror("Missing fields", "PCSX2 Quick Export needs CRC (8 hex, e.g. A1B2C3D4).")
                return None
            ok = bool(re.fullmatch(r"[0-9A-F]{8}", crc))
            if not self._warn_if_not(ok, "Validation warning", "PCSX2 CRC is usually 8 hex characters (0-9, A-F)."):
                return None
            out_dir = os.path.join(root, "PCSX2", "cheats")
            os.makedirs(out_dir, exist_ok=True)
            return os.path.join(out_dir, crc + ".pnach")

        if pid == "retroarch_citra":
            game_id = safe_filename(self.citra_game_id_var.get(), "game_id").lower()
            if not game_id:
                messagebox.showerror("Missing fields", "Citra Quick Export needs Game ID.")
                return None
            out_dir = os.path.join(root, "RetroArch", "saves", "Citra", "cheats")
            os.makedirs(out_dir, exist_ok=True)
            return os.path.join(out_dir, game_id + ".txt")

        if pid == "switch_atmosphere":
            tid, tid_warn = self._validate_switch_hex16(self.switch_tid_var.get(), "TID")
            bid, bid_warn = self._validate_switch_hex16(self.switch_bid_var.get(), "BID")
            self.switch_tid_var.set(tid)
            self.switch_bid_var.set(bid)

            warn = "\n".join([w for w in [tid_warn, bid_warn] if w])
            if warn:
                if not messagebox.askyesno("Validation warning", warn + "\n\nContinue anyway?"):
                    return None

            out_dir = os.path.join(root, "Switch", "atmosphere", "contents", tid, "cheats")
            os.makedirs(out_dir, exist_ok=True)
            return os.path.join(out_dir, bid + ".txt")

        out_dir = os.path.join(root, safe_filename(profile.get("name", "Exports")))
        os.makedirs(out_dir, exist_ok=True)
        base = safe_filename(self.filename_var.get(), "cheats")
        ext = normalize_ext(profile.get("default_extension") or ".txt")
        return os.path.join(out_dir, base + ext)

    # ------------------ ACTIONS ------------------

    def quick_export(self):
        p = self.current_profile()
        if not p:
            return

        content = self.text.get("1.0", "end").strip()
        if not content:
            messagebox.showerror("Empty", "Editor is empty")
            return

        path = self.build_export_path(p)
        if not path:
            return

        if os.path.exists(path):
            if not messagebox.askyesno("Overwrite?", f"File exists:\n{path}\n\nOverwrite it?"):
                return

        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(content + "\n")
        except Exception as e:
            messagebox.showerror("Export failed", f"Could not write:\n{path}\n\n{e}")
            return

        messagebox.showinfo("Exported", f"Saved to:\n{path}")
        self.status.set("Quick Export complete ✅")

    def convert_and_save(self):
        p = self.current_profile()
        if not p:
            return

        content = self.text.get("1.0", "end").strip()
        if not content:
            messagebox.showerror("Empty", "Editor is empty")
            return

        filetypes = [(e.get("label", "File"), e.get("pattern", "*.*")) for e in p.get("extensions", [])]
        initial = safe_filename(self.filename_var.get(), "cheats")

        path = filedialog.asksaveasfilename(
            defaultextension=p.get("default_extension"),
            filetypes=filetypes,
            initialfile=initial
        )
        if not path:
            return

        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(content + "\n")
        except Exception as e:
            messagebox.showerror("Save failed", f"Could not write:\n{path}\n\n{e}")
            return

        self.status.set("File saved ✅")


if __name__ == "__main__":
    CheatCreatorApp().mainloop()
