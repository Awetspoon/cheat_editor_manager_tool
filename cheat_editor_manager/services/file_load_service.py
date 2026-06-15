from __future__ import annotations

import re
import tkinter as tk
from pathlib import Path
from typing import Optional

from tkinter import filedialog, messagebox

from ..export_logic import (
    clean_hex as _clean_hex,
    extract_switch_metadata,
    normalize_bids,
    normalize_profile_id,
)
from ..profiles import profile_display_group
from . import retroarch_core_service


CHEAT_FILE_TYPES = [
    ("Cheat files", "*.txt *.cht *.ini *.pnach *.yml *.yaml *.json *.xml *.dat"),
    ("All files", "*.*"),
]


def load_file_into_app(app, filepath: Optional[str] = None) -> None:
    if not filepath:
        filepath = filedialog.askopenfilename(title="Load cheat file", filetypes=CHEAT_FILE_TYPES)
    if not filepath:
        return

    path = Path(filepath)
    text = _read_cheat_file(path)
    if text is None:
        return

    _fill_editor(app, path, text)
    _detect_loaded_file(app, path, text)
    app.refresh_profile_info()


def _read_cheat_file(path: Path) -> Optional[str]:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        try:
            return path.read_text(encoding="latin-1", errors="replace")
        except Exception as exc:
            messagebox.showerror("Load File", f"Could not read file:\n{path}\n\n{exc}")
            return None


def _fill_editor(app, path: Path, text: str) -> None:
    app.editor.delete("1.0", tk.END)
    app.editor.insert("1.0", text)
    app.status.set(f"Loaded: {path.name}")


def _detect_loaded_file(app, path: Path, text: str) -> None:
    path_text = str(path).replace("\\", "/")
    lower_path = path_text.lower()
    filename = path.name.lower()

    _detect_citra_layout(app, path, lower_path)
    _detect_luma_layout(app, lower_path, filename)
    _detect_retroarch_layout(app, path, path_text, lower_path)
    _detect_atmosphere_layout(app, path, lower_path)
    _detect_switch_emulator_layouts(app, path, lower_path)
    _detect_switch_header_metadata(app, text)
    _detect_generic_profile_layouts(app, path, lower_path, filename)


def _profile_values(app) -> set[str]:
    return set(app.get_profile_values())


def _set_profile(app, profile_name: str, profile_values: Optional[set[str]] = None) -> bool:
    available = profile_values if profile_values is not None else _profile_values(app)
    if profile_name not in available:
        return False

    app.profile_var.set(profile_name)
    if hasattr(app, "profile_group_var"):
        try:
            app.profile_group_var.set(profile_display_group(app.prefs, profile_name))
        except Exception:
            pass
    refresh_dropdown = getattr(app, "refresh_profiles_dropdown", None)
    if callable(refresh_dropdown):
        refresh_dropdown()
    try:
        app.profile_cb.set(profile_name)
    except Exception:
        pass
    return True


def _set_title_id(app, raw_value: str) -> None:
    title_id = _clean_hex(raw_value)
    if len(title_id) == 16:
        app.tid_var.set(title_id)


def _set_build_id(app, raw_value: str) -> None:
    build_id = _clean_hex(raw_value)
    if len(build_id) in (16, 32):
        app.bid_var.set(build_id)


def _detect_citra_layout(app, path: Path, lower_path: str) -> None:
    if "/saves/citra/cheats/" not in lower_path or path.suffix.lower() != ".txt":
        return

    _set_title_id(app, path.stem)
    _set_profile(app, "Citra (3DS) - PC")


def _detect_luma_layout(app, lower_path: str, filename: str) -> None:
    if "/luma/plugins/" not in lower_path or filename != "cheats.txt":
        return

    title_id = lower_path.split("/luma/plugins/")[-1].split("/")[0]
    _set_title_id(app, title_id)
    _set_profile(app, "Nintendo 3DS (CFW) (Luma)")


def _detect_retroarch_layout(app, path: Path, path_text: str, lower_path: str) -> None:
    if "/cheats/" not in lower_path or path.suffix.lower() != ".cht" or "/duckstation/" in lower_path:
        return

    parts = path_text.split("/")
    lower_parts = [part.lower() for part in parts]
    remaining: list[str] = []
    default_core_name = retroarch_core_service.DEFAULT_CORE_NAME
    core_folder = ""

    if "cheats" in lower_parts:
        index = len(lower_parts) - 1 - lower_parts[::-1].index("cheats")
        remaining = parts[index + 1 :]
        if len(remaining) >= 2:
            core_folder = (remaining[0] or "").strip()
        elif len(remaining) == 1:
            core_folder = default_core_name

    if not core_folder:
        return

    _set_profile(app, "RetroArch (Multi-platform)")

    cores = retroarch_core_service.normalize_core_list(app.prefs.get("retroarch_cores"))
    wanted_core = retroarch_core_service.normalize_core_name(core_folder)
    matched_name = ""
    for core in cores:
        if retroarch_core_service.normalize_core_name(core) == wanted_core:
            matched_name = core
            break

    if matched_name:
        app.core_var.set(matched_name)
        app._show_core(True)
        app.status.set(f"Detected RetroArch core: {matched_name}")
    elif wanted_core == retroarch_core_service.normalize_core_name(default_core_name):
        app.core_var.set(default_core_name)
        app._show_core(True)
        app.status.set(f"Detected RetroArch core: {default_core_name}")
    elif len(remaining) >= 2:
        app._show_core(True)
        app.status.set(f"Detected RetroArch core folder '{core_folder}', but it isn't in your core list.")


def _detect_atmosphere_layout(app, path: Path, lower_path: str) -> None:
    if "/atmosphere/contents/" not in lower_path or "/cheats/" not in lower_path:
        return

    title_id = lower_path.split("/atmosphere/contents/")[-1].split("/")[0]
    _set_title_id(app, title_id)
    _set_build_id(app, path.stem)
    _set_profile(app, "Atmosphere (Switch) (CFW)")


def _detect_switch_emulator_layouts(app, path: Path, lower_path: str) -> None:
    if "/load/" in lower_path and "/cheats/" in lower_path:
        title_id = lower_path.split("/load/")[-1].split("/")[0]
        _set_title_id(app, title_id)
        _set_build_id(app, path.stem)
        _set_profile(app, _switch_load_profile_name(lower_path))

    if "/mods/contents/" in lower_path and "/cheats/" in lower_path:
        title_id = lower_path.split("/mods/contents/")[-1].split("/")[0]
        _set_title_id(app, title_id)
        _set_build_id(app, path.stem)
        _set_profile(app, "Ryujinx (Switch) - PC")


def _switch_load_profile_name(lower_path: str) -> str:
    if "/yuzu/" in lower_path:
        return "Yuzu (Switch) - PC"
    if "/sudachi/" in lower_path:
        return "Sudachi (Switch) - PC"
    if "/suyu/" in lower_path:
        return "Suyu (Switch) - PC"
    return ""


def _detect_switch_header_metadata(app, text: str) -> None:
    metadata = extract_switch_metadata(text)
    current_bids = normalize_bids(app.bid_var.get())
    merged_bids = list(current_bids)

    if len(_clean_hex(app.tid_var.get())) != 16 and metadata["tid"]:
        app.tid_var.set(metadata["tid"])

    for bid in metadata["bids"]:
        if bid not in merged_bids:
            merged_bids.append(bid)
    if merged_bids:
        app.bid_var.set(", ".join(merged_bids))

    if metadata["bids"] and len(_clean_hex(app.tid_var.get())) == 16:
        _set_profile(app, "Atmosphere (Switch) (CFW)")


def _detect_generic_profile_layouts(app, path: Path, lower_path: str, filename: str) -> None:
    profile_values = _profile_values(app)

    def set_profile(profile_name: str) -> bool:
        return _set_profile(app, profile_name, profile_values)

    def set_profile_id_from_filename(profile_name: str, raw_value: str) -> None:
        normalized = _normalized_profile_id(app, profile_name, raw_value)
        if normalized:
            app.tid_var.set(normalized)

    if filename.endswith(".pnach") and set_profile("PCSX2 (PS2) - PC"):
        set_profile_id_from_filename("PCSX2 (PS2) - PC", path.stem)

    if "/gamesettings/" in lower_path and filename.endswith(".ini") and set_profile("Dolphin (GC/Wii) - PC"):
        set_profile_id_from_filename("Dolphin (GC/Wii) - PC", path.stem)

    if (
        ("/psp/cheats/" in lower_path or "/memstick/psp/cheats/" in lower_path)
        and filename.endswith(".ini")
        and set_profile("PPSSPP (PSP) - PC")
    ):
        set_profile_id_from_filename("PPSSPP (PSP) - PC", path.stem)

    if (
        ("/vitacheat/db/" in lower_path or "/psvita/vitacheat/db/" in lower_path)
        and filename.endswith(".psv")
        and set_profile("PS Vita (CFW) (taiHEN)")
    ):
        set_profile_id_from_filename("PS Vita (CFW) (taiHEN)", path.stem)

    if (
        ("/seplugins/cwcheat/" in lower_path or "/psp/seplugins/cwcheat/" in lower_path)
        and filename.endswith(".ini")
        and set_profile("PSP (CFW)")
    ):
        set_profile_id_from_filename("PSP (CFW)", path.stem)

    if _looks_like_wii_homebrew_code(lower_path, filename) and set_profile("Wii (Homebrew)"):
        set_profile_id_from_filename("Wii (Homebrew)", path.stem)

    if (
        ("/wiiu/codes/" in lower_path or "/wii u/codes/" in lower_path)
        and filename.endswith(".txt")
        and set_profile("Wii U (CFW)")
    ):
        set_profile_id_from_filename("Wii U (CFW)", path.stem)

    if (
        "/duckstation/" in lower_path
        and "/cheats/" in lower_path
        and filename.endswith(".cht")
        and set_profile("DuckStation (PS1) - PC")
    ):
        set_profile_id_from_filename("DuckStation (PS1) - PC", path.stem)

    if "/patches/" in lower_path and filename.endswith(".patch.toml") and set_profile("Xenia (Xbox 360) - PC"):
        set_profile_id_from_filename("Xenia (Xbox 360) - PC", path.name[: -len(".patch.toml")])

    if filename in ("patch.yml", "patch.yaml"):
        set_profile("RPCS3 (PS3) - PC")


def _normalized_profile_id(app, profile_name: str, raw_value: str) -> str:
    info = app.get_profile_info(profile_name)
    normalized = normalize_profile_id(info, raw_value)
    if not normalized:
        return ""

    id_regex = str(info.get("id_regex") or "").strip()
    if id_regex and not re.fullmatch(id_regex, normalized):
        return ""
    return normalized


def _looks_like_wii_homebrew_code(lower_path: str, filename: str) -> bool:
    return (
        filename.endswith(".gct")
        and ("/wii/codes/" in lower_path or "/codes/" in lower_path)
    ) or (filename.endswith(".txt") and "/txtcodes/" in lower_path)
