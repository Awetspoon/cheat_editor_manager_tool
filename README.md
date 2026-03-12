# Cheat Editor Manager Tool

![Cheat Editor Manager Tool](assets/logo-wide.png)

![App Full Screen](assets/app-fullscreen.png)

![Version](https://img.shields.io/badge/version-1.3.3-blue)
![Platform](https://img.shields.io/badge/platform-Windows-lightgrey)
![Python](https://img.shields.io/badge/python-3.9%2B-blue)

Retro-ready cheat editing and export for Switch, emulators, and modded console workflows.

## What It Does

- Edit cheat files safely in one place
- Auto-detect IDs where possible when loading files
- Build correct folder/file layouts for each target
- Preview export output before writing
- Support emulator-only custom profiles with validation

## Supported Targets

### PC Emulators

- Yuzu
- Ryujinx
- Sudachi
- Suyu
- Citra
- RetroArch
- Dolphin
- PCSX2
- PPSSPP
- DuckStation
- Cemu
- Xenia
- RPCS3

### CFW / Modded Console Targets

- Atmosphere (Switch)
- Nintendo 3DS (Luma)
- PSP (CFW)
- PS Vita (taiHEN)
- Wii (Homebrew)
- Wii U (CFW)

## Build

```bash
python -m PyInstaller --clean --noconfirm cheat_editor_manager_tool.spec
```

The Windows executable is generated at:

`dist/cheat_editor_manager_tool.exe`

## Release

Latest release tag: `v1.3.3`

Direct download (Windows EXE):

`https://github.com/Awetspoon/cheat_editor_manager_tool/releases/download/v1.3.3/cheat_editor_manager_tool.exe`

## License

MIT License. See `LICENSE`.