"""Local override for PyInstaller's tkinter pre-find hook.

The default hook excludes tkinter when Tcl probing fails in build environments.
We keep tkinter importable and provide vendored Tcl/Tk data via spec/runtime hook.
"""


def pre_find_module_path(hook_api):
    # Intentionally keep default search paths untouched.
    return
