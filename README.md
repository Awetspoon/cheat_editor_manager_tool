# Cheat Editor Manager Tool

![Cheat Editor Manager Tool (Full Screen)](assets/app-fullscreen.png)

![Version](https://img.shields.io/badge/version-1.3.3-blue)
![Platform](https://img.shields.io/badge/platform-Windows-lightgrey)
![License](https://img.shields.io/badge/license-MIT-green)

Cheat Editor Manager Tool is a Windows desktop app for creating, editing, validating, and exporting cheat files to the correct folder layout for each emulator or modded console target.

## What This Program Does

- Loads existing cheat files and keeps editing focused on cheat text only
- Auto-detects IDs from known layouts when possible (for example Switch TID/BID, Citra, Dolphin, PPSSPP)
- Builds correct export paths automatically with **Quick Export**
- Shows live export preview before writing files
- Supports emulator path overrides and profile-based layouts
- Supports emulator custom profiles while keeping built-in targets stable

## Supported Targets

### Switch / CFW

- Atmosphere (Switch CFW)
- Yuzu
- Ryujinx
- Sudachi
- Suyu

### Emulator / Console Profiles

- Citra (3DS)
- RetroArch
- Dolphin
- PCSX2
- PPSSPP
- DuckStation
- Cemu
- Xenia
- RPCS3
- Nintendo 3DS (Luma)
- PSP (CFW)
- PS Vita (taiHEN)
- Wii (Homebrew)
- Wii U (CFW)

## How To Use

1. Select a profile (emulator/console target).
2. Load an existing cheat file or paste/edit cheat text.
3. Fill required IDs (TID/BID or profile ID field) when needed.
4. Use **Quick Export** to write files to the correct layout.
5. Use **Convert & Save** when you want manual filename/location control.

## Build (Windows)

```bash
python -m PyInstaller --clean --noconfirm cheat_editor_manager_tool.spec
```

Generated executable:

`dist/cheat_editor_manager_tool.exe`

## Download

Latest release:

`https://github.com/Awetspoon/cheat_editor_manager_tool/releases/latest`

## License

This project is licensed under the **MIT License**.
See [LICENSE](LICENSE).