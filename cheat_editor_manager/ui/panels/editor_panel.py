from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk

from ...storage import save_prefs
from ..widgets import AutoScrollbar
from ..style import (
    CONTROL_GAP,
    FONT_SUBSECTION,
    PANEL_GAP,
    PANEL_INNER_PAD_X,
    PANEL_OUTER_PAD_X,
)


PANEL_PAD_X = PANEL_INNER_PAD_X
TOOLBAR_GAP = CONTROL_GAP


def build_editor_panel(app, *, has_dnd: bool, dnd_files) -> None:
    _build_editor_shell(app)
    _build_editor_header(app)
    _build_editor_toolbar(app)
    _build_editor_text_area(app, has_dnd=has_dnd, dnd_files=dnd_files)


def _build_editor_shell(app) -> None:
    parent = getattr(app, "editor_workspace", app.body.inner)
    app.editor_panel = tk.Frame(parent, bd=0, highlightthickness=1)
    if hasattr(app, "editor_workspace"):
        app.editor_panel.pack(fill="both", expand=True, padx=0, pady=(0, PANEL_GAP))
    else:
        app.editor_panel.pack(
            fill="both", expand=True, padx=PANEL_OUTER_PAD_X, pady=(0, PANEL_GAP)
        )
    app.editor_panel.columnconfigure(0, weight=1)
    app.editor_panel.rowconfigure(2, weight=1)


def _build_editor_header(app) -> None:
    app.editor_header = tk.Frame(app.editor_panel, bd=0, highlightthickness=0)
    app.editor_header.grid(
        row=0, column=0, sticky="ew", padx=PANEL_PAD_X, pady=(9, 4)
    )
    app.editor_header.columnconfigure(0, weight=1)
    app.editor_title = tk.Label(
        app.editor_header, text="Cheat Editor", font=FONT_SUBSECTION, anchor="w"
    )
    app.editor_title.grid(row=0, column=0, sticky="w")

    app.wrap_var = tk.BooleanVar(value=bool(app.prefs.get("wrap", True)))
    app.wrap_check = ttk.Checkbutton(
        app.editor_header,
        text="Wrap text",
        variable=app.wrap_var,
        command=app.toggle_wrap,
        style="Editor.TCheckbutton",
    )
    app.wrap_check.grid(row=0, column=1, sticky="e")


def _build_editor_toolbar(app) -> None:
    app.editor_toolbar = tk.Frame(app.editor_panel, bd=0, highlightthickness=0)
    app.editor_toolbar.grid(
        row=1, column=0, sticky="ew", padx=PANEL_PAD_X, pady=(0, CONTROL_GAP)
    )
    for label, style, command in (
        ("Heading", "Toolbar.TButton", app.fmt_heading),
        ("Bold", "Toolbar.TButton", app.fmt_bold),
        ("Undo", "Toolbar.TButton", app.do_undo),
        ("Redo", "Toolbar.TButton", app.do_redo),
        ("Clear text", "Danger.TButton", app.clear_editor),
    ):
        _toolbar_button(app, text=label, style=style, command=command)


def _toolbar_button(app, *, text: str, style: str, command) -> ttk.Button:
    has_previous_button = bool(app.editor_toolbar.winfo_children())
    button = ttk.Button(
        app.editor_toolbar,
        text=text,
        style=style,
        command=command,
    )
    button.pack(side="left", padx=(TOOLBAR_GAP if has_previous_button else 0, 0))
    return button


def _build_editor_text_area(app, *, has_dnd: bool, dnd_files) -> None:
    app.editor_frame = tk.Frame(app.editor_panel, bd=0, highlightthickness=1)
    app.editor_frame.grid(
        row=2, column=0, sticky="nsew", padx=PANEL_PAD_X, pady=(0, 12)
    )
    app.editor_frame.columnconfigure(0, weight=1)
    app.editor_frame.rowconfigure(0, weight=1)
    app.editor = tk.Text(
        app.editor_frame,
        height=16,
        wrap=tk.WORD if app.wrap_var.get() else tk.NONE,
        undo=True,
        autoseparators=True,
        maxundo=4000,
        bd=0,
        highlightthickness=0,
    )
    _wire_editor_scrollbars(app)
    _register_drop_target(app, has_dnd=has_dnd, dnd_files=dnd_files)
    _bind_editor_shortcuts(app)


def _wire_editor_scrollbars(app) -> None:
    vertical_scrollbar = AutoScrollbar(
        app.editor_frame, orient="vertical", command=app.editor.yview
    )
    horizontal_scrollbar = AutoScrollbar(
        app.editor_frame, orient="horizontal", command=app.editor.xview
    )
    app.editor.configure(
        yscrollcommand=vertical_scrollbar.set,
        xscrollcommand=horizontal_scrollbar.set,
    )

    app.editor.grid(row=0, column=0, sticky="nsew")
    vertical_scrollbar.grid(row=0, column=1, sticky="ns")
    horizontal_scrollbar.grid(row=1, column=0, sticky="ew")


def _register_drop_target(app, *, has_dnd: bool, dnd_files) -> None:
    if not has_dnd:
        return
    try:
        app.editor.drop_target_register(dnd_files)
        app.editor.dnd_bind("<<Drop>>", app._on_drop_files)
    except Exception:
        pass


def _bind_editor_shortcuts(app) -> None:
    app.editor.bind("<Control-z>", app.do_undo)
    app.editor.bind("<Control-y>", app.do_redo)
    app.editor.bind("<Control-Shift-Z>", app.do_redo)
    app.editor.bind("<Control-Shift-z>", app.do_redo)

    try:
        app.editor.bind("<<Modified>>", app._on_editor_modified)
        app.editor.edit_modified(False)
    except Exception:
        pass


def format_heading(app) -> None:
    try:
        line_start = app.editor.index("insert linestart")
        current_line = app.editor.get(line_start, f"{line_start} lineend")
        if current_line.lstrip().startswith("#"):
            return
        app.editor.insert(line_start, "# ")
    except Exception:
        pass


def format_bold(app) -> None:
    try:
        if app.editor.tag_ranges(tk.SEL):
            selected_text = app.editor.get(tk.SEL_FIRST, tk.SEL_LAST)
            app.editor.delete(tk.SEL_FIRST, tk.SEL_LAST)
            app.editor.insert(tk.INSERT, f"*{selected_text}*")
        else:
            app.editor.insert(tk.INSERT, "**")
            app.editor.mark_set(tk.INSERT, f"{app.editor.index(tk.INSERT)}-1c")
    except Exception:
        pass


def undo(app, *_):
    try:
        app.editor.edit_undo()
    except Exception:
        pass


def redo(app, *_):
    try:
        app.editor.edit_redo()
    except Exception:
        pass


def clear_editor(app) -> None:
    if messagebox.askyesno(
        "Clear editor text",
        (
            "This will remove all text from the editor only.\n\n"
            "Templates, settings, and files on disk will NOT be affected.\n\n"
            "Do you want to continue?"
        ),
    ):
        try:
            app.editor.edit_separator()
        except Exception:
            pass
        app.editor.delete("1.0", tk.END)


def toggle_wrap(app) -> None:
    app.prefs["wrap"] = bool(app.wrap_var.get())
    save_prefs(app.prefs)
    app.editor.configure(wrap=tk.WORD if app.wrap_var.get() else tk.NONE)


def handle_drop_files(app, event) -> None:
    data = (getattr(event, "data", "") or "").strip()
    if not data:
        return
    paths = []
    for braced, plain in _split_drop_data(data):
        candidate = (braced or plain).strip()
        if candidate:
            paths.append(candidate)
    filepath = paths[0] if paths else data
    app.load_file(filepath)


def _split_drop_data(data: str) -> list[tuple[str, str]]:
    import re

    return re.findall(r"\{([^}]*)\}|([^\s]+)", data)
