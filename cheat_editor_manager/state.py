from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class AppState:
    profile: str = ""
    export_root: str = ""
    title_id: str = ""
    build_ids: str = ""
    retroarch_core: str = ""
    wrap_enabled: bool = True
    theme_mode: str = "light"

    @classmethod
    def from_prefs(cls, prefs: dict) -> "AppState":
        return cls(
            export_root=str(prefs.get("export_root", "")),
            retroarch_core=str(prefs.get("retroarch_core", "")),
            wrap_enabled=bool(prefs.get("wrap", True)),
            theme_mode=str(prefs.get("mode", "light")),
        )
