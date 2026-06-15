# Cheat Editor Manager Tool

![Cheat Editor Manager Tool (Full Screen)](assets/app-fullscreen.png)

![Version](https://img.shields.io/badge/version-1.3.6-blue)
![Platform](https://img.shields.io/badge/platform-Windows-lightgrey)
![License](https://img.shields.io/badge/license-MIT-green)

Cheat Editor Manager Tool is a Windows desktop app for creating, editing, validating, and exporting cheat files to the correct folder layout for each emulator or modded console target.

## What The App Does

- Edits cheat text safely without mixing folder path logic into the editor
- Auto-detects IDs from known file layouts when possible (Switch TID/BID, Citra, Dolphin, PPSSPP, etc.)
- Builds correct target output structure automatically with **Quick Export**
- Shows live export path preview before writing files
- Supports emulator path overrides and profile-based export logic
- Supports emulator custom profiles while preserving built-in profile safety

## Purpose And Scope

The app exists to help users keep cheat text, required IDs, and emulator/CFW export folders in one clear desktop workflow.

In scope:

- Local Windows desktop editing, loading, validation, and export
- Built-in target profiles for common CFW and emulator layouts
- Custom emulator-only profiles for extra export rules
- Local preferences, templates, cheat source links, and export-root overrides
- Packaged Windows EXE builds through PyInstaller

Out of scope:

- Downloading cheats automatically
- Injecting cheats into games or consoles
- Online accounts, cloud sync, or API-key features
- Replacing emulator-specific cheat validation tools

## Finished App Requirements

- The app must start from both `python cheat_editor_manager_tool.py` and `python -m cheat_editor_manager`.
- Loading a known cheat file should fill supported IDs where the file layout makes that possible.
- Quick Export must write to the selected profile's expected folder and filename pattern.
- Convert & Save must stay available for manual save locations and file extensions.
- Settings must keep built-in CFW layouts safe while allowing custom emulator profiles and export-root overrides.
- User preferences and templates must stay local on the device.
- Tests must cover startup, storage, services, export logic, and key UI workflows.

## How The App Starts

The direct Windows entry point is:

```bash
python cheat_editor_manager_tool.py
```

The package entry point is:

```bash
python -m cheat_editor_manager
```

Both paths create `cheat_editor_manager.app.App` and start the Tkinter event loop. Startup calls `configure_tcl_environment()` before the UI imports Tk-heavy code, and `App` calls it again before creating the Tk root window so direct app construction is still safe.

## Core Brand Assets

- Primary logo: `assets/primary-logo.png`
- Secondary logo: `assets/secondary-logo.png`
- Wordmark (text-only): `assets/wordmark.png`
- Logomark (symbol-only): `assets/logomark.png`
- Runtime header mark: `assets/mark-48.png`
- App icon: `assets/app-icon.png` and `assets/app-icon.ico`
- Watermark: `assets/watermark-brand.png`

The runtime header intentionally uses one compact mark plus real text labels. Large wordmark/watermark images are retained as brand assets, but they are not used as duplicate top-left header branding.

See `assets/README.md` for the runtime-vs-brand-source asset inventory.

## Supported Targets

### Switch / CFW

- Atmosphere (Switch CFW)
- Yuzu
- Ryujinx
- Sudachi
- Suyu

### Emulator / CFW Profiles

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

The target selector uses two dropdowns: one for the group, such as CFW / Homebrew, PC / Emulator, or Custom Emulators, and one for the actual target profile. User-added emulator profiles stay separate from the hardcoded CFW layouts. The selected profile is still one real value internally, so export and helper logic receive the exact profile name they expect.

## Quick Start

1. Select the target group, then choose a profile such as Atmosphere, Ryujinx, PCSX2, or RetroArch.
2. Click **Load File** to open an existing cheat file, or paste cheat text into the editor.
3. When the loaded file comes from a known layout, the app reads IDs such as Switch TID/BID, Citra title IDs, Dolphin game IDs, or PCSX2 CRCs where possible.
4. If an ID cannot be detected automatically, fill the required TID/BID or profile ID fields manually.
5. Click **Quick Export** to write the cheat to the correct folder and filename layout.

## User Flow

1. Open the app.
2. Choose the target profile.
3. Load an existing cheat file or paste cheat text.
4. Check the Helper panel for required IDs and export preview.
5. Use Quick Export for the normal profile layout, or Convert & Save for manual control.
6. Adjust settings, templates, source links, or export roots only when needed.

## Screen Map

- Main window: profile controls, Helper panel, editor, and action bar.
- Settings: profiles, appearance, and export-root preferences.
- Templates: reusable saved cheat snippets, with an editable add-template dialog.
- Help Links: saved cheat source websites where users found codes or notes.
- RetroArch Cores: core folder selection for RetroArch exports.
- Extension picker: file type selection for Convert & Save.

## Feature List

- Load cheat files and paste cheat text
- Auto-detect supported profile IDs from known file paths
- Edit, undo, redo, clear, wrap, and save cheat text
- Preview export paths before writing files
- Quick Export to built-in and custom profile layouts
- Convert & Save to a manual location and extension
- Manage custom emulator profiles
- Manage appearance, editable templates, source links, RetroArch cores, and export roots

## Main UI Sections

- Header: app identity, mode toggle, Templates, Help Links, and Settings.
- Profile controls: target group selection, target profile selection, profile details, and export-root controls.
- Helper panel: profile-specific export rules, required ID fields, and live path preview.
- Help Links: opens saved cheat source websites in your browser; it does not download or inject cheats automatically.
- Cheat editor: main text editor with formatting helpers, undo/redo, clear, wrap, scrollbars, and optional drag-and-drop.
- Action bar: Load File, Quick Export, Convert & Save, and current status.
- Dialogs: Settings, Templates, Help Links source manager, RetroArch Cores, and Convert & Save extension selection.

## Documentation

- This README is the main product and developer guide.
- [assets/README.md](assets/README.md) explains runtime assets, retained brand-source files, and screenshot usage.

## Install For Local Development

Use Python 3.10 or newer.

```bash
python -m pip install -e ".[dev]"
```

To enable optional drag-and-drop file loading as well:

```bash
python -m pip install -e ".[dev,dnd]"
```

For the packaged build helper dependencies listed in `requirements.txt`:

```bash
python -m pip install -r requirements.txt
```

`tkinterdnd2` is optional. If it is not installed, the app still runs and uses the normal Load File button.

## Test

The current tests are standard `unittest` tests. They include pure logic tests, startup smoke tests for both entry points, and safe GUI workflow smoke tests for the main editor/export flow:

```bash
python -m unittest discover -s tests -q
```

The startup smoke tests launch the app with `CHEAT_EDITOR_MANAGER_SMOKE_EXIT=1`, so the Tk window is created, updated once, and closed automatically. To skip those GUI smoke tests in a constrained environment:

```bash
$env:CHEAT_EDITOR_MANAGER_SKIP_GUI_SMOKE = "1"
```

You can also check that all Python files compile:

```bash
python -m compileall -q assets/generate_brand_assets.py cheat_editor_manager tests hooks
```

## Build For Windows

```bash
python -m PyInstaller --clean --noconfirm cheat_editor_manager_tool.spec
```

Output executable:

`dist/cheat_editor_manager_tool.exe`

The PyInstaller build uses the custom Tk/Tcl hooks in `hooks/` and the bundled runtime script files in `vendor/tcl/`. Runtime startup normalises those Tcl/Tk paths for Windows before Tk is created.

## Project Structure

```text
cheat_editor_manager/
  app.py                  Main Tkinter app shell and compatibility wrappers
  app_actions.py          Thin file/export/RetroArch callback methods used by the UI
  bootstrap.py            Tcl/Tk runtime setup before the UI starts
  constants.py            Built-in defaults, themes, links, profiles, and paths
  export_logic.py         Pure export/path logic used by the UI and tests
  profiles.py             Profile helpers and validation
  resources.py            Packaged asset lookup helpers
  services/
    export_service.py     Export orchestration and user-facing export messages
    file_load_service.py  Cheat file loading and ID auto-detection
    help_link_service.py  Cheat source link cleanup and duplicate detection
    retroarch_core_service.py  RetroArch core cleanup and selection rules
    theme_service.py      Colour calculation and contrast helpers
  storage/
    prefs_store.py        Preferences loading/saving and stale-key cleanup
    template_store.py     Template loading, saving, deleting, and safe filenames
  ui/
    context_menu.py       Shared right-click editing menu
    style.py              Shared font and spacing tokens
    theme.py              Tk/ttk theme application for the main UI
    widgets.py            Shared Tk widgets
    panels/               Header, profile, helper, editor, and action-bar panels
    dialogs/              Settings, templates, help links, and core dialogs
      dialog_utils.py     Shared dialog shell, header, footer, and theme helpers
      extension_dialog.py Convert & Save extension picker
      settings_appearance_page.py  Theme and font settings page
      settings_export_roots_page.py  Built-in profile export-root overrides page
      settings_profiles_page.py  Custom profile management page
tests/                    Smoke, storage, profile, theme, help-link, RetroArch, and export tests
assets/                   App icons, logos, screenshots, and generated brand files
hooks/                    PyInstaller Tk/Tcl packaging hooks
vendor/tcl/               Vendored Tcl/Tk runtime files for packaged builds
MANIFEST.in               Source package include rules
pyproject.toml            Python package metadata and optional dependency groups
requirements.txt          Local build helper dependency list
```

## Maintenance Notes

- Keep UI construction in `cheat_editor_manager/ui/`; keep `app.py` focused on startup and wiring.
- Keep pure export rules in `export_logic.py` so they remain easy to test.
- Keep loading/saving in `cheat_editor_manager/storage/`.
- Keep user-facing orchestration in `cheat_editor_manager/services/`.
- Keep `app_actions.py` thin; real export, file-load, help-link, and RetroArch core work should stay in services.
- Split large dialogs by real sections, such as Settings pages, instead of rewriting the whole window at once.
- Add new emulator targets through profiles first, then add tests for the expected export path.

## Future Expansion Points

- Add emulator or CFW targets through `cheat_editor_manager/profiles.py`, then add export-path tests.
- Add new export rules in `cheat_editor_manager/export_logic.py` before wiring them into the UI.
- Keep file auto-detection changes in `services/file_load_service.py` covered by focused fixture tests.
- Keep new dialogs inside `cheat_editor_manager/ui/dialogs/` and share dialog chrome through `dialog_utils.py`.
- Keep new main-window sections inside `cheat_editor_manager/ui/panels/`.
- Keep new settings in `storage/prefs_store.py` with a safe default and migration/cleanup path.

## Known Limitations

- Running from source still requires a local Python install with Tkinter support, but the app now points Tk at the vendored Tcl/Tk scripts in `vendor/tcl/`.
- The packaged Windows executable includes the same Tcl/Tk script runtime and has a startup smoke mode for verification.
- Drag-and-drop support requires `tkinterdnd2`; if it is not installed, the app falls back to standard file loading.

## Download

Latest releases page:

`https://github.com/Awetspoon/cheat_editor_manager_tool/releases/latest`

## License

MIT License. See [LICENSE](LICENSE).
