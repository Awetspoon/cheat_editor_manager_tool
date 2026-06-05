from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from ...constants import APP_NAME, APP_TAGLINE
from ...services import theme_service
from ..style import FONT_HEADER_SUBTITLE, FONT_HEADER_TITLE


HEADER_PAD_X = 14
HEADER_BRAND_PAD_Y = 7
HEADER_ACTION_PAD_Y = 8
HEADER_BUTTON_GAP = 8


def build_header(app) -> None:
    header_bg = theme_service.effective_button_colors(app.prefs)["header"]

    app.header = tk.Frame(app.root, bg=header_bg, bd=0, highlightthickness=1)
    app.header.pack(fill="x")
    app.header.columnconfigure(0, weight=1)

    _build_brand_area(app)
    _build_action_strip(app)
    app._apply_brand_images()


def _build_brand_area(app) -> None:
    app.header_brand = tk.Frame(app.header, bg=app.header["bg"])
    app.header_brand.grid(
        row=0,
        column=0,
        sticky="w",
        padx=HEADER_PAD_X,
        pady=HEADER_BRAND_PAD_Y,
    )
    app.header_mark = tk.Label(app.header_brand, bg=app.header["bg"], bd=0)
    app.header_mark.grid(row=0, column=0, rowspan=2, sticky="w", padx=(0, 10))

    app.header_titles = tk.Frame(app.header_brand, bg=app.header["bg"])
    app.header_titles.grid(row=0, column=1, sticky="w")
    app.header_title = tk.Label(
        app.header_titles,
        text=APP_NAME,
        bg=app.header["bg"],
        fg="#fff6e8",
        font=FONT_HEADER_TITLE,
        bd=0,
    )
    app.header_title.pack(anchor="w")
    app.header_subtitle = tk.Label(
        app.header_titles,
        text=APP_TAGLINE,
        bg=app.header["bg"],
        fg="#ffd5b8",
        font=FONT_HEADER_SUBTITLE,
        bd=0,
    )
    app.header_subtitle.pack(anchor="w")


def _build_action_strip(app) -> None:
    app.header_actions = tk.Frame(app.header, bg=app.header["bg"])
    app.header_actions.grid(
        row=0,
        column=1,
        sticky="e",
        padx=HEADER_PAD_X,
        pady=HEADER_ACTION_PAD_Y,
    )

    app.btn_settings = _header_button(
        app,
        text="Settings",
        command=app.open_settings,
    )
    app.btn_links = _header_button(
        app,
        text="Help Links",
        command=app.open_help_links,
    )
    app.btn_templates = _header_button(
        app,
        text="Templates...",
        command=app.open_templates,
    )
    app.btn_dark = _header_button(
        app,
        text="Dark Mode",
        command=app.toggle_mode,
    )


def _header_button(app, *, text: str, command) -> ttk.Button:
    has_previous_button = bool(app.header_actions.winfo_children())
    button = ttk.Button(
        app.header_actions,
        text=text,
        command=command,
        style="Header.TButton",
    )
    button.pack(
        side="left",
        padx=(HEADER_BUTTON_GAP if has_previous_button else 0, 0),
    )
    return button
