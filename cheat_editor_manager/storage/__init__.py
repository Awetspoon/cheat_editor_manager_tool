from __future__ import annotations

from pathlib import Path

from ..constants import PREFS_FILE as DEFAULT_PREFS_FILE, TEMPLATES_DIR
from . import prefs_store as _prefs_store
from .template_store import ensure_demo_templates, list_templates, profile_templates_dir, read_template, write_template

PREFS_FILE = Path(DEFAULT_PREFS_FILE)

def load_prefs() -> dict:
    _prefs_store.PREFS_FILE = PREFS_FILE
    return _prefs_store.load_prefs()

def save_prefs(prefs: dict) -> None:
    _prefs_store.PREFS_FILE = PREFS_FILE
    _prefs_store.save_prefs(prefs)

__all__ = [
    "PREFS_FILE",
    "TEMPLATES_DIR",
    "ensure_demo_templates",
    "list_templates",
    "load_prefs",
    "profile_templates_dir",
    "read_template",
    "save_prefs",
    "write_template",
]
