from __future__ import annotations

import os
import sys
from pathlib import Path


def configure_tcl_environment() -> None:
    if getattr(sys, "frozen", False):
        return

    if os.environ.get("TCL_LIBRARY") and os.environ.get("TK_LIBRARY"):
        return
    package_root = Path(__file__).resolve().parent
    repo_root = package_root.parent
    vendor_root = repo_root / "vendor" / "tcl"
    tcl_dir = vendor_root / "tcl8.6"
    tk_dir = vendor_root / "tk8.6"
    if not tcl_dir.exists() or not tk_dir.exists():
        return

    # Absolute paths are more reliable than relative ones for Tk startup
    # (especially when launch context/cwd changes across tools/processes).
    tcl_value = str(tcl_dir.resolve())
    tk_value = str(tk_dir.resolve())

    os.environ["TCL_LIBRARY"] = tcl_value
    os.environ["TK_LIBRARY"] = tk_value
