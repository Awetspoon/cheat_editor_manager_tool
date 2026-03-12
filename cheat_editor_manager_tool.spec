# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path


PROJECT_ROOT = Path.cwd()
HOOKS_ROOT = PROJECT_ROOT / "hooks"


a = Analysis(
    ['cheat_editor_manager_tool.py'],
    pathex=[str(PROJECT_ROOT)],
    binaries=[],
    datas=[
        (str(PROJECT_ROOT / "vendor" / "tcl" / "tcl8.6"), "_tcl_data"),
        (str(PROJECT_ROOT / "vendor" / "tcl" / "tk8.6"), "_tk_data"),
        (str(PROJECT_ROOT / "assets"), "assets"),
    ],
    hiddenimports=[
        'tkinter',
        'tkinter.font',
        'tkinter.ttk',
    ],
    hookspath=[str(HOOKS_ROOT)],
    hooksconfig={},
    runtime_hooks=[str(HOOKS_ROOT / "runtime" / "pyi_rth_tcl_vendor.py")],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='cheat_editor_manager_tool',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)


