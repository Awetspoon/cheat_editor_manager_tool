from __future__ import annotations

from ..export_logic import profile_id_label


def build_helper_snippet(info: dict) -> str:
    """Return a starter snippet that matches the selected profile type."""
    kind = info.get("kind", "generic")

    if kind == "switch":
        return (
            "# Switch helper\n"
            "# TitleID stays the same.\n"
            "# BuildID changes with updates.\n"
            "# You can enter multiple BIDs separated by commas.\n"
            "# Atmosphere path: atmosphere/contents/<TID>/cheats/<BID>.txt\n\n"
        )

    if kind in {"titleid", "idfile"}:
        snippet = (
            "# ID-based helper\n"
            f"# Use the {profile_id_label(info)} this target expects.\n"
            "# Quick Export builds the filename or plugin folder from that ID.\n"
        )
        if info.get("citra_enabled"):
            return snippet + "*citra_enabled\n\n"
        return snippet + "\n"

    if kind == "retroarch":
        return (
            "# RetroArch helper (multi-platform)\n"
            "# Path: RetroArch/cheats/<Core Name>/<Game>.cht\n"
            "# Pick your core in the Helper panel.\n\n"
        )

    return "# Helper snippet\n# Safe starting structure for this emulator.\n\n"
