from __future__ import annotations

from typing import Optional

from .constants import DEFAULT_PROFILES
from .export_logic import profile_id_label


PROFILE_GROUP_CFW = "CFW / Homebrew"
PROFILE_GROUP_PC = "PC / Emulator"
PROFILE_GROUP_OTHER = "Custom / Other"
PROFILE_GROUP_ORDER = {
    PROFILE_GROUP_CFW: 0,
    PROFILE_GROUP_PC: 1,
    PROFILE_GROUP_OTHER: 2,
}


def get_profile_values(prefs: dict) -> list[str]:
    names = list(DEFAULT_PROFILES.keys())
    custom = list((prefs.get("custom_profiles") or {}).keys())
    for name in custom:
        if name not in names:
            names.append(name)
    return _grouped_profile_names(names)


def profile_target_group(profile_name: str) -> str:
    name = profile_name.casefold()
    if "cfw" in name or "homebrew" in name or name.startswith("atmosphere"):
        return PROFILE_GROUP_CFW
    if " - pc" in name or "retroarch" in name or "emulator" in name:
        return PROFILE_GROUP_PC
    return PROFILE_GROUP_OTHER


def _grouped_profile_names(names: list[str]) -> list[str]:
    indexed_names = list(enumerate(names))
    grouped = sorted(
        indexed_names,
        key=lambda item: (
            PROFILE_GROUP_ORDER[profile_target_group(item[1])],
            item[0],
        ),
    )
    return [name for _index, name in grouped]


def profile_group_label(profile_name: str) -> str:
    return profile_target_group(profile_name)


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
