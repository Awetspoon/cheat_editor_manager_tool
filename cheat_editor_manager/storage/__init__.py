from __future__ import annotations

from pathlib import Path

from ..constants import PREFS_FILE as DEFAULT_PREFS_FILE, TEMPLATES_DIR
from . import prefs_store as _prefs_store
from .template_store import (
    delete_template,
    list_templates,
    read_template,
    templates_dir,
    write_template,
)

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
    "delete_template",
    "list_templates",
    "load_prefs",
    "read_template",
    "save_prefs",
    "templates_dir",
    "write_template",
]
