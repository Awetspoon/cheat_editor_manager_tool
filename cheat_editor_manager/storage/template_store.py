from __future__ import annotations

from pathlib import Path
from typing import List

from ..constants import DEFAULT_PROFILES, TEMPLATES_DIR


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


def ensure_demo_templates() -> None:
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
