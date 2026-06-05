from __future__ import annotations

import json

from ..constants import (
    DEFAULT_BUTTON_COLORS,
    DEFAULT_PREFS,
    DEFAULT_THEME_DARK,
    PREFS_FILE,
)
from ..services import help_link_service
from ..services import retroarch_core_service

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

STALE_PREF_KEYS = (
    "window_remember",
    "window_geometry",
    "window_asked_once",
)


def load_prefs() -> dict:
    data = _read_prefs_file()
    prefs = dict(DEFAULT_PREFS)
    prefs.update(data)

    _remove_stale_keys(prefs)
    _apply_branding_migrations(prefs, data)
    _ensure_pref_shapes(prefs)
    _clean_custom_profiles(prefs)
    return prefs


def save_prefs(prefs: dict) -> None:
    PREFS_FILE.parent.mkdir(parents=True, exist_ok=True)
    temp_file = PREFS_FILE.with_suffix(PREFS_FILE.suffix + ".tmp")
    temp_file.write_text(
        json.dumps(prefs, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    temp_file.replace(PREFS_FILE)


def _read_prefs_file() -> dict:
    if not PREFS_FILE.exists():
        return {}
    try:
        loaded = json.loads(PREFS_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return loaded if isinstance(loaded, dict) else {}


def _remove_stale_keys(prefs: dict) -> None:
    for key in STALE_PREF_KEYS:
        prefs.pop(key, None)


def _apply_branding_migrations(prefs: dict, raw_data: dict) -> None:
    if int(raw_data.get("branding_revision", 0) or 0) < 1:
        saved_buttons = dict(raw_data.get("button_colors") or {})
        if (not saved_buttons) or saved_buttons == LEGACY_BUTTON_COLORS:
            prefs["button_colors"] = dict(DEFAULT_BUTTON_COLORS)
        prefs["branding_revision"] = 1

    if int(raw_data.get("branding_revision", 0) or 0) < 2:
        saved_buttons = dict(prefs.get("button_colors") or {})
        if (not saved_buttons) or saved_buttons == BRANDING_V1_BUTTON_COLORS:
            prefs["button_colors"] = dict(DEFAULT_BUTTON_COLORS)
        prefs["branding_revision"] = 2


def _ensure_pref_shapes(prefs: dict) -> None:
    prefs["help_links"] = help_link_service.merge_default_links(
        prefs.get("help_links")
    )
    button_colors = dict(DEFAULT_BUTTON_COLORS)
    button_colors.update(prefs.get("button_colors", {}) or {})
    prefs["button_colors"] = button_colors
    prefs.setdefault("custom_theme", dict(DEFAULT_THEME_DARK))
    retroarch_core_service.ensure_core_preferences(prefs)
    prefs.setdefault("templates_default", {})
    prefs.setdefault("emulator_paths", {})
    prefs.setdefault("custom_profiles", {})
    prefs.pop("profile_sort", None)


def _clean_custom_profiles(prefs: dict) -> None:
    custom_profiles = prefs.get("custom_profiles") or {}
    if not isinstance(custom_profiles, dict):
        prefs["custom_profiles"] = {}
        return

    cleaned_profiles = {}
    for name, profile_data in custom_profiles.items():
        if not isinstance(profile_data, dict):
            cleaned_profiles[name] = profile_data
            continue
        cleaned = dict(profile_data)
        cleaned.pop("export_root", None)
        cleaned_profiles[name] = cleaned
    prefs["custom_profiles"] = cleaned_profiles
