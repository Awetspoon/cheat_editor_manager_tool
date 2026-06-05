from __future__ import annotations

import os
import sys
from pathlib import Path


def _as_tcl_runtime_path(path: Path) -> str:
    resolved = str(path.resolve())
    if os.name != "nt":
        return resolved
    if resolved.startswith("\\\\?\\"):
        return resolved
    if resolved.startswith("\\\\"):
        return "\\\\?\\UNC\\" + resolved.lstrip("\\")
    return "\\\\?\\" + resolved


def configure_tcl_environment() -> None:
    if getattr(sys, "frozen", False):
        bundle_root = Path(getattr(sys, "_MEIPASS", ""))
        tcl_dir = bundle_root / "_tcl_data"
        tk_dir = bundle_root / "_tk_data"
    else:
        package_root = Path(__file__).resolve().parent
        repo_root = package_root.parent
        vendor_root = repo_root / "vendor" / "tcl"
        tcl_dir = vendor_root / "tcl8.6"
        tk_dir = vendor_root / "tk8.6"

    if not tcl_dir.exists() or not tk_dir.exists():
        return

    os.environ["TCL_LIBRARY"] = _as_tcl_runtime_path(tcl_dir)
    os.environ["TK_LIBRARY"] = _as_tcl_runtime_path(tk_dir)
