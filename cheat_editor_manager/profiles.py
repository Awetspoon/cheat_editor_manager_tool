from __future__ import annotations

from typing import Optional

from .constants import DEFAULT_PROFILES
from .export_logic import profile_id_label


def get_profile_values(prefs: dict) -> list[str]:
    names = list(DEFAULT_PROFILES.keys())
    custom = list((prefs.get("custom_profiles") or {}).keys())
    for name in custom:
        if name not in names:
            names.append(name)
    mode = (prefs.get("profile_sort") or "default").lower()
    if mode in ("az", "a-z", "alphabetical", "alpha"):
        return sorted(names, key=lambda s: s.casefold())
    return names


def get_profile_info(prefs: dict, profile_name: str) -> dict:
    return (prefs.get("custom_profiles") or {}).get(profile_name) or DEFAULT_PROFILES.get(profile_name, {"kind": "generic"})


def is_atmosphere_profile(prefs: dict, profile_name: str, info: Optional[dict] = None) -> bool:
    info = info or get_profile_info(prefs, profile_name)
    subdir = (info.get("subdir") or "").replace("\\", "/").lower()
    return subdir.startswith("atmosphere/contents/")


def primary_extension(info: dict) -> str:
    exts = info.get("extensions") or []
    if not exts:
        return ".txt"
    ext = (exts[0] or ".txt").strip()
    if not ext:
        return ".txt"
    return ext if ext.startswith(".") else f".{ext}"


def uses_id_layout(info: dict) -> bool:
    return info.get("kind", "generic") in {"titleid", "idfile"}


def profile_id_field_label(info: dict) -> str:
    return f"{profile_id_label(info)}:"


def profile_id_hint(info: dict) -> str:
    return (info.get("titleid_hint") or info.get("id_hint") or "Use the ID this target expects.").strip()


def profile_template_path(prefs: dict, profile_name: str, info: dict, core_value: str = "") -> str:
    if is_atmosphere_profile(prefs, profile_name, info):
        return "SD:/atmosphere/contents/<TID>/cheats/<BID>.txt"

    kind = info.get("kind", "generic")
    ext = primary_extension(info)
    fixed_filename = (info.get("fixed_filename") or "").strip()
    subdir = (info.get("subdir") or "").strip().replace("\\", "/")

    if kind == "retroarch":
        core = (core_value or "").strip()
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
