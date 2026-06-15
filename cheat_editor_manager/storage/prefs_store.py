from __future__ import annotations

from collections.abc import Mapping
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
    "templates_default",
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
        saved_buttons = _dict_or_empty(raw_data.get("button_colors"))
        if (not saved_buttons) or saved_buttons == LEGACY_BUTTON_COLORS:
            prefs["button_colors"] = dict(DEFAULT_BUTTON_COLORS)
        prefs["branding_revision"] = 1

    if int(raw_data.get("branding_revision", 0) or 0) < 2:
        saved_buttons = _dict_or_empty(prefs.get("button_colors"))
        if (not saved_buttons) or saved_buttons == BRANDING_V1_BUTTON_COLORS:
            prefs["button_colors"] = dict(DEFAULT_BUTTON_COLORS)
        prefs["branding_revision"] = 2


def _ensure_pref_shapes(prefs: dict) -> None:
    if prefs.get("mode") not in ("dark", "light"):
        prefs["mode"] = DEFAULT_PREFS["mode"]

    prefs["help_links"] = help_link_service.merge_default_links(
        prefs.get("help_links")
    )

    button_colors = dict(DEFAULT_BUTTON_COLORS)
    for key, value in _dict_or_empty(prefs.get("button_colors")).items():
        if key in DEFAULT_BUTTON_COLORS:
            button_colors[key] = value
    prefs["button_colors"] = button_colors

    custom_theme = dict(DEFAULT_THEME_DARK)
    custom_theme.update(_dict_or_empty(prefs.get("custom_theme")))
    prefs["custom_theme"] = custom_theme

    retroarch_core_service.ensure_core_preferences(prefs)
    prefs["emulator_paths"] = _clean_string_map(prefs.get("emulator_paths"))
    prefs["custom_profiles"] = _dict_or_empty(prefs.get("custom_profiles"))
    prefs.pop("profile_sort", None)


def _clean_custom_profiles(prefs: dict) -> None:
    custom_profiles = _dict_or_empty(prefs.get("custom_profiles"))

    cleaned_profiles = {}
    for raw_name, profile_data in custom_profiles.items():
        name = str(raw_name or "").strip()
        if not name or not isinstance(profile_data, Mapping):
            continue
        cleaned = dict(profile_data)
        cleaned.pop("export_root", None)
        cleaned_profiles[name] = cleaned
    prefs["custom_profiles"] = cleaned_profiles


def _dict_or_empty(value) -> dict:
    return dict(value) if isinstance(value, Mapping) else {}


def _clean_string_map(value) -> dict[str, str]:
    cleaned = {}
    for key, item in _dict_or_empty(value).items():
        clean_key = str(key or "").strip()
        clean_value = str(item or "").strip()
        if clean_key and clean_value:
            cleaned[clean_key] = clean_value
    return cleaned
