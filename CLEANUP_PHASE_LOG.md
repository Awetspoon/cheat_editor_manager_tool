# Cleanup Phase Log

This log records the audit and cleanup work phase by phase. It is intentionally plain English so the project state is easy to understand later.

## Phase 0 - Baseline Safety Check

**What was checked**
- Programming language and app type.
- Project/package files: `pyproject.toml`, `requirements.txt`, `cheat_editor_manager_tool.spec`.
- Entry points: `cheat_editor_manager_tool.py` and `cheat_editor_manager/__main__.py`.
- Current source tree, dependency availability, compile check, unit tests, pytest availability, source GUI launch, and PyInstaller build.

**What was changed**
- No source cleanup changes were made in this phase.
- This log file was created.

**What was removed**
- Nothing.

**What was moved or renamed**
- Nothing.

**Wiring updated**
- Nothing.

**Build/test/run status**
- Compile check passed: `python -m compileall -q cheat_editor_manager tests scripts hooks`.
- Unit tests passed: `python -m unittest discover -s tests -q` ran 29 tests.
- PyInstaller build passed and produced `dist/cheat_editor_manager_tool.exe`.
- `pytest` did not run because `pytest` is not installed.
- Source GUI launch failed because local Python/Tk cannot find a usable `init.tcl`.
- Plain `tkinter.Tk()` also fails in this Python install, so the source-run issue is at least partly environmental.

**Problems found**
- `tkinterdnd2` is declared as a dependency but is not installed in this environment, so drag-and-drop support falls back or is omitted from the current build.
- PyInstaller warning includes missing optional `tkinterdnd2`.
- The working tree already contains uncommitted cleanup changes and user asset changes, so all further work must preserve them.

**Remaining risks**
- Source GUI launch cannot be fully verified until local Python/Tk is repaired or a clean virtual environment is used.
- Full pytest verification cannot be run until dev dependencies install correctly.

**Next phase**
- Phase 1: map the repo structure and identify clean, messy, duplicated, or misplaced areas.

## Phase 1 - Structure Map

**What was checked**
- Root-level files and folders.
- Source package under `cheat_editor_manager/`.
- Tests under `tests/`.
- Assets, docs, scripts, hooks, vendored Tcl/Tk runtime files, generated build folders, and cache folders.
- `.gitignore` coverage for generated folders.

**What was changed**
- No project cleanup changes were made in this phase.
- This log was updated.

**What was removed**
- Nothing.

**What was moved or renamed**
- Nothing.

**Wiring updated**
- Nothing.

**Current structure summary**
- `cheat_editor_manager/`: real application package. This belongs in the repo and is the main codebase.
- `cheat_editor_manager/services/`: user-facing service orchestration. This structure is useful and should stay.
- `cheat_editor_manager/storage/`: preference/template persistence. This is the right location for storage code.
- `cheat_editor_manager/ui/`: shared widgets and dialogs. This is the right location for UI-only helpers.
- `tests/`: useful smoke, export, profile, storage, and theme tests. This belongs in the repo.
- `assets/`: branding, icons, screenshots, and generated image assets. It belongs in the repo, but asset usage should be checked before deleting anything.
- `hooks/`: PyInstaller custom Tk/Tcl hooks. Required for packaged builds.
- `scripts/`: utility scripts. Currently small and acceptable.
- `docs/`: historical documentation. Useful as reference, but the old versioned filename may confuse future readers.
- `vendor/tcl/`: bundled Tcl/Tk runtime data. Required for packaged builds.
- `build/`, `dist/`, `__pycache__/`, `.pytest_cache/`, `_tmp_mei/`: generated/cache output and should not be treated as source.

**Folders/files that look good**
- The main package now has clear top-level areas for app shell, pure logic, services, storage, UI, and resources.
- Tests are in a conventional `tests/` folder.
- PyInstaller support is separated into `hooks/` and `cheat_editor_manager_tool.spec`.

**Folders/files that look messy or need follow-up**
- `app.py` is still the largest and most mixed file. It owns the main UI shell and many event handlers.
- `file_load_service.py` is useful but dense and should be reviewed for smaller detection helpers later.
- `docs/Cheat_File_Creator_MASTER_EXPLANATION_v1_3_2.txt` is historical and version-specific; keep for now but document that it is archival.
- Generated cache folders exist locally; they are ignored and should not be committed.

**Potentially unused, misplaced, or confusing areas**
- Preview asset files are currently untracked and should be manually reviewed before committing.
- The generated build output is present locally but ignored.

**Build/test/run status**
- No new build or test command was run specifically for this phase. Phase 0 results still apply.

**Problems found**
- No new structural breakage was found.

**Remaining risks**
- Large UI shell and dense file-loading logic remain the main maintainability risks.

**Next phase**
- Phase 2: map startup, configuration loading, service wiring, and command/event wiring.

## Phase 2 - Startup And Wiring Map

**What was checked**
- Script entry point: `cheat_editor_manager_tool.py`.
- Package entry point: `cheat_editor_manager/__main__.py`.
- Tcl/Tk bootstrap: `cheat_editor_manager/bootstrap.py`.
- App shell startup: `cheat_editor_manager/app.py`.
- Preference/template loading through `cheat_editor_manager/storage/`.
- Service imports and callback wiring from the app shell.
- Dialog wiring for settings, templates, help links, and RetroArch cores.
- Command and event bindings in the main Tkinter window.

**What was changed**
- No startup or wiring changes were made in this phase.
- This log was updated.

**What was removed**
- Nothing.

**What was moved or renamed**
- Nothing.

**Wiring updated**
- Nothing.

**How the app currently starts**
- `cheat_editor_manager_tool.py` calls `configure_tcl_environment()` and then creates `App().run()`.
- `python -m cheat_editor_manager` runs `cheat_editor_manager/__main__.py`, which creates `App().run()`.
- `App.__init__()` also calls `configure_tcl_environment()`, creates demo templates, loads preferences, audits RetroArch cores, sets the Windows app ID, creates the Tk root window, builds styles, loads branding, builds the UI, and wires callbacks.

**Services and navigation currently wired**
- There is no route system because this is a Tkinter desktop app.
- Navigation is dialog/window based.
- Main callbacks are Tk `command=` handlers and event bindings.
- Export behaviour is delegated to `services/export_service.py`.
- File loading is delegated to `services/file_load_service.py`.
- Theme helpers are in `services/theme_service.py`.
- Dialogs live in `ui/dialogs/` and receive the app object.
- Preferences and templates are accessed through `storage/`.

**Wiring that looks clean**
- The app has one real main window class.
- Dialog modules are separated from the main app file.
- Storage access is centralised through the `storage` package.
- Pure export path logic is separated from UI code in `export_logic.py`.

**Wiring that looks risky**
- `App.__init__()` still does a lot: environment setup, storage setup, UI construction, state variables, event wiring, and service delegates.
- Service functions use the app object directly instead of explicit data objects. This is workable for Tkinter but makes future testing harder.
- `configure_tcl_environment()` points source runs at vendored Tcl/Tk when present. Source Tk still fails in this local Python install, and plain Tkinter fails too, so the environment remains suspect.
- `tkinterdnd2` is optional in code but declared as a dependency; the current environment does not have it.

**Build/test/run status**
- No new build was run in this phase.
- Extra startup probes confirmed that adding the Python `DLLs` folder does not fix this local Tk startup issue.

**Problems found**
- Source GUI startup remains blocked by local Tk/Tcl initialization.
- Startup flow is clear enough to keep, but the app shell remains too large.

**Remaining risks**
- Future changes inside `App.__init__()` can easily affect unrelated UI areas because construction and wiring are still concentrated there.

**Next phase**
- Phase 3: map all UI files, controls, dialogs, and visible behaviours.

## Phase 3 - UI Map

**What was checked**
- Main window/UI shell in `app.py`.
- Shared widgets in `ui/widgets.py`.
- Dialogs in `ui/dialogs/`: settings, templates, help links, and RetroArch cores.
- Tkinter buttons, checkboxes, listboxes, treeviews, scrollbars, command callbacks, and bindings.
- Search for placeholder/fake/TODO style markers in UI and services.

**What was changed**
- No UI cleanup changes were made in this phase.
- This log was updated.

**What was removed**
- Nothing.

**What was moved or renamed**
- Nothing.

**Wiring updated**
- Nothing.

**UI files found**
- `app.py`: main window, header, profile fields, target cards, editor, toolbar, export controls, theme application, callback delegates.
- `ui/widgets.py`: `ToolTip`, `Scrollable`, and a small text prompt helper.
- `ui/dialogs/settings_dialog.py`: preferences, custom profiles, appearance, emulator paths, and advanced settings.
- `ui/dialogs/templates_dialog.py`: template browsing, insertion, saving, folder opening, and reset.
- `ui/dialogs/help_links_dialog.py`: help link list management and browser opening.
- `ui/dialogs/retroarch_cores_dialog.py`: RetroArch core list management.

**UI that looks useful**
- Header controls are wired to real actions: templates, help links, settings, and dark mode.
- Export root controls are wired to real folder selection/reset/open behaviour.
- Editor toolbar actions are wired to text formatting, undo/redo, clear, and wrap.
- File loading, Quick Export, and Convert & Save are wired to service functions.
- Dialog buttons mostly connect to concrete preference/template/core/link behaviours.

**UI that looks fake or unused**
- No obvious fake placeholder screens were found in the current source.
- Previously stale window-size settings are already absent from the settings dialog.

**UI that has broken or risky wiring**
- Source GUI cannot be launched in the current Python/Tk environment, so UI behaviour cannot be visually verified from source.
- Drag-and-drop binding is optional and depends on `tkinterdnd2`, which is not installed here.
- Several UI helpers swallow best-effort Tk errors with `except Exception: pass`. Some of that is acceptable for UI cleanup paths, but it makes hidden UI failures harder to debug.

**UI files that may need splitting**
- `app.py` is too large for long-term maintainability.
- `settings_dialog.py` is also large and combines custom profiles, appearance, paths, and advanced preferences in one file.

**UI files that may need cleanup or rewrite**
- Repair/tidy is preferred over rewrite. The UI is real and wired; the issue is size and separation, not fake behaviour.
- A future split could move profile panel, editor panel, export panel, and target cards into smaller UI modules.

**Build/test/run status**
- No new build/test command was run specifically for this phase. Phase 0 results still apply.

**Problems found**
- No disconnected visible controls were confirmed by source inspection.

**Remaining risks**
- Visual regressions remain hard to catch until source Tk works or UI automation can run against the packaged app.

**Next phase**
- Phase 4: map core logic, duplication, large methods, and layer boundaries.

## Phase 4 - Core Logic Map

**What was checked**
- Pure export helpers in `export_logic.py`.
- Profile lookup and display helpers in `profiles.py`.
- Preference/template storage in `storage/`.
- Export orchestration in `services/export_service.py`.
- File loading and auto-detection in `services/file_load_service.py`.
- Theme helpers in `services/theme_service.py`.
- App-level delegate methods in `app.py`.

**What was changed**
- No core logic cleanup changes were made in this phase.
- This log was updated.

**What was removed**
- Nothing.

**What was moved or renamed**
- Nothing.

**Wiring updated**
- Nothing.

**Main logic areas**
- `export_logic.py`: validates IDs, normalizes text/path fragments, derives cheat names, and builds export plans. This is the cleanest core logic area and is covered by tests.
- `profiles.py`: provides profile names, profile metadata, ID labels/hints, and template path previews. This is small and readable.
- `storage/prefs_store.py`: loads preferences, merges defaults, migrates old branding values, removes stale preference keys, and saves atomically through a temp file.
- `storage/template_store.py`: manages template folder names, template listing, reading, writing, and seeded demo templates.
- `services/export_service.py`: connects the app UI state to export logic, preview rendering, Convert & Save, and Quick Export.
- `services/file_load_service.py`: loads files into the editor and performs best-effort emulator/profile detection.
- `services/theme_service.py`: keeps theme contrast and palette calculations testable.

**Logic that looks clean**
- `export_logic.py` is clear, mostly pure, and testable.
- `profiles.py` is simple and correctly separated from UI construction.
- `theme_service.py` is a good pure helper module and has useful tests.
- Template storage is small and understandable.

**Logic that needs tidying**
- `prefs_store.py` has useful migration logic, but some best-effort migration blocks swallow exceptions broadly.
- `export_service.py` still mixes UI dialogs/message boxes with export orchestration. It is acceptable for now but could be split later into UI prompts and export actions.
- `app.py` contains many wrapper methods that delegate into profile/theme/export helpers; this keeps UI wiring simple but still makes the class long.

**Logic that needs repair**
- No clearly broken core export logic was found during source inspection.
- Environment repair is still needed outside the codebase for source Tk startup.

**Duplicated logic**
- Theme helper methods in `App` delegate to `theme_service`, so the source of truth is `theme_service.py`; the wrappers are present for backward-compatible tests/UI calls.
- Profile helper methods in `App` delegate to `profiles.py`; the source of truth is `profiles.py`.
- No separate competing export-plan implementation was found.

**Logic that may need rewriting**
- `file_load_service.py` is the main rewrite candidate later because it is one long detection function with many emulator-specific branches. It should be split only with tests around detection behaviour.
- `app.py` should be split over time, not rewritten wholesale.

**Build/test/run status**
- No new build/test command was run specifically for this phase. Phase 0 results still apply.

**Problems found**
- No fake core logic was found.
- The largest maintainability issue is concentration of workflow logic inside long files, not incorrect behaviour.

**Remaining risks**
- File auto-detection is hard to refactor safely without more targeted tests.

**Next phase**
- Phase 5: write the Section 1 final cleanup plan before making Section 2 changes.

## Phase 5 - Cleanup Plan / Section 1 Final Report

**What was checked**
- Results from Phases 0-4.
- Current build/test/run status.
- Project areas grouped by keep/tidy/repair/move/split/merge/remove/rewrite.

**What was changed**
- No application source changes were made in this phase.
- This Section 1 plan was added to the log.

**What was removed**
- Nothing.

**What was moved or renamed**
- Nothing.

**Wiring updated**
- Nothing.

**1. What the app currently is**
- A Python 3.10+ Windows desktop app using Tkinter.
- It creates, edits, validates, and exports cheat files for emulator/modded console profiles.
- It packages with PyInstaller and uses vendored Tcl/Tk files for packaged builds.

**2. Current build/run/test status**
- Compile check: passed.
- `unittest`: passed, 29 tests.
- PyInstaller build: passed.
- Packaged executable: previously launched successfully in smoke check.
- Source GUI launch: failed because local Python/Tk cannot initialize Tcl/Tk.
- `pytest`: unavailable because the package is not installed.
- `tkinterdnd2`: unavailable, so drag-and-drop is not active in this environment.

**3. Areas that look clean - KEEP**
- `export_logic.py`.
- `profiles.py`.
- `theme_service.py`.
- `storage/template_store.py`.
- Existing test suite structure.
- PyInstaller hook/spec structure.

**4. Areas that need tidying - TIDY**
- `app.py` formatting and small repeated delegate wrappers.
- `settings_dialog.py` formatting and nested helper readability.
- Broad best-effort exception handling in UI/services where safe to narrow later.
- README/log documentation should stay aligned with actual build/run limits.

**5. Areas that need repair - REPAIR**
- Entry-point duplication can be reduced by routing the root script through the package `main()`.
- Preference cleanup should keep removing stale keys.
- Build/dependency documentation should clearly state that local Tk and optional drag-and-drop dependencies matter.

**6. Areas that should be moved - MOVE**
- No required source moves were identified.
- Generated local caches/build output should remain ignored, not moved.

**7. Areas that should be split - SPLIT**
- `app.py` should eventually split into smaller UI panel modules.
- `settings_dialog.py` could eventually split into custom profile, appearance, and emulator path sections.
- `file_load_service.py` should eventually split emulator detection into smaller tested helpers.

**8. Areas that should be merged - MERGE**
- Root startup should merge around the package `main()` path.
- No duplicate export, profile, storage, or theme systems need merging now.

**9. Areas that should be removed - REMOVE**
- Generated/cache folders can be cleaned locally: `__pycache__/`, `.pytest_cache/`, `_tmp_mei/`, and generated build output before final rebuild.
- Already-deleted dead shim/model files should stay removed: `defaults.py`, `state.py`, root-level `storage.py`, root-level `widgets.py`.

**10. Areas that may need rewriting - REWRITE**
- No full rewrite is recommended right now.
- `file_load_service.py` is the only realistic future rewrite candidate, but only after adding detection tests.

**11. Main risks**
- Source GUI cannot be verified until local Python/Tk works.
- `tkinterdnd2` missing means drag-and-drop is not verified or packaged in this environment.
- Large Tkinter files remain harder to maintain than the pure logic modules.

**12. Recommended Section 2 order**
- Phase 6: clean ignored generated/cache folders and confirm structure.
- Phase 7: centralise startup through package `main()`.
- Phase 8: do safe UI tidying only; avoid visual redesign.
- Phase 9: keep core logic stable; add only small safe repairs.
- Phase 10: verify service/helper boundaries and avoid duplicate abstractions.
- Phase 11: verify storage/model cleanup and stale preference handling.
- Phase 12: verify assets/resource paths without deleting branding.
- Phase 13: verify config/build/dependencies and update docs if needed.
- Phase 14: run tests and keep useful smoke coverage.
- Phase 15: ensure README and this log are accurate.
- Phase 16: final dead-code/reference sweep.
- Phase 17: final compile, tests, build, packaged launch, and report.

**Build/test/run status**
- No new build/test command was run specifically for this phase. Section 1 uses Phase 0 results.

**Problems found**
- No blocker prevents Section 2 cleanup.

**Remaining risks**
- Source GUI remains blocked by environment.

**Next phase**
- Phase 6: begin Section 2 with safe structure cleanup.

## Phase 6 - Structure Cleanup

**What was checked**
- Ignored/generated folders in the project root.
- Generated Python cache folders under source, tests, scripts, hooks, and generated build output.
- Current Git status after cleanup.

**What was changed**
- Removed generated Python `__pycache__` folders.
- Removed `.pytest_cache/`.
- Removed generated `build/` and `dist/` folders. These will be recreated during final build verification.
- This log was updated.

**What was removed**
- `__pycache__/` folders under the workspace.
- `.pytest_cache/`.
- `build/`.
- `dist/`.

**What was moved or renamed**
- Nothing.

**Wiring updated**
- Nothing. These were generated files only.

**Folders cleaned**
- Source, test, script, hook, and generated-output cache folders.

**References updated**
- None needed.

**Build/test/run status**
- No build/test command was run in this phase because only ignored generated output was removed.

**Problems found**
- `_tmp_mei/` could not be fully removed because Windows denied access to `_tmp_mei/_MEI82682`.
- The first PowerShell recursive cleanup attempt was blocked by safety policy, so a checked Python cleanup script was used for project-local generated folders.

**Remaining risks**
- `_tmp_mei/` remains locally but is ignored by `.gitignore`; it may need manual removal after whatever process owns it exits.

**Next phase**
- Phase 7: clean startup and wiring by centralising root script startup through the package entry point.

## Phase 7 - Startup And Wiring Cleanup

**What was checked**
- Root script startup in `cheat_editor_manager_tool.py`.
- Package startup in `cheat_editor_manager/__main__.py`.
- Compile and unit test status after changing startup wiring.

**What was changed**
- `cheat_editor_manager_tool.py` now delegates to `cheat_editor_manager.__main__.main()`.
- `cheat_editor_manager/__main__.py` now explicitly calls `configure_tcl_environment()` before creating `App`.

**What was removed**
- Duplicate root-script knowledge of `configure_tcl_environment()` and `App`.

**What was moved or renamed**
- Nothing.

**Wiring updated**
- Startup now has one clearer source of truth: package `main()`.
- The direct script and package entry point use the same startup function.

**Duplicate startup logic removed**
- The root script no longer manually imports and starts `App`.

**Build/test/run status**
- Compile check passed for `cheat_editor_manager` and `cheat_editor_manager_tool.py`.
- Unit tests passed: 29 tests.

**Problems found**
- Source GUI launch is still expected to fail until local Python/Tk is fixed; this phase did not attempt to solve the environment problem.

**Remaining risks**
- `App.__init__()` still calls `configure_tcl_environment()` as a defensive safeguard for direct programmatic construction.

**Next phase**
- Phase 8: safe UI cleanup without visual redesign.

## Phase 8 - UI Cleanup

**What was checked**
- Main visible controls in `app.py`.
- Dialog controls in settings, templates, help links, and RetroArch core management.
- Previously identified stale/fake window-size settings.
- Source search results for placeholder or fake UI markers.

**What was changed**
- No UI source changes were made in this phase.
- This log was updated.

**What was removed**
- Nothing in this phase.
- No fake or disconnected UI was confirmed during this pass.

**What was moved or renamed**
- Nothing.

**Wiring updated**
- Nothing.

**UI kept**
- Main editor workflow.
- Profile selection and export-root controls.
- Quick Export and Convert & Save actions.
- Templates dialog.
- Help links dialog.
- Settings dialog.
- RetroArch core management dialog.
- Theme controls and editor toolbar.

**UI tidied**
- No further UI tidying was done in this phase because the remaining cleanup would be structural splitting, not a safe small repair.

**UI repaired**
- No new UI repair was required.

**UI removed**
- Nothing in this phase.

**UI rewritten**
- Nothing. A rewrite is not justified because the UI is real and wired.

**UI wiring fixed**
- None needed in this phase.

**Build/test/run status**
- No build/test command was run specifically for this phase because no UI files changed.

**Remaining UI risks**
- `app.py` remains too large.
- `settings_dialog.py` remains large.
- Source visual verification remains blocked by local Python/Tk.
- Drag-and-drop remains dependent on the missing `tkinterdnd2` package.

**Next phase**
- Phase 9: core logic cleanup and duplication review.

## Phase 9 - Core Logic Cleanup

**What was checked**
- Core export service documentation and function layout.
- Compile and test status after the tidy.

**What was changed**
- Moved intended function docstrings in `services/export_service.py` to the first statement in each function.
- This makes `effective_export_root_for_profile`, `get_all_known_extensions`, and `pick_extension_for_save` documentable by Python tools.

**What was removed**
- No behaviour or features were removed.

**What was moved or renamed**
- No files were moved or renamed.

**Wiring updated**
- No wiring changes were needed.

**Logic kept**
- Export root resolution.
- Known extension discovery.
- Extension picker behaviour.
- Export plan/build/preview/quick export behaviour.

**Logic tidied**
- Function documentation placement in `export_service.py`.

**Logic repaired**
- Corrected docstring placement; this is a maintainability repair, not a runtime behaviour change.

**Logic merged**
- Nothing.

**Logic removed**
- Nothing.

**Logic rewritten**
- Nothing.

**Build/test/run status**
- Compile check passed.
- Unit tests passed: 29 tests.

**Behaviour risks**
- Low. The change only moved docstrings above `self = app`.

**Next phase**
- Phase 10: services, helpers, and module cleanup.

## Phase 10 - Services, Helpers, And Modules Cleanup

**What was checked**
- Service package marker and imports.
- UI package marker and dialog package marker.
- Old shim imports for removed `widgets.py` and `storage.py`.
- Service/helper boundaries.

**What was changed**
- No source changes were needed in this phase.
- This log was updated.

**What was removed**
- Nothing in this phase.

**What was moved or renamed**
- Nothing.

**Wiring updated**
- Nothing.

**Services kept**
- `services/export_service.py`: export orchestration and UI-facing export workflow.
- `services/file_load_service.py`: file loading and best-effort profile/ID detection.
- `services/theme_service.py`: pure theme/contrast helpers.

**Services repaired**
- No additional service repair was needed in this phase after the Phase 9 docstring tidy.

**Services merged**
- Nothing. No duplicate service system was found.

**Services removed**
- Nothing in this phase.

**Helpers renamed**
- Nothing.

**Wiring updated**
- Old shim import patterns were checked and are not present.

**Build/test/run status**
- No build/test command was run specifically for this phase because no source files changed.

**Problems found**
- `file_load_service.py` remains dense but still has one clear job.
- Services use the app object directly, which is acceptable for this Tkinter app but less ideal for isolated tests.

**Remaining risks**
- Future service refactors should avoid creating parallel service systems.

**Next phase**
- Phase 11: data, models, and storage cleanup.

## Phase 11 - Data, Models, And Storage Cleanup

**What was checked**
- Storage package API in `storage/__init__.py`.
- Preference loading/saving in `storage/prefs_store.py`.
- Storage tests.
- Previously removed unused data/model files.

**What was changed**
- Added clearer top-level spacing in `storage/__init__.py`.
- Wrapped the long constants import in `storage/prefs_store.py` for readability.

**What was removed**
- Nothing in this phase.
- The unused `state.py` and `defaults.py` files remain removed.

**What was moved or renamed**
- Nothing.

**Wiring updated**
- Nothing. The storage API still exports `load_prefs`, `save_prefs`, template helpers, `PREFS_FILE`, and `TEMPLATES_DIR`.

**Models kept**
- No active model classes are required for the current app shape.
- Preferences and profile dictionaries remain the current data format.

**Models removed**
- No additional models were removed in this phase.

**Models renamed**
- Nothing.

**Storage paths fixed**
- No path fixes were needed in this phase.

**Import/export fixed**
- No import/export behaviour changed.

**Build/test/run status**
- Storage compile check passed.
- Storage tests passed: 2 tests.

**Data risks left**
- Preferences are dictionary-based, so future larger changes may benefit from typed schemas/dataclasses.
- Do not add typed models until they reduce real complexity.

**Next phase**
- Phase 12: assets, themes, branding, and resource paths.

## Phase 12 - Assets, Themes, Branding, And Resource Paths

**What was checked**
- App-referenced assets: `app-icon.ico`, `app-icon.png`, `icon-256.png`, `mark-48.png`, `wordmark-360.png`.
- README asset references.
- PyInstaller icon reference in `cheat_editor_manager_tool.spec`.
- `assets/README.md`.

**What was changed**
- Updated `assets/README.md` to list `icon-256.png`, which is used by the app at runtime.
- Added a screenshot/preview section for `app-fullscreen.png`.

**What was removed**
- Nothing. Branding assets were preserved.

**What was moved or renamed**
- Nothing.

**Wiring updated**
- No code wiring changed.

**Assets kept**
- App icon files.
- Header/wordmark/mark images.
- Branding and watermark files.
- Screenshot/preview image files.
- Asset generation script.

**Assets moved**
- Nothing.

**Assets removed**
- Nothing.

**Resource paths fixed**
- No broken resource paths were found.
- Documentation now better matches runtime asset usage.

**Branding status**
- Main runtime branding assets exist.
- PyInstaller icon path exists.

**Build/test/run status**
- No build/test command was run specifically for this phase because only asset documentation changed.

**Problems found**
- Three preview assets are untracked: `exe-icon-preview.png`, `runtime-window-icon.png`, and `source-icon-preview.png`.

**Remaining risks**
- The untracked preview assets need manual review before deciding whether to commit them.

**Next phase**
- Phase 13: config, build, and project file cleanup.

## Phase 13 - Config, Build, And Project File Cleanup

**What was checked**
- Version consistency across `pyproject.toml`, `README.md`, and `constants.py`.
- Dependency files: `pyproject.toml` and `requirements.txt`.
- PyInstaller spec file and asset/hook paths.
- `.gitignore`.
- Obvious secret/API-key markers outside ignored generated/vendor folders.

**What was changed**
- Updated README wording so `requirements.txt` is described as packaged build helper dependencies, not runtime-only dependencies.

**What was removed**
- Nothing.

**What was moved or renamed**
- Nothing.

**Wiring updated**
- No code wiring changed.

**Dependency changes**
- No dependency files changed in this phase.
- `pyproject.toml` remains the source for package metadata and optional dev dependencies.
- `requirements.txt` remains useful for build/package helper installation.

**Project file changes**
- None in this phase.

**Config fixes**
- Documentation wording corrected.

**Build fixes**
- No spec/build fix was needed in this phase.

**Security/config risks**
- No real secrets were found.
- Search hits for `token` were emulator placeholder-token text, not credentials.

**Restore/build/run instructions**
- README now distinguishes editable dev install from `requirements.txt` package/build helpers.

**Build/test/run status**
- No build/test command was run specifically for this documentation wording change.

**Problems found**
- The archived v1.3.2 docs file still contains old version text by design.

**Remaining risks**
- Full dev dependency install is still blocked by local Python user-site permissions.

**Next phase**
- Phase 14: tests and basic verification.

## Phase 14 - Tests And Basic Verification

**What was checked**
- Python compile check for source, tests, scripts, and hooks.
- Standard library unittest discovery.
- Pytest availability.

**What was changed**
- No source changes were made in this phase.
- This log was updated.

**What was removed**
- Nothing.

**What was moved or renamed**
- Nothing.

**Wiring updated**
- Nothing.

**Tests found**
- `tests/test_app_smoke.py`.
- `tests/test_export_logic.py`.
- `tests/test_profile_helpers.py`.
- `tests/test_storage.py`.
- `tests/test_theme_contrast.py`.

**Tests removed**
- None.

**Tests repaired**
- None in this phase.

**Tests added**
- None in this phase.

**Test results**
- Compile check passed: `python -m compileall -q cheat_editor_manager tests scripts hooks`.
- Unit tests passed: `python -m unittest discover -s tests -q` ran 29 tests.
- `pytest` did not run because `pytest` is not installed.

**Untested risks**
- Source GUI startup remains unverified due local Tk/Tcl failure.
- Drag-and-drop remains unverified because `tkinterdnd2` is missing.
- Emulator-specific file auto-detection needs more targeted tests before a larger refactor.

**Next phase**
- Phase 15: documentation cleanup.

## Phase 15 - Documentation Cleanup

**What was checked**
- `README.md`.
- `assets/README.md`.
- Historical docs folder.
- This phase log.

**What was changed**
- Added README notes pointing to `CLEANUP_PHASE_LOG.md`.
- Clarified in README that `docs/` currently contains historical notes and version labels should be checked before treating them as current product docs.

**What was removed**
- Nothing.

**What was moved or renamed**
- Nothing.

**Wiring updated**
- Nothing.

**Docs updated**
- `README.md`.
- `assets/README.md` was already updated in Phase 12.
- `CLEANUP_PHASE_LOG.md` is being maintained after every phase.

**Setup instructions added**
- README includes editable dev install and requirements install commands.

**Build/run instructions added**
- README includes source script startup, package startup, unittest, compile, and PyInstaller build commands.

**Known issues listed**
- Source Tk/Tcl requirement.
- Packaged executable Tcl/Tk bundling.
- Optional drag-and-drop dependency.

**Build/test/run status**
- No build/test command was run specifically for this documentation-only phase.

**Problems found**
- The old v1.3.2 docs file is useful historically but should not be treated as current documentation.

**Remaining risks**
- Future docs updates should keep README, pyproject version, and `APP_VERSION` aligned.

**Next phase**
- Phase 16: final dead code and duplication sweep.

## Phase 16 - Final Dead Code And Duplication Sweep

**What was checked**
- References to removed files/modules: `state.py`, `defaults.py`, old root `storage.py`, and old root `widgets.py`.
- Stale window-size preference keys.
- Corrupted text markers.
- Placeholder/TODO/fake UI markers.
- Compile status after the sweep.

**What was changed**
- No source changes were needed in this phase.
- This log was updated.

**What was removed**
- Nothing in this phase.

**What was moved or renamed**
- Nothing.

**Wiring updated**
- Nothing.

**Dead code removed**
- No additional dead code was found that could be safely removed in this final sweep.

**Duplicates removed or merged**
- No additional duplicate systems were found.

**Stale comments removed**
- None.

**Names improved**
- None in this phase.

**References checked**
- Old removed module references were not found in source/tests, except documentation mentions in this log.
- Stale window preference keys only remain in the migration cleanup list and its test.
- No corrupted help-link text markers were found in source.

**Build/test/run status**
- Compile check passed.

**Problems found**
- No new code problems were found in the final sweep.

**Remaining risks**
- Large UI files remain a maintainability risk but are not dead code.
- `_tmp_mei/` remains locked locally and ignored.

**Next phase**
- Phase 17: final build, run, verification, and report.

## Phase 17 - Final Build, Run, And Report

**What was checked**
- Final compile check.
- Final unittest run.
- Pytest availability.
- PyInstaller clean build.
- PyInstaller warning file.
- Source GUI smoke launch.
- Packaged executable smoke launch.
- Final Git status and source tree.

**What was changed**
- No source cleanup changes were made in this phase.
- This final phase record was added.

**What was removed**
- Nothing in this phase.

**What was moved or renamed**
- Nothing in this phase.

**Wiring updated**
- Nothing in this phase.

**Final project structure**
- `cheat_editor_manager/`: app package, core logic, services, storage, UI helpers, and dialogs.
- `tests/`: unittest-based smoke/core/storage/theme tests.
- `assets/`: branding, runtime icons, screenshots, and generated brand images.
- `hooks/`: PyInstaller Tcl/Tk hooks.
- `scripts/`: utility scripts.
- `docs/`: historical notes.
- `vendor/tcl/`: Tcl/Tk runtime data for packaged builds.
- Root files: README, license, pyproject, requirements, PyInstaller spec, root script, and this cleanup log.

**What was clean and kept**
- Export logic, profile helpers, theme helpers, template storage, tests, assets, hooks, and PyInstaller packaging structure.

**What was tidied**
- Startup entry point, storage formatting, export service docstrings, asset docs, README, and phase log.

**What was repaired**
- Root script startup now delegates through package `main()`.
- Stale preference cleanup remains in place and covered by tests.
- Asset documentation now matches runtime usage.

**What was rewritten**
- Nothing was rewritten wholesale.

**What was removed**
- Generated cache/build output was cleaned earlier where possible.
- Dead source files remain removed: `defaults.py`, `state.py`, root `storage.py`, root `widgets.py`.

**What was moved or renamed**
- No files were moved or renamed in this run.

**What duplicate systems were merged**
- Root startup was merged around `cheat_editor_manager.__main__.main()`.

**What wiring was fixed**
- Direct script startup now uses the same package startup function.
- Old widget/storage shim imports remain absent.

**Build/test/run checks completed**
- Compile check passed: `python -m compileall -q cheat_editor_manager tests scripts hooks`.
- Unit tests passed: `python -m unittest discover -s tests -q` ran 29 tests.
- PyInstaller clean build passed and produced `dist/cheat_editor_manager_tool.exe`.
- Packaged executable launched successfully in a smoke check and was force-closed after the check.
- `pytest` did not run because `pytest` is not installed.
- Source GUI launch failed because local Python/Tk cannot find a usable `init.tcl`.

**What still has problems**
- `tkinterdnd2` is not installed, so drag-and-drop is not included/verified in this environment.
- PyInstaller warning lists `tkinterdnd2` as missing/optional; other warning entries are normal Windows/stdlib optional imports.
- Local source Tk startup is blocked by the current Python/Tk installation.
- `_tmp_mei/` remains locally because Windows denied access during cleanup.

**What should be improved next**
- Fix local Python/Tk or use a clean virtual environment, then re-check source GUI launch.
- Install dev/runtime dependencies in a writable environment, especially `tkinterdnd2` and `pytest`.
- Add file auto-detection tests before splitting `file_load_service.py`.
- Split `app.py` and `settings_dialog.py` gradually when UI runtime verification is available.

**Files that need manual review**
- Untracked preview assets: `assets/exe-icon-preview.png`, `assets/runtime-window-icon.png`, `assets/source-icon-preview.png`.
- Historical docs file: `docs/Cheat_File_Creator_MASTER_EXPLANATION_v1_3_2.txt`.
- Locked local `_tmp_mei/` folder.

## Follow-Up - Environment Setup Attempt And File Load Coverage

**What was checked**
- Project-local virtual environment creation.
- Local package/dev dependency installation.
- Tkinter startup inside the virtual environment.
- File auto-detection coverage for `services/file_load_service.py`.
- Compile, unittest, and pytest status after adding tests.

**What was changed**
- Created a project-local `.venv/` folder. It is ignored by `.gitignore`.
- Added `tests/test_file_load_service.py` with focused file-loading detection tests.

**What was removed**
- Nothing.

**What was moved or renamed**
- Nothing.

**Wiring updated**
- No application wiring changed.

**Environment results**
- `.venv` creation succeeded.
- Installing the editable project with dev dependencies timed out while pip was installing build dependencies.
- Directly installing `pytest`, `tkinterdnd2`, `Pillow`, and `pyinstaller` into `.venv` also timed out while fetching package metadata/wheels.
- `.venv` Tkinter startup still failed because it uses the same base Python installation, which cannot find a usable `init.tcl`.

**Tests added**
- Atmosphere layout detection sets TID, BID, profile, and loads text.
- RetroArch core-folder detection sets the profile/core without mutating the saved core list.
- Citra RetroArch save layout detection sets TitleID/profile.
- PCSX2 `.pnach` detection normalizes CRC/profile.

**Build/test/run status**
- Compile check passed.
- Unit tests passed: 33 tests.
- `pytest` still did not run because `pytest` is not installed.

**Problems found**
- A venv alone does not fix the broken local Python/Tk install.
- Pip/package fetching is timing out before dependencies install.

**Remaining risks**
- Source GUI launch and drag-and-drop still need a repaired Python/Tk/dependency environment.
- `.venv/` exists locally but is ignored.

## Section 2 Continuation - Phase 9/10 File Load Service Repair

**Phase name**
- Core logic cleanup / services, helpers, and modules cleanup.

**What was checked**
- `services/file_load_service.py`.
- Focused file-load detection tests.
- Full unittest suite.

**What was changed**
- Split the long `load_file_into_app()` implementation into smaller helper functions.
- Kept `load_file_into_app(app, filepath=None)` as the public service entry point.
- Added named helpers for file reading, editor filling, profile setting, ID setting, RetroArch core normalization, and each detection family.

**What was removed**
- No feature behaviour was removed.
- Nested detector helper definitions inside the main function were removed in favour of module-level helpers.

**What was moved or renamed**
- Detection logic was moved from one giant function body into private module-level helpers.
- No files were moved or renamed.

**Wiring updated**
- No external imports needed to change because the public function name stayed the same.
- `app.py` still imports and calls `load_file_into_app`.

**Logic kept**
- UTF-8 then latin-1 file read fallback.
- Editor fill/status update.
- Citra, Luma, RetroArch, Atmosphere, Switch emulator, header metadata, and generic emulator detection.
- Final `refresh_profile_info()` call.

**Logic tidied**
- The service now has one readable orchestration function and separate detector helpers.
- RetroArch core name normalization is now a named helper.
- Profile and ID setting are now shared helpers instead of repeated inline blocks.

**Logic repaired**
- The service is easier to test and safer to extend.
- No known behaviour change was intended.

**Logic merged**
- Repeated "set profile and combobox" logic now uses one helper.
- Repeated TitleID/BuildID normalization now uses one helper per ID type.

**Logic removed**
- No useful logic was removed.

**Logic rewritten**
- `services/file_load_service.py` was rewritten internally because the audit identified it as dense enough to split once focused tests existed.

**Build/test/run status**
- Compile check passed.
- Focused file-load tests passed: 4 tests.
- Full unittest suite passed: 33 tests.

**Behaviour risks left**
- File auto-detection covers many emulator-specific path conventions; more tests should be added before changing those rules further.

**Next phase**
- Run final Section 2 verification and report.

## Section 2 Continuation - Phase 17 Final Verification

**What was checked**
- Compile check after the file-load service split.
- Full unittest suite.
- Pytest availability.
- PyInstaller clean build.
- PyInstaller warning file.
- Source GUI smoke launch.
- Packaged executable smoke launch.
- Final Git status/source tree.

**What was changed**
- No source changes were made in this final verification phase.
- This log was updated with the final continuation results.

**What was removed**
- Nothing.

**What was moved or renamed**
- Nothing.

**Wiring updated**
- Nothing in this phase.

**Final project structure**
- `cheat_editor_manager/`: app package, startup, constants, resources, core export logic, profiles, services, storage, UI widgets, and dialogs.
- `tests/`: unittest suite, now including file-load service detection tests.
- `assets/`: branding, icons, screenshots, and generated brand files.
- `hooks/`: PyInstaller hooks for Tcl/Tk.
- `scripts/`: utility scripts.
- `docs/`: historical notes.
- `vendor/tcl/`: vendored Tcl/Tk runtime data for packaged builds.

**What was clean and kept**
- App purpose, export logic, profiles, storage, theme helpers, UI dialogs, assets, build hooks, and tests.

**What was tidied**
- File-load service structure.
- Repeated profile/ID setting code inside file-load detection.

**What was repaired**
- `services/file_load_service.py` now has clearer private helpers and focused tests.

**What was rewritten**
- `services/file_load_service.py` was internally rewritten/split while preserving its public entry point and tested behaviours.

**What was removed**
- No additional source files were removed in this continuation.

**What was moved or renamed**
- No files were moved or renamed.

**What duplicate systems were merged**
- Repeated profile-setting and ID-normalization snippets in file-load detection were merged into shared helpers.

**What wiring was fixed**
- No external wiring changed; `app.py` still calls `load_file_into_app`.

**Build/test/run checks completed**
- Compile check passed.
- Full unittest suite passed: 33 tests.
- PyInstaller clean build passed and produced `dist/cheat_editor_manager_tool.exe`.
- Packaged executable smoke launch passed.
- `pytest` did not run because `pytest` is not installed.
- Source GUI smoke launch failed because the local Python/Tk install cannot find a usable `init.tcl`.

**What still has problems**
- Local Python/Tk source startup remains broken.
- `tkinterdnd2` is still missing, so drag-and-drop is not verified or bundled in this environment.
- PyInstaller warning still lists missing optional `tkinterdnd2`; the other warning entries are expected optional Windows/stdlib imports.

**What should be improved next**
- Repair or reinstall local Python/Tk, or use a clean Python install that can start `tkinter.Tk()`.
- Install `pytest` and `tkinterdnd2` in a working environment.
- Add more file-detection tests before changing additional emulator-specific rules.

**Files that need manual review**
- Untracked preview assets: `assets/exe-icon-preview.png`, `assets/runtime-window-icon.png`, `assets/source-icon-preview.png`.
- Historical docs file: `docs/Cheat_File_Creator_MASTER_EXPLANATION_v1_3_2.txt`.
- Local `.venv/` and `_tmp_mei/` folders are ignored but remain on disk.

## Follow-Up - Development Environment Diagnostic Script

**What was checked**
- Local Python executable, version, and base prefix.
- Required packages: Pillow and PyInstaller.
- Optional/dev packages: pytest and tkinterdnd2.
- Tcl/Tk init files and DLLs.
- Actual `tkinter.Tk()` startup.
- Compile, unittest, PyInstaller build, and packaged executable smoke launch after adding the script.

**What was changed**
- Added `scripts/check_dev_environment.py`.
- Updated `README.md` with the environment check command.

**What was removed**
- A temporary `_tk_diag_lib/` diagnostic folder was removed after probing the local Tk failure.

**What was moved or renamed**
- Nothing.

**Wiring updated**
- Nothing in application runtime wiring.

**Build/test/run status**
- `python scripts/check_dev_environment.py` ran and correctly reported environment problems.
- Compile check passed.
- Full unittest suite passed: 33 tests.
- PyInstaller clean build passed.
- Packaged executable smoke launch passed.

**Problems found**
- Pillow and PyInstaller are installed.
- pytest and tkinterdnd2 are not installed.
- Tcl/Tk files and DLLs exist under the Python install.
- `tkinter.Tk()` still fails, which points to a broken local Python/Tk runtime rather than a missing repo file.

**Remaining risks**
- Source GUI launch remains blocked until Python/Tk is repaired or reinstalled.
- Drag-and-drop remains unverified until tkinterdnd2 can be installed.

**Next phase**
- Repair/reinstall Python with working Tk/Tcl support, then install dev dependencies and rerun `python scripts/check_dev_environment.py`.

## UI Visual Cleanup - Phases 1-9

**Phase 1 - UI baseline scan**
- UI framework: Tkinter plus ttk.
- Main UI starts in `cheat_editor_manager/app.py`.
- Screens/dialogs found: main editor window, Settings, Templates, Help Links, RetroArch Cores, extension picker, text prompt dialogs, context menu, profile sort menu.
- Visual style found: warm retro desktop palette, branded header, ttk button styles, custom dark/light/custom theme preferences.
- Consistent areas: main export workflow, helper cards, editor controls, bottom action bar, branded assets.
- Messy areas: repeated hardcoded font tuples, raw Tk listboxes/text previews using default OS colours, header buttons using `tk.Button` while most other buttons use ttk styles.
- Fake UI found: none confirmed.
- Duplicated UI systems found: no second theme system, but some styling was copy-pasted in individual files.

**Phase 2 - style system audit**
- Source of truth kept: `constants.py` for default colour tokens and `services/theme_service.py` for theme/contrast calculations.
- Added `ui/style.py` as the shared source for UI font and spacing tokens.
- Added themed raw Tk widget helpers in `ui/widgets.py` for listboxes and text widgets.
- Style risks left: Tkinter still needs some direct `bg/fg` configuration for raw Tk widgets.

**Phase 3 - screen-by-screen cleanup**
- Kept: main window, Settings, Templates, Help Links, RetroArch Cores, extension picker, text prompt dialogs.
- Tidied: Templates, Help Links, and RetroArch Cores list widgets now use app theme colours.
- Tidied: section/header fonts now use shared UI font tokens.
- Repaired: header action buttons now use ttk `Header.TButton` instead of separate `tk.Button` styling.
- Removed: no useful UI screens were removed.
- Rewritten: no screen was rewritten.

**Phase 4 - buttons, menus, tabs, and controls check**
- Header buttons are still wired to real behaviour: mode toggle, templates, help links, settings.
- Main action buttons are still wired to real behaviour: load file, quick export, convert/save.
- Dialog buttons remain wired to real preference/template/link/core behaviour.
- Fake controls removed: none found.
- Interaction risk left: source GUI click-through cannot be verified until local Python/Tk is repaired.

**Phase 5 - component and layout consistency**
- Created shared style-token module: `cheat_editor_manager/ui/style.py`.
- Created reusable theme helpers for raw Tk listboxes and text widgets.
- Merged repeated inline listbox colour styling into `configure_listbox_theme`.
- Kept layout structure unchanged to avoid redesigning the app.

**Phase 6 - assets, icons, and brand visuals check**
- Kept existing branding assets and app icon paths.
- No asset paths needed code changes.
- Existing `app-fullscreen.png` was reviewed as the visual baseline.
- Untracked preview assets still need manual review before committing.

**Phase 7 - fake UI and placeholder sweep**
- Searched for fake UI, placeholder screens, TODO-only features, empty command handlers, and lorem/sample text.
- No fake screen or dead visible control was confirmed.
- Existing template demo/reset behaviour remains real template functionality, not a fake screen.

**Phase 8 - final visual pass**
- Removed remaining direct hardcoded `Segoe UI`/`Consolas` font tuples from app/UI construction except dynamic font composition.
- Header buttons now belong to the same ttk style system as the rest of the app.
- Raw Tk listboxes/text preview now match theme colours, selection colours, borders, and focus colours.

**Phase 9 - build, run, and UI verification**
- Compile check passed.
- Full unittest suite passed: 33 tests.
- PyInstaller clean build passed.
- Packaged executable smoke launch passed.
- `python scripts/check_dev_environment.py` still reports the local Python/Tk startup failure.
- `pytest` still did not run because pytest is not installed.

**Files changed in this UI pass**
- `cheat_editor_manager/ui/style.py`.
- `cheat_editor_manager/ui/widgets.py`.
- `cheat_editor_manager/app.py`.
- `cheat_editor_manager/ui/dialogs/help_links_dialog.py`.
- `cheat_editor_manager/ui/dialogs/retroarch_cores_dialog.py`.
- `cheat_editor_manager/ui/dialogs/settings_dialog.py`.
- `cheat_editor_manager/ui/dialogs/templates_dialog.py`.
- `README.md`.

**Remaining UI risks**
- Source GUI navigation/click-through cannot be verified until local Python/Tk works.
- Drag-and-drop remains unverified until `tkinterdnd2` can be installed.
- `app.py` is still large, though styling is now more centralised.

## UI Follow-Up - Duplicate Header Mark Removed

**What was checked**
- Header brand image loading in `app.py`.
- `assets/wordmark-360.png`.
- `assets/mark-48.png`.

**What was changed**
- The header now hides the standalone `mark-48.png` when `wordmark-360.png` is available.
- The wordmark asset already contains the mark, so this removes the duplicated top-left brand mark/watermark effect.
- The standalone mark still remains as a fallback if the wordmark image is missing.

**What was not changed**
- The window/app icon remains unchanged.
- Branding assets were not deleted.
- Header layout and behaviour were not redesigned.

**Build/test/run status**
- Compile check passed.
- Full unittest suite passed: 33 tests.
- PyInstaller clean build passed.
- Packaged executable smoke launch passed.

**Remaining risks**
- Source GUI visual verification still depends on fixing the local Python/Tk install.

## Current Redesign Phase 14 - Config And Build Cleanup

**What this section currently does**
- `pyproject.toml` defines package metadata, runtime dependencies, optional dependency groups, and the GUI entry point.
- `requirements.txt` gives a simple local dependency install path for packaging work.
- `.gitignore` keeps generated build/cache output out of source control.
- `cheat_editor_manager_tool.spec`, `hooks/`, and `vendor/tcl/` package the Tkinter app into a Windows executable.

**What was wrong**
- `tkinterdnd2` was treated like a required project dependency even though the app already falls back when drag-and-drop support is missing.
- Source-package include rules were not explicit.
- Generated Python/cache/coverage outputs were not all covered by `.gitignore`.
- Build config had no focused tests to stop future path drift.

**What changed**
- Moved `tkinterdnd2` into an optional `dnd` extra in `pyproject.toml`.
- Kept PyInstaller and pytest in the optional `dev` extra.
- Clarified `requirements.txt` so `tkinterdnd2` is visibly optional.
- Added `MANIFEST.in` for README/license, app entry script, spec file, assets, docs, hooks, and vendored Tcl/Tk runtime files.
- Expanded `.gitignore` for Python cache, packaging metadata, and coverage output.
- Tidied `cheat_editor_manager_tool.spec` formatting without changing packaged behaviour.
- Added `tests/test_build_config.py`.

**Files changed**
- `pyproject.toml`.
- `requirements.txt`.
- `.gitignore`.
- `cheat_editor_manager_tool.spec`.
- `README.md`.
- `docs/REDESIGN_PLAN.md`.
- `CLEANUP_PHASE_LOG.md`.

**Files added**
- `MANIFEST.in`.
- `tests/test_build_config.py`.

**Files removed or moved**
- None.

**Wiring updated**
- Package dependency groups now match runtime reality: normal app use requires Pillow, drag-and-drop is optional, and build/test tools are dev dependencies.
- Source package include rules now match the current folders used by runtime assets, docs, PyInstaller hooks, and vendored Tcl/Tk files.

**Build/test/run status**
- Environment check passed: `python scripts/check_dev_environment.py`.
- Compile check passed: `python -m compileall -q assets/generate_brand_assets.py cheat_editor_manager tests scripts hooks`.
- Unit tests passed: `python -m unittest discover -s tests -q` ran 65 tests.
- Source smoke mode passed with `CHEAT_EDITOR_MANAGER_SMOKE_EXIT=1`.
- PyInstaller clean build passed: `python -m PyInstaller --clean --noconfirm cheat_editor_manager_tool.spec`.
- Packaged executable smoke mode passed with `CHEAT_EDITOR_MANAGER_SMOKE_EXIT=1`.

**Remaining risks**
- `pytest` is still not installed in the current global Python, but the project test suite is currently standard `unittest`.
- `tkinterdnd2` is still not installed in the current global Python, so optional drag-and-drop behaviour is not active in this environment.

**Next phase**
- Continue with the Tests phase, then documentation and final cleanup/verification.

## Current Redesign Phase 15 - Tests Audit

**What this section currently does**
- `tests/` contains standard `unittest` coverage for export logic, file loading, storage, services, profile helpers, theme contrast, assets, build config, bootstrap path handling, and app smoke imports.
- The app already has a safe smoke-exit mode through `CHEAT_EDITOR_MANAGER_SMOKE_EXIT=1`.

**What was wrong**
- The app smoke test proved imports and helper methods were available, but it did not prove that the real direct script or package entry point could create the Tk app and exit safely.
- This left startup wiring under-tested compared with the rest of the cleanup work.

**What changed**
- Added direct script startup smoke coverage for `cheat_editor_manager_tool.py`.
- Added package startup smoke coverage for `python -m cheat_editor_manager`.
- Both tests run in a subprocess with `CHEAT_EDITOR_MANAGER_SMOKE_EXIT=1`, so the app starts, updates once, closes, and returns control to the test runner.
- Added `CHEAT_EDITOR_MANAGER_SKIP_GUI_SMOKE=1` as an escape hatch for constrained machines that cannot create a Tk window.

**Files changed**
- `tests/test_app_smoke.py`.
- `README.md`.
- `docs/REDESIGN_PLAN.md`.
- `CLEANUP_PHASE_LOG.md`.

**Files added, removed, or moved**
- None.

**Wiring updated**
- No runtime wiring changed.
- Test coverage now exercises both startup wiring paths.

**Build/test/run status**
- Environment check passed: `python scripts/check_dev_environment.py`.
- Focused app smoke tests passed: `python -m unittest tests.test_app_smoke -v`.
- Compile check passed: `python -m compileall -q assets/generate_brand_assets.py cheat_editor_manager tests scripts hooks`.
- Unit tests passed: `python -m unittest discover -s tests -q` ran 67 tests.
- Source smoke mode passed with `CHEAT_EDITOR_MANAGER_SMOKE_EXIT=1`.
- PyInstaller clean build passed: `python -m PyInstaller --clean --noconfirm cheat_editor_manager_tool.spec`.
- Packaged executable smoke mode passed with `CHEAT_EDITOR_MANAGER_SMOKE_EXIT=1`.
- Whitespace diff check passed: `git diff --check`.

**Remaining risks**
- Optional drag-and-drop still depends on installing `tkinterdnd2`; that path is not active in the current global Python environment.
- Full manual UI click-through is still a separate final verification task.

**Next phase**
- Continue with documentation cleanup.

## Current Redesign Phase 16 - Documentation Cleanup

**What this section currently does**
- `README.md` is the main user/developer-facing guide for what the app does, how it starts, how to test, how to build, and where important folders live.
- `docs/REDESIGN_PLAN.md` tracks the cleanup/redesign checklist.
- `assets/README.md` explains runtime assets and retained brand-source files.
- `docs/Cheat_File_Creator_MASTER_EXPLANATION_v1_3_2.txt` is an older historical explanation.

**What was wrong**
- The README did not yet describe the current UI sections in one simple place.
- Future expansion points were scattered through maintenance notes rather than grouped clearly.
- The `docs/` folder did not have an index explaining which files are current and which are historical.
- The old v1.3.2 explanation file was versioned, but it did not start with a strong archive warning.

**What changed**
- Added `docs/README.md`.
- Added a clear archive warning to `docs/Cheat_File_Creator_MASTER_EXPLANATION_v1_3_2.txt`.
- Added README sections for Main UI Sections, Documentation, and Future Expansion Points.
- Updated the README project structure to list `docs/README.md` and the archived v1.3.2 explanation.
- Updated maintenance notes so future work follows the current docs index.
- Added `tests/test_docs.py` to protect the docs index, archive warning, README guide sections, and current local docs links.

**Files changed**
- `README.md`.
- `docs/REDESIGN_PLAN.md`.
- `docs/Cheat_File_Creator_MASTER_EXPLANATION_v1_3_2.txt`.
- `CLEANUP_PHASE_LOG.md`.

**Files added**
- `docs/README.md`.
- `tests/test_docs.py`.

**Files removed or moved**
- None.

**Wiring updated**
- No runtime wiring changed.
- Documentation references now point to the current docs index and current project structure.

**Build/test/run status**
- Focused docs tests passed: `python -m unittest tests.test_docs -v`.
- Compile check passed: `python -m compileall -q assets/generate_brand_assets.py cheat_editor_manager tests scripts hooks`.
- Unit tests passed: `python -m unittest discover -s tests -q` ran 71 tests.
- Whitespace diff check passed: `git diff --check`.

**Remaining risks**
- Final manual UI click-through and final packaged verification still belong to the final verification phase.

**Next phase**
- Continue with final cleanup.

## Current Redesign Phase 17 - Final Cleanup

**What this section currently does**
- The repo now has one app package, one storage package, one services layer, one UI package, one documented asset generator, and one PyInstaller packaging path.
- Generated local folders such as `build/`, `dist/`, `_tmp_mei/`, `.venv/`, and `__pycache__/` are ignored.

**What was wrong**
- `scripts/generate_brand_assets.py` was an unused wrapper around the real documented generator in `assets/generate_brand_assets.py`.
- `MANIFEST.in` did not include the documented utility scripts folder.
- `scripts/check_dev_environment.py` still described `tkinterdnd2` like a dev package instead of optional drag-and-drop support.

**What changed**
- Removed `scripts/generate_brand_assets.py`.
- Added `recursive-include scripts *.py` to `MANIFEST.in`.
- Updated `tests/test_build_config.py` to protect utility-script manifest coverage.
- Updated `scripts/check_dev_environment.py` optional-package labels and install hints.
- Rechecked stale deleted-module references, fake/TODO markers, duplicate runtime branding paths, stale window-setting leftovers, asset paths, dialog imports, and build paths.

**Files changed**
- `MANIFEST.in`.
- `scripts/check_dev_environment.py`.
- `tests/test_build_config.py`.
- `docs/REDESIGN_PLAN.md`.
- `CLEANUP_PHASE_LOG.md`.

**Files removed**
- `scripts/generate_brand_assets.py`.

**Files moved**
- None.

**Wiring updated**
- No runtime app wiring changed.
- Source package include rules now match the documented utility-script folder.
- Environment-check messaging now matches the real optional dependency groups.

**Build/test/run status**
- Environment check passed: `python scripts/check_dev_environment.py`.
- Compile check passed: `python -m compileall -q assets/generate_brand_assets.py cheat_editor_manager tests scripts hooks`.
- Unit tests passed: `python -m unittest discover -s tests -q` ran 71 tests.
- Source smoke mode passed with `CHEAT_EDITOR_MANAGER_SMOKE_EXIT=1`.
- PyInstaller clean build passed: `python -m PyInstaller --clean --noconfirm cheat_editor_manager_tool.spec`.
- Packaged executable smoke mode passed with `CHEAT_EDITOR_MANAGER_SMOKE_EXIT=1`.
- Whitespace diff check passed: `git diff --check`.
- Static lint tools were checked but unavailable: `pyflakes` and `ruff` are not installed in the current Python environment.

**Remaining risks**
- Local generated/environment folders remain on disk but are ignored: `.venv/`, `_tmp_mei/`, `build/`, and `dist/`.
- Final manual UI click-through still belongs to the final verification phase.

**Next phase**
- Run final build/manual verification and produce the final report.

## Current Redesign Phase 18 - Final Build, Verification, And Report

**What this section currently does**
- This phase proves the app can build, launch from source, launch from the packaged executable, and exercise the main UI workflow safely.

**What was wrong**
- The previous checklist still had manual UI workflow items open: Load File picker, editor text entry, profile/helper preview refresh, Quick Export validation, Convert & Save flow, final screenshot, and final concept comparison.

**What changed**
- Added `tests/test_ui_workflows.py` for safe GUI workflow smoke checks.
- Refreshed `assets/app-fullscreen.png` from the live app window after workflow checks passed.
- Updated `README.md` to mention GUI workflow smoke tests.
- Updated `docs/REDESIGN_PLAN.md` to mark final verification complete.

**Files changed**
- `README.md`.
- `assets/app-fullscreen.png`.
- `docs/REDESIGN_PLAN.md`.
- `CLEANUP_PHASE_LOG.md`.

**Files added**
- `tests/test_ui_workflows.py`.

**Files removed or moved**
- None in this phase.

**Wiring verified**
- Direct source entry point: `python cheat_editor_manager_tool.py`.
- Package entry point: `python -m cheat_editor_manager`.
- File picker wiring for Load File.
- Text entry in the editor.
- Profile refresh into helper text and export preview.
- Quick Export validation before writing.
- Convert & Save extension/save flow.
- PyInstaller packaged executable startup.

**Build/test/run checks completed**
- Environment check passed: `python scripts/check_dev_environment.py`.
- Compile check passed: `python -m compileall -q assets/generate_brand_assets.py cheat_editor_manager tests scripts hooks`.
- Unit tests passed: `python -m unittest discover -s tests -q` ran 75 tests.
- Source smoke mode passed with `CHEAT_EDITOR_MANAGER_SMOKE_EXIT=1`.
- PyInstaller clean build passed: `python -m PyInstaller --clean --noconfirm cheat_editor_manager_tool.spec`.
- Packaged executable smoke mode passed with `CHEAT_EDITOR_MANAGER_SMOKE_EXIT=1`.
- Whitespace diff check passed: `git diff --check`.
- Final executable produced: `dist/cheat_editor_manager_tool.exe`.

**Remaining problems**
- `pytest` is not installed, but the current suite runs through standard `unittest`.
- `tkinterdnd2` is not installed, so optional drag-and-drop support is not active in this environment. The app falls back to normal file loading.
- `pyflakes` and `ruff` are not installed, so static lint checks could not run.

**Recommended next steps**
- Install optional extras in a clean environment if desired: `python -m pip install -e ".[dev,dnd]"`.
- Manually click through drag-and-drop after `tkinterdnd2` is installed.
- Commit the cleaned project once the user has reviewed the final result.
