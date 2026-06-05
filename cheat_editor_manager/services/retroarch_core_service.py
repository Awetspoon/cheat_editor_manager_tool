from __future__ import annotations

import re
from collections.abc import Iterable, MutableMapping

from ..constants import DEFAULT_RETROARCH_CORES


DEFAULT_CORE_NAME = "Default (no subfolder)"


def normalize_core_name(value: str) -> str:
    """Return a comparable RetroArch core name."""
    normalized = (value or "").strip().casefold()
    normalized = re.sub(r"[-_]+", " ", normalized)
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return normalized


def normalize_core_list(cores: Iterable[str] | None) -> list[str]:
    """Return a de-duplicated RetroArch core list with the default entry first."""
    cleaned = [DEFAULT_CORE_NAME]
    seen = {DEFAULT_CORE_NAME.casefold()}

    for raw_core in cores or DEFAULT_RETROARCH_CORES:
        core = (raw_core or "").strip()
        if not core:
            continue
        key = core.casefold()
        if key in seen:
            continue
        seen.add(key)
        cleaned.append(core)

    return cleaned


def ensure_core_preferences(prefs: MutableMapping[str, object]) -> tuple[list[str], str]:
    """Normalize RetroArch core preferences and return the core list/current core."""
    cores = normalize_core_list(prefs.get("retroarch_cores"))
    prefs["retroarch_cores"] = cores

    current = str(prefs.get("retroarch_core") or "").strip()
    known = {core.casefold() for core in cores}
    if not current or current.casefold() not in known:
        current = DEFAULT_CORE_NAME

    prefs["retroarch_core"] = current
    return cores, current


def set_current_core(prefs: MutableMapping[str, object], core_name: str) -> str:
    cores, _current = ensure_core_preferences(prefs)
    wanted = (core_name or "").strip()
    known = {core.casefold() for core in cores}
    prefs["retroarch_core"] = wanted if wanted.casefold() in known else DEFAULT_CORE_NAME
    return str(prefs["retroarch_core"])


def add_core(prefs: MutableMapping[str, object], core_name: str) -> tuple[list[str], str]:
    cores, current = ensure_core_preferences(prefs)
    name = (core_name or "").strip()
    if not name:
        return cores, current

    if name.casefold() not in {core.casefold() for core in cores}:
        cores.append(name)
        prefs["retroarch_cores"] = cores

    return ensure_core_preferences(prefs)


def rename_core(
    prefs: MutableMapping[str, object],
    current_name: str,
    new_name: str,
) -> tuple[list[str], str]:
    current = (current_name or "").strip()
    new = (new_name or "").strip()
    if not current or not new or current.casefold() == DEFAULT_CORE_NAME.casefold():
        return ensure_core_preferences(prefs)

    cores, _selected = ensure_core_preferences(prefs)
    renamed = [new if core.casefold() == current.casefold() else core for core in cores]
    prefs["retroarch_cores"] = renamed

    if str(prefs.get("retroarch_core") or "").casefold() == current.casefold():
        prefs["retroarch_core"] = new

    return ensure_core_preferences(prefs)


def remove_core(
    prefs: MutableMapping[str, object],
    core_name: str,
) -> tuple[list[str], str]:
    name = (core_name or "").strip()
    if not name or name.casefold() == DEFAULT_CORE_NAME.casefold():
        return ensure_core_preferences(prefs)

    cores, _selected = ensure_core_preferences(prefs)
    prefs["retroarch_cores"] = [
        core for core in cores if core.casefold() != name.casefold()
    ]

    if str(prefs.get("retroarch_core") or "").casefold() == name.casefold():
        prefs["retroarch_core"] = DEFAULT_CORE_NAME

    return ensure_core_preferences(prefs)
