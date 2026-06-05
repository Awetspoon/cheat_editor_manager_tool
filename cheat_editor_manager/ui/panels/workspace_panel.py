from __future__ import annotations

import tkinter as tk

from ..style import CONTROL_GAP, PANEL_OUTER_PAD_X


LEFT_COLUMN_WIDTH = 292
RIGHT_COLUMN_WIDTH = 350
CENTER_MIN_WIDTH = 520


def build_workspace(app) -> None:
    app.workspace = tk.Frame(app.body.inner, bd=0, highlightthickness=0)
    app.workspace.pack(
        fill="both",
        expand=True,
        padx=PANEL_OUTER_PAD_X,
        pady=(CONTROL_GAP, CONTROL_GAP),
    )
    app.workspace.columnconfigure(0, weight=0, minsize=LEFT_COLUMN_WIDTH)
    app.workspace.columnconfigure(1, weight=1, minsize=CENTER_MIN_WIDTH)
    app.workspace.columnconfigure(2, weight=0, minsize=RIGHT_COLUMN_WIDTH)
    app.workspace.rowconfigure(0, weight=1)

    app.left_sidebar = tk.Frame(app.workspace, bd=0, highlightthickness=0)
    app.left_sidebar.grid(row=0, column=0, sticky="nsew", padx=(0, CONTROL_GAP))
    app.left_sidebar.configure(width=LEFT_COLUMN_WIDTH)
    app.left_sidebar.grid_propagate(False)
    app.left_sidebar.pack_propagate(False)

    app.editor_workspace = tk.Frame(app.workspace, bd=0, highlightthickness=0)
    app.editor_workspace.grid(row=0, column=1, sticky="nsew")
    app.editor_workspace.columnconfigure(0, weight=1)
    app.editor_workspace.rowconfigure(0, weight=1)

    app.right_sidebar = tk.Frame(app.workspace, bd=0, highlightthickness=0)
    app.right_sidebar.grid(row=0, column=2, sticky="nsew", padx=(CONTROL_GAP, 0))
    app.right_sidebar.columnconfigure(0, weight=1)
    app.right_sidebar.configure(width=RIGHT_COLUMN_WIDTH)
    app.right_sidebar.grid_propagate(False)
    app.right_sidebar.pack_propagate(False)
