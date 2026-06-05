from __future__ import annotations

import importlib.metadata
import importlib.util
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from cheat_editor_manager.bootstrap import configure_tcl_environment


REQUIRED_PACKAGES = {
    "Pillow": "PIL",
    "PyInstaller": "PyInstaller",
}

OPTIONAL_PACKAGES = {
    "pytest": ("pytest", "optional test runner"),
    "tkinterdnd2": ("tkinterdnd2", "optional drag-and-drop support"),
}


def package_version(distribution_name: str) -> str:
    try:
        return importlib.metadata.version(distribution_name)
    except importlib.metadata.PackageNotFoundError:
        return ""


def check_package(distribution_name: str, import_name: str, *, required: bool, note: str = "") -> bool:
    spec = importlib.util.find_spec(import_name)
    version = package_version(distribution_name)
    if spec is not None:
        suffix = f" {version}" if version else ""
        note_suffix = f" ({note})" if note else ""
        print(f"[OK] {distribution_name}{suffix} is importable as {import_name}.{note_suffix}")
        return True

    level = "FAIL" if required else "WARN"
    note_suffix = f" ({note})" if note else ""
    print(f"[{level}] {distribution_name} is not importable as {import_name}.{note_suffix}")
    return not required


def check_vendor_tcl_files() -> bool:
    tcl_init = REPO_ROOT / "vendor" / "tcl" / "tcl8.6" / "init.tcl"
    tk_init = REPO_ROOT / "vendor" / "tcl" / "tk8.6" / "tk.tcl"

    ok = True
    for label, path in (
        ("Vendored Tcl init", tcl_init),
        ("Vendored Tk init", tk_init),
    ):
        if path.exists():
            print(f"[OK] {label} found: {path}")
        else:
            print(f"[FAIL] {label} missing: {path}")
            ok = False
    return ok


def check_python_tk_dlls() -> bool:
    base = Path(sys.base_prefix)
    tcl_dll = base / "DLLs" / "tcl86t.dll"
    tk_dll = base / "DLLs" / "tk86t.dll"

    ok = True
    for label, path in (
        ("Python Tcl DLL", tcl_dll),
        ("Python Tk DLL", tk_dll),
    ):
        if path.exists():
            print(f"[OK] {label} found: {path}")
        else:
            print(f"[FAIL] {label} missing: {path}")
            ok = False
    return ok


def check_tk_startup() -> bool:
    try:
        configure_tcl_environment()
        import tkinter as tk

        root = tk.Tk()
        root.withdraw()
        root.destroy()
    except Exception as exc:
        print("[FAIL] tkinter.Tk() could not start.")
        print(f"       {type(exc).__name__}: {exc}")
        return False

    print("[OK] tkinter.Tk() started successfully with app bootstrap paths.")
    print(f"     TCL_LIBRARY={os.environ.get('TCL_LIBRARY', '')}")
    print(f"     TK_LIBRARY={os.environ.get('TK_LIBRARY', '')}")
    return True


def main() -> int:
    print("Cheat Editor Manager Tool - development environment check")
    print(f"Python executable: {sys.executable}")
    print(f"Python version: {sys.version.split()[0]}")
    print(f"Python base prefix: {sys.base_prefix}")
    print()

    ok = True
    for distribution_name, import_name in REQUIRED_PACKAGES.items():
        ok = check_package(distribution_name, import_name, required=True) and ok
    for distribution_name, (import_name, note) in OPTIONAL_PACKAGES.items():
        ok = check_package(distribution_name, import_name, required=False, note=note) and ok

    print()
    ok = check_vendor_tcl_files() and ok
    ok = check_python_tk_dlls() and ok
    ok = check_tk_startup() and ok

    print()
    if ok:
        print("Environment check passed.")
        return 0

    print("Environment check found problems.")
    print("Recommended fixes:")
    print("- Reinstall or repair Python if the Tcl/Tk DLLs are missing.")
    print("- Restore vendor/tcl if the vendored Tcl/Tk scripts are missing.")
    print("- Use a clean virtual environment after Python/Tk works.")
    print("- Install test/build tools with: python -m pip install -e \".[dev]\"")
    print("- Install optional drag-and-drop support with: python -m pip install -e \".[dnd]\"")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
