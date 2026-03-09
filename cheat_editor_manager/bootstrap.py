from __future__ import annotations

import os
import sys
from pathlib import Path


def configure_tcl_environment() -> None:
    if getattr(sys, "frozen", False):
        return

    package_root = Path(__file__).resolve().parent
    repo_root = package_root.parent
    vendor_root = repo_root / "vendor" / "tcl"
    tcl_dir = vendor_root / "tcl8.6"
    tk_dir = vendor_root / "tk8.6"
    if not tcl_dir.exists() or not tk_dir.exists():
        return

    try:
        cwd = Path.cwd()
        tcl_value = os.path.relpath(tcl_dir, cwd).replace("\\", "/")
        tk_value = os.path.relpath(tk_dir, cwd).replace("\\", "/")
    except Exception:
        tcl_value = str(tcl_dir)
        tk_value = str(tk_dir)

    os.environ["TCL_LIBRARY"] = tcl_value
    os.environ["TK_LIBRARY"] = tk_value
