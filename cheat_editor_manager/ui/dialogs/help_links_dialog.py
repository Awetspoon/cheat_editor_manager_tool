from __future__ import annotations

import tkinter as tk
import webbrowser
from typing import Optional

from tkinter import messagebox, ttk

from ...services import help_link_service
from ...storage import save_prefs
from ...ui.style import CONTROL_GAP, PANEL_GAP, PANEL_INNER_PAD_X
from ...ui.widgets import AutoScrollbar
from .dialog_utils import (
    bind_dialog_shortcuts,
    build_dialog_footer,
    build_dialog_header,
    configure_dialog_window,
)


HELP_LINKS_GEOMETRY = "760x480"
LINK_DIALOG_GEOMETRY = "560x245"
CONTENT_PAD = PANEL_INNER_PAD_X
BUTTON_GAP = CONTROL_GAP


def open_help_links(app):
    self = app
    win = tk.Toplevel(self.root)
    configure_dialog_window(self, win, "Help Links", HELP_LINKS_GEOMETRY)
    try:
        win.minsize(700, 430)
    except Exception:
        pass

    build_dialog_header(
        self,
        win,
        "Cheat Source Links",
        "Save the websites or pages where you found cheat codes.",
    )

    body = ttk.Frame(win)
    body.pack(fill="both", expand=True, padx=CONTENT_PAD, pady=(0, PANEL_GAP))
    body.columnconfigure(0, weight=1)
    body.rowconfigure(1, weight=1)

    action_row = ttk.Frame(body)
    action_row.grid(row=0, column=0, sticky="ew", pady=(0, CONTROL_GAP))
    ttk.Label(action_row, text="Saved source locations").pack(side="left")

    table_frame = ttk.Frame(body)
    table_frame.grid(row=1, column=0, sticky="nsew")
    table_frame.columnconfigure(0, weight=1)
    table_frame.rowconfigure(0, weight=1)

    columns = ("name", "url")
    table = ttk.Treeview(
        table_frame,
        columns=columns,
        show="headings",
        height=12,
        selectmode="browse",
    )
    table.heading("name", text="Name")
    table.heading("url", text="Website")
    table.column("name", width=220, minwidth=130, stretch=False)
    table.column("url", width=460, minwidth=220, stretch=True)

    y_scroll = AutoScrollbar(table_frame, orient="vertical", command=table.yview)
    x_scroll = AutoScrollbar(table_frame, orient="horizontal", command=table.xview)
    table.configure(yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set)
    table.grid(row=0, column=0, sticky="nsew")
    y_scroll.grid(row=0, column=1, sticky="ns")
    x_scroll.grid(row=1, column=0, sticky="ew")

    def current_links() -> list[dict[str, str]]:
        return help_link_service.normalize_links(self.prefs.get("help_links"))

    def selected_index() -> Optional[int]:
        selection = table.selection()
        if not selection:
            return None
        try:
            return int(selection[0])
        except Exception:
            return None

    def refresh(index: Optional[int] = None) -> None:
        table.delete(*table.get_children())
        links = current_links()
        for row_index, item in enumerate(links):
            table.insert(
                "",
                "end",
                iid=str(row_index),
                values=(
                    help_link_service.display_name(item),
                    help_link_service.display_url(item),
                ),
            )
        if links:
            target = index if index is not None else 0
            target = max(0, min(target, len(links) - 1))
            iid = str(target)
            table.selection_set(iid)
            table.focus(iid)
            table.see(iid)

    def save_links(links: list[dict[str, str]], selected: Optional[int] = None) -> None:
        self.prefs["help_links"] = links
        save_prefs(self.prefs)
        refresh(selected)

    def prompt_link(
        existing: Optional[dict] = None,
        *,
        edit_index: int | None = None,
    ) -> Optional[dict[str, str]]:
        dlg = tk.Toplevel(win)
        title = "Edit Source Link" if existing else "Add Source Link"
        configure_dialog_window(
            self,
            dlg,
            title,
            LINK_DIALOG_GEOMETRY,
            parent=win,
            resizable=False,
        )
        build_dialog_header(
            self,
            dlg,
            title,
            "Save where the cheat information came from.",
        )

        form = ttk.Frame(dlg)
        form.pack(fill="both", expand=True, padx=CONTENT_PAD, pady=(0, PANEL_GAP))
        form.columnconfigure(1, weight=1)

        name_var = tk.StringVar(value=(existing or {}).get("name", ""))
        url_var = tk.StringVar(value=(existing or {}).get("url", ""))

        ttk.Label(form, text="Source name").grid(
            row=0, column=0, sticky="w", pady=(0, CONTROL_GAP)
        )
        name_entry = ttk.Entry(form, textvariable=name_var)
        name_entry.grid(
            row=0,
            column=1,
            sticky="ew",
            padx=(BUTTON_GAP, 0),
            pady=(0, CONTROL_GAP),
        )

        ttk.Label(form, text="Website").grid(
            row=1, column=0, sticky="w", pady=(0, CONTROL_GAP)
        )
        url_entry = ttk.Entry(form, textvariable=url_var)
        url_entry.grid(
            row=1,
            column=1,
            sticky="ew",
            padx=(BUTTON_GAP, 0),
            pady=(0, CONTROL_GAP),
        )

        output: dict[str, Optional[dict[str, str]]] = {"value": None}

        def save() -> None:
            name = name_var.get().strip()
            url = help_link_service.normalize_url(url_var.get())
            if not name or not url:
                messagebox.showerror(
                    "Help Links",
                    "Source name and website are both required.",
                    parent=dlg,
                )
                return

            duplicate = help_link_service.duplicate_url_index(
                current_links(),
                url,
                ignore_index=edit_index,
            )
            if duplicate is not None:
                duplicate_name = help_link_service.display_name(current_links()[duplicate])
                if not messagebox.askyesno(
                    "Duplicate Source",
                    f"'{duplicate_name}' already uses this website. Save it anyway?",
                    parent=dlg,
                ):
                    return

            output["value"] = {"name": name, "url": url}
            dlg.destroy()

        def cancel() -> None:
            output["value"] = None
            dlg.destroy()

        footer = build_dialog_footer(self, dlg, pady=(0, CONTENT_PAD))
        ttk.Button(footer, text="Cancel", command=cancel).pack(
            side="right",
            padx=(BUTTON_GAP, CONTENT_PAD),
            pady=PANEL_GAP,
        )
        ttk.Button(footer, text="Save", command=save).pack(
            side="right",
            pady=PANEL_GAP,
        )

        bind_dialog_shortcuts(dlg, confirm=save, cancel=cancel)
        name_entry.focus_set()
        dlg.wait_window()
        return output["value"]

    def open_link(_event=None) -> None:
        idx = selected_index()
        if idx is None:
            return
        links = current_links()
        if idx >= len(links):
            return
        url = links[idx].get("url", "")
        if url:
            webbrowser.open(url)

    def add_link() -> None:
        item = prompt_link()
        if not item:
            return
        links = help_link_service.add_link(current_links(), item)
        save_links(links, len(links) - 1)

    def edit_link() -> None:
        idx = selected_index()
        if idx is None:
            return
        links = current_links()
        if idx >= len(links):
            return
        item = prompt_link(links[idx], edit_index=idx)
        if not item:
            return
        links = help_link_service.replace_link(links, idx, item)
        save_links(links, idx)

    def delete_link() -> None:
        idx = selected_index()
        if idx is None:
            return
        links = current_links()
        if idx >= len(links):
            return
        name = help_link_service.display_name(links[idx])
        if not messagebox.askyesno(
            "Delete Source Link",
            f"Delete '{name}' from your saved source links?",
            parent=win,
        ):
            return
        links = help_link_service.delete_link(links, idx)
        save_links(links, max(idx - 1, 0))

    table.bind("<Double-1>", open_link)
    table.bind("<Return>", open_link)

    footer = build_dialog_footer(self, win, pady=(0, CONTENT_PAD))
    ttk.Button(footer, text="Open Link", command=open_link).pack(
        side="left", padx=(CONTENT_PAD, 0), pady=PANEL_GAP
    )
    ttk.Button(footer, text="Add Link", command=add_link).pack(
        side="left", padx=(BUTTON_GAP, 0), pady=PANEL_GAP
    )
    ttk.Button(footer, text="Edit", command=edit_link).pack(
        side="left", padx=(BUTTON_GAP, 0), pady=PANEL_GAP
    )
    ttk.Button(
        footer,
        text="Delete",
        command=delete_link,
        style="Danger.TButton",
    ).pack(side="left", padx=(BUTTON_GAP, 0), pady=PANEL_GAP)
    ttk.Button(footer, text="Close", command=win.destroy).pack(
        side="right", padx=CONTENT_PAD, pady=PANEL_GAP
    )

    refresh(0)
