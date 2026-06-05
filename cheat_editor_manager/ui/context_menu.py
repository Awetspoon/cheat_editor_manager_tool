from __future__ import annotations

import tkinter as tk


def build_context_menu(app) -> None:
    app._ctx_menu = tk.Menu(app.root, tearoff=0)
    app._ctx_menu.add_command(label="Cut", command=lambda: app._ctx_action("cut"))
    app._ctx_menu.add_command(label="Copy", command=lambda: app._ctx_action("copy"))
    app._ctx_menu.add_command(label="Paste", command=lambda: app._ctx_action("paste"))
    app._ctx_menu.add_separator()
    app._ctx_menu.add_command(label="Delete", command=lambda: app._ctx_action("delete"))
    app._ctx_menu.add_command(
        label="Select All", command=lambda: app._ctx_action("select_all")
    )
    app._ctx_widget = None

    for class_name in ("Entry", "Text", "TEntry"):
        try:
            app.root.bind_class(class_name, "<Button-3>", app._show_ctx_menu, add="+")
            app.root.bind_class(class_name, "<Shift-F10>", app._show_ctx_menu, add="+")
        except Exception:
            pass


def show_context_menu(app, event):
    try:
        app._ctx_widget = event.widget
        app._ctx_menu.tk_popup(event.x_root, event.y_root)
    finally:
        try:
            app._ctx_menu.grab_release()
        except Exception:
            pass
    return "break"


def run_context_action(app, action: str) -> None:
    widget = getattr(app, "_ctx_widget", None)
    if widget is None:
        return
    try:
        if action == "cut":
            widget.event_generate("<<Cut>>")
        elif action == "copy":
            widget.event_generate("<<Copy>>")
        elif action == "paste":
            widget.event_generate("<<Paste>>")
        elif action == "delete":
            _delete_selection_or_char(widget)
        elif action == "select_all":
            _select_all(widget)
    except Exception:
        pass


def _delete_selection_or_char(widget) -> None:
    try:
        if isinstance(widget, tk.Text):
            if widget.tag_ranges("sel"):
                widget.delete("sel.first", "sel.last")
            else:
                widget.delete("insert")
            return

        if widget.selection_present():
            widget.delete("sel.first", "sel.last")
            return

        index = widget.index("insert")
        if index is not None:
            try:
                widget.delete(index)
            except Exception:
                pass
    except Exception:
        pass


def _select_all(widget) -> None:
    try:
        if isinstance(widget, tk.Text):
            widget.tag_add("sel", "1.0", "end-1c")
            widget.mark_set("insert", "end-1c")
            widget.see("insert")
            return

        widget.selection_range(0, "end")
        widget.icursor("end")
    except Exception:
        pass
