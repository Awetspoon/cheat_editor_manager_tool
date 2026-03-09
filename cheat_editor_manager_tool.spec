# -*- mode: python ; coding: utf-8 -*-

import os
from pathlib import Path

SPEC_DIR = Path(globals().get("SPECPATH", Path.cwd())).resolve()
os.chdir(SPEC_DIR)
os.environ["TCL_LIBRARY"] = "vendor/tcl/tcl8.6"
os.environ["TK_LIBRARY"] = "vendor/tcl/tk8.6"

ASSET_FILES = [
    "app-icon.ico",
    "icon-256.png",
    "mark-48.png",
    "logo-header.png",
    "logo-wide.png",
    "watermark-ui.png",
    "watermark.png",
]
ASSET_DATAS = [
    (str(SPEC_DIR / "assets" / name), "assets")
    for name in ASSET_FILES
    if (SPEC_DIR / "assets" / name).exists()
]
ICON_FILE = SPEC_DIR / "assets" / "app-icon.ico"


a = Analysis(
    ['cheat_editor_manager_tool.py'],
    pathex=[],
    binaries=[],
    datas=ASSET_DATAS,
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
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
    icon=str(ICON_FILE) if ICON_FILE.exists() else None,
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


