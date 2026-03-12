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


def load_file_into_app(app, filepath: Optional[str] = None):
    self = app
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


    # Atmosphere/contents/<TID>/cheats/<BID>.txt
    if "/atmosphere/contents/" in sl and "/cheats/" in sl:
        try:
            tid_raw = sl.split("/atmosphere/contents/")[-1].split("/")[0]
            tid = _clean_hex(tid_raw)
            if len(tid) == 16:
                self.tid_var.set(tid)

            # Atmosphere BuildID is commonly 32 hex, but some sources show 16.
            bid = _clean_hex(p.stem)
            if len(bid) in (16, 32):
                self.bid_var.set(bid)

            # Auto-switch profile to Atmosphere
            atm_name = "Atmosphere (Switch) (CFW)"
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
            atm_name = "Atmosphere (Switch) (CFW)"
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
        profile_values = set(self.get_profile_values())

        def _set_profile(profile_name: str) -> bool:
            if profile_name not in profile_values:
                return False
            self.profile_var.set(profile_name)
            try:
                self.profile_cb.set(profile_name)
            except Exception:
                pass
            return True

        def _normalized_profile_id(profile_name: str, raw_value: str) -> str:
            info = self.get_profile_info(profile_name)
            normalized = normalize_profile_id(info, raw_value)
            if not normalized:
                return ""
            id_regex = str(info.get("id_regex") or "").strip()
            if id_regex and not re.fullmatch(id_regex, normalized):
                return ""
            return normalized

        def _set_profile_id_from_filename(profile_name: str, raw_value: str) -> None:
            normalized = _normalized_profile_id(profile_name, raw_value)
            if normalized:
                self.tid_var.set(normalized)

        # PCSX2 (.pnach)
        if fname.endswith(".pnach") and _set_profile("PCSX2 (PS2) - PC"):
            _set_profile_id_from_filename("PCSX2 (PS2) - PC", p.stem)

        # Dolphin GameSettings (.ini)
        if "/gamesettings/" in sl2 and fname.endswith(".ini") and _set_profile("Dolphin (GC/Wii) - PC"):
            _set_profile_id_from_filename("Dolphin (GC/Wii) - PC", p.stem)

        # PPSSPP cheats (.ini) commonly in memstick/PSP/Cheats
        if ("/psp/cheats/" in sl2 or "/memstick/psp/cheats/" in sl2) and fname.endswith(".ini") and _set_profile("PPSSPP (PSP) - PC"):
            _set_profile_id_from_filename("PPSSPP (PSP) - PC", p.stem)

        # Modded console layouts (best-effort path detection + ID from filename)
        if ("/vitacheat/db/" in sl2 or "/psvita/vitacheat/db/" in sl2) and fname.endswith(".psv") and _set_profile("PS Vita (CFW) (taiHEN)"):
            _set_profile_id_from_filename("PS Vita (CFW) (taiHEN)", p.stem)

        if ("/seplugins/cwcheat/" in sl2 or "/psp/seplugins/cwcheat/" in sl2) and fname.endswith(".ini") and _set_profile("PSP (CFW)"):
            _set_profile_id_from_filename("PSP (CFW)", p.stem)

        if (fname.endswith(".gct") and ("/wii/codes/" in sl2 or "/codes/" in sl2)) or (fname.endswith(".txt") and "/txtcodes/" in sl2):
            if _set_profile("Wii (Homebrew)"):
                _set_profile_id_from_filename("Wii (Homebrew)", p.stem)

        if ("/wiiu/codes/" in sl2 or "/wii u/codes/" in sl2) and fname.endswith(".txt") and _set_profile("Wii U (CFW)"):
            _set_profile_id_from_filename("Wii U (CFW)", p.stem)

        # DuckStation (.cht)
        if "/duckstation/" in sl2 and "/cheats/" in sl2 and fname.endswith(".cht") and _set_profile("DuckStation (PS1) - PC"):
            _set_profile_id_from_filename("DuckStation (PS1) - PC", p.stem)

        # Xenia patches (.patch.toml)
        if "/patches/" in sl2 and fname.endswith(".patch.toml") and _set_profile("Xenia (Xbox 360) - PC"):
            _set_profile_id_from_filename("Xenia (Xbox 360) - PC", p.name[:-len(".patch.toml")])

        # RPCS3 patch.yml
        if fname in ("patch.yml", "patch.yaml"):
            _set_profile("RPCS3 (PS3) - PC")
    except Exception:
        pass

    # Refresh helper UI state based on current selected profile
    self.refresh_profile_info()

