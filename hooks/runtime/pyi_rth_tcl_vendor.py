"""Runtime hook to set Tcl/Tk locations in onefile bundles."""

import os
import sys
from pathlib import Path


meipass = getattr(sys, "_MEIPASS", "")
if meipass:
    bundle_root = Path(meipass)
    tcl_dir = bundle_root / "_tcl_data"
    tk_dir = bundle_root / "_tk_data"
    if tcl_dir.is_dir():
        os.environ.setdefault("TCL_LIBRARY", str(tcl_dir))
    if tk_dir.is_dir():
        os.environ.setdefault("TK_LIBRARY", str(tk_dir))
