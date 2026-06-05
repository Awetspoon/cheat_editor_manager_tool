"""Runtime hook to set Tcl/Tk locations in onefile bundles."""

import os
import sys
from pathlib import Path


def _as_tcl_runtime_path(path):
    resolved = str(path.resolve())
    if os.name != "nt":
        return resolved
    if resolved.startswith("\\\\?\\"):
        return resolved
    if resolved.startswith("\\\\"):
        return "\\\\?\\UNC\\" + resolved.lstrip("\\")
    return "\\\\?\\" + resolved


meipass = getattr(sys, "_MEIPASS", "")
if meipass:
    bundle_root = Path(meipass)
    tcl_dir = bundle_root / "_tcl_data"
    tk_dir = bundle_root / "_tk_data"
    if tcl_dir.is_dir():
        os.environ["TCL_LIBRARY"] = _as_tcl_runtime_path(tcl_dir)
    if tk_dir.is_dir():
        os.environ["TK_LIBRARY"] = _as_tcl_runtime_path(tk_dir)
