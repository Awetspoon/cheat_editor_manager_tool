from __future__ import annotations

import json
from pathlib import Path
from typing import List, Optional

from .constants import (
    DEFAULT_BUTTON_COLORS,
    DEFAULT_HELP_LINKS,
    DEFAULT_PREFS,
    DEFAULT_PROFILES,
    DEFAULT_RETROARCH_CORES,
    DEFAULT_THEME_DARK,
    PREFS_FILE,
    TEMPLATES_DIR,
)

LEGACY_BUTTON_COLORS = {
    "header": "#c62828",
    "primary": "#c62828",
    "secondary": "#ffffff",
    "toolbar": "#ffffff",
    "danger": "#c62828",
}

BRANDING_V1_BUTTON_COLORS = {
    "header": "#432f23",
    "primary": "#ca4c2d",
    "secondary": "#2f241c",
    "toolbar": "#574233",
    "danger": "#a92b2b",
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

    if int(data.get("branding_revision", 0) or 0) < 1:
        saved_buttons = dict(data.get("button_colors") or {})
        if (not saved_buttons) or saved_buttons == LEGACY_BUTTON_COLORS:
            prefs["button_colors"] = dict(DEFAULT_BUTTON_COLORS)
        prefs["branding_revision"] = 1

    if int(data.get("branding_revision", 0) or 0) < 2:
        saved_buttons = dict(prefs.get("button_colors") or {})
        if (not saved_buttons) or saved_buttons == BRANDING_V1_BUTTON_COLORS:
            prefs["button_colors"] = dict(DEFAULT_BUTTON_COLORS)
        prefs["branding_revision"] = 2

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
    PREFS_FILE.parent.mkdir(parents=True, exist_ok=True)
    temp_file = PREFS_FILE.with_suffix(PREFS_FILE.suffix + ".tmp")
    temp_file.write_text(json.dumps(prefs, indent=2, ensure_ascii=False), encoding="utf-8")
    temp_file.replace(PREFS_FILE)

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



