from __future__ import annotations

from pathlib import Path

from ..constants import TEMPLATES_DIR

BLANK_TEMPLATE_NAME = "Blank"


def _safe_name(name: str, *, fallback: str) -> str:
    safe_name = "".join(ch for ch in name if ch not in r'\/:*?"<>|').strip()
    return safe_name or fallback


def _is_blank_template(name: str) -> bool:
    return str(name or "").strip().casefold() == BLANK_TEMPLATE_NAME.casefold()


def templates_dir() -> Path:
    d = TEMPLATES_DIR
    d.mkdir(parents=True, exist_ok=True)
    return d


def list_templates() -> list[str]:
    d = templates_dir()
    names = [
        p.stem for p in sorted(d.glob("*.txt")) if not _is_blank_template(p.stem)
    ]
    names.insert(0, BLANK_TEMPLATE_NAME)
    return names


def read_template(name: str) -> str:
    if _is_blank_template(name):
        return ""
    p = templates_dir() / f"{_safe_name(name, fallback='Untitled')}.txt"
    if p.exists():
        return p.read_text(encoding="utf-8", errors="replace")
    return ""


def write_template(name: str, content: str) -> None:
    if _is_blank_template(name):
        return
    p = templates_dir() / f"{_safe_name(name, fallback='Untitled')}.txt"
    p.write_text(content, encoding="utf-8")


def delete_template(name: str) -> bool:
    if _is_blank_template(name):
        return False
    p = templates_dir() / f"{_safe_name(name, fallback='Untitled')}.txt"
    if not p.exists():
        return False
    p.unlink()
    return True
