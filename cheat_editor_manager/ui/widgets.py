from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Optional

from ..services import theme_service


def _selection_palette_for_app(app) -> tuple[str, str]:
    button_colors = theme_service.effective_button_colors(app.prefs)
    return theme_service.selection_palette(button_colors["primary"])


def configure_listbox_theme(listbox: tk.Listbox, app) -> None:
    colors = app.effective_colors()
    selection_bg, selection_fg = _selection_palette_for_app(app)
    entry_fg = theme_service.ensure_text_contrast(
        colors["entry"], preferred=colors["text"], minimum=4.5
    )
    listbox.configure(
        bg=colors["entry"],
        fg=entry_fg,
        selectbackground=selection_bg,
        selectforeground=selection_fg,
        highlightbackground=colors["border"],
        highlightcolor=colors["accent"],
        relief="solid",
        bd=1,
    )


def configure_text_theme(text: tk.Text, app, *, editor: bool = False) -> None:
    colors = app.effective_colors()
    selection_bg, selection_fg = _selection_palette_for_app(app)
    bg_key = "editor_bg" if editor else "entry"
    fg_key = "editor_fg" if editor else "text"
    foreground = theme_service.ensure_text_contrast(
        colors[bg_key], preferred=colors[fg_key], minimum=4.5
    )
    text.configure(
        bg=colors[bg_key],
        fg=foreground,
        insertbackground=foreground,
        selectbackground=selection_bg,
        selectforeground=selection_fg,
        highlightbackground=colors["border"],
        highlightcolor=colors["accent"],
        relief="solid",
        bd=1,
    )


class AutoScrollbar(ttk.Scrollbar):
    """Scrollbar that appears only when its linked widget has overflow."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._layout_manager = ""
        self._pack_options = {}

    def grid(self, *args, **kwargs):
        self._layout_manager = "grid"
        return super().grid(*args, **kwargs)

    def pack(self, *args, **kwargs):
        self._layout_manager = "pack"
        self._pack_options = dict(kwargs)
        return super().pack(*args, **kwargs)

    def set(self, first, last) -> None:
        try:
            first_f = float(first)
            last_f = float(last)
        except (TypeError, ValueError):
            first_f = 0.0
            last_f = 0.0

        if first_f <= 0.001 and last_f >= 0.999:
            self._hide()
        else:
            self._show()
        super().set(first, last)

    def _hide(self) -> None:
        if self._layout_manager == "pack":
            self.pack_forget()
            return
        self.grid_remove()

    def _show(self) -> None:
        if self._layout_manager == "pack":
            self.pack(**self._pack_options)
            return
        self.grid()


def _readable_text_color(bg: str, *, light: str = "#fff8eb", dark: str = "#231b15") -> str:
    return theme_service.readable_text_color(bg, light=light, dark=dark)

class ToolTip:
    """Simple Tk tooltip (pure tkinter, no dependencies)."""

    def __init__(self, widget, text: str, delay_ms: int = 450):
        self.widget = widget
        self.text = text
        self.delay_ms = delay_ms
        self._after_id = None
        self._tip = None
        widget.bind("<Enter>", self._schedule, add="+")
        widget.bind("<Leave>", self._hide, add="+")
        widget.bind("<ButtonPress>", self._hide, add="+")

    def _schedule(self, *_):
        self._cancel()
        self._after_id = self.widget.after(self.delay_ms, self._show)

    def _cancel(self):
        if self._after_id is not None:
            try:
                self.widget.after_cancel(self._after_id)
            except Exception:
                pass
            self._after_id = None

    def _show(self):
        if self._tip or not self.text:
            return
        try:
            x = self.widget.winfo_rootx() + 12
            y = self.widget.winfo_rooty() + self.widget.winfo_height() + 8
        except Exception:
            return

        self._tip = tk.Toplevel(self.widget)
        self._tip.wm_overrideredirect(True)
        self._tip.wm_geometry(f"+{x}+{y}")

        frm = tk.Frame(self._tip, bd=1, relief="solid")
        frm.pack(fill="both", expand=True)

        lbl = tk.Label(frm, text=self.text, justify="left", padx=8, pady=6, wraplength=380)
        lbl.pack()

        # Try to inherit theme-ish colours (works fine in light/dark/custom)
        try:
            bg = self.widget.winfo_toplevel().cget("bg")
            fg = _readable_text_color(bg)
            lbl.configure(bg=bg, fg=fg)
            frm.configure(bg=bg)
        except Exception:
            pass

    def _hide(self, *_):
        self._cancel()
        if self._tip:
            try:
                self._tip.destroy()
            except Exception:
                pass
            self._tip = None

class Scrollable(ttk.Frame):
    """A scrollable container that auto-hides scrollbars when not needed."""

    def __init__(self, parent):
        super().__init__(parent)

        # Use a tk.Canvas so we can scroll any Tk/ttk widgets placed inside.
        self.canvas = tk.Canvas(self, highlightthickness=0)
        self.v = AutoScrollbar(self, orient="vertical", command=self.canvas.yview)
        self.h = AutoScrollbar(self, orient="horizontal", command=self.canvas.xview)

        self.inner = ttk.Frame(self.canvas)
        self.inner_id = self.canvas.create_window((0, 0), window=self.inner, anchor="nw")

        self.canvas.configure(yscrollcommand=self.v.set, xscrollcommand=self.h.set)

        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.v.grid(row=0, column=1, sticky="ns")
        self.h.grid(row=1, column=0, sticky="ew")

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        self.inner.bind("<Configure>", self._on_inner_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)

        # initial hide until we know content size
        self.v.grid_remove()
        self.h.grid_remove()

    def set_canvas_bg(self, bg: str):
        """Set canvas background (used by theming)."""
        try:
            self.canvas.configure(bg=bg)
        except Exception:
            pass

    def _update_scrollbars(self):
        bbox = self.canvas.bbox("all")
        if not bbox:
            return
        x0, y0, x1, y1 = bbox
        cw = max(1, self.canvas.winfo_width())
        ch = max(1, self.canvas.winfo_height())
        need_h = (x1 - x0) > (cw + 2)
        need_v = (y1 - y0) > (ch + 2)

        if need_v:
            self.v.grid()
        else:
            self.v.grid_remove()

        if need_h:
            self.h.grid()
        else:
            self.h.grid_remove()

    def _on_inner_configure(self, _e=None):
        try:
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        except Exception:
            pass
        self._update_scrollbars()

    def _on_canvas_configure(self, e=None):
        # Match inner width and minimum height to the canvas so content reflows.
        try:
            w = max(1, self.canvas.winfo_width() if e is None else e.width)
            h = max(1, self.canvas.winfo_height() if e is None else e.height)
            requested_h = max(1, self.inner.winfo_reqheight())
            self.canvas.itemconfigure(self.inner_id, width=w, height=max(h, requested_h))
        except Exception:
            pass
        self._update_scrollbars()

def ask_text(parent, title: str, label: str) -> Optional[str]:
    win = tk.Toplevel(parent)
    win.title(title)
    win.transient(parent)
    win.grab_set()
    win.resizable(False, False)
    try:
        win.configure(bg=parent.winfo_toplevel().cget("bg"))
    except Exception:
        pass

    frame = ttk.Frame(win)
    frame.pack(fill="both", expand=True, padx=12, pady=12)

    ttk.Label(frame, text=label).pack(anchor="w", pady=(0, 6))
    var = tk.StringVar()
    ent = ttk.Entry(frame, textvariable=var, width=48)
    ent.pack(fill="x", pady=(0, 10))
    ent.focus_set()
    out = {"v": None}

    def ok():
        out["v"] = var.get().strip()
        win.destroy()

    row = ttk.Frame(frame)
    row.pack(fill="x")
    ttk.Button(row, text="OK", command=ok).pack(side="left")
    ttk.Button(row, text="Cancel", command=win.destroy).pack(side="left", padx=(8, 0))
    win.wait_window()
    return out["v"]
