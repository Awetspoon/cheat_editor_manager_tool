from __future__ import annotations

import tkinter as tk
from tkinter import ttk

def _readable_text_color(bg: str, *, light: str = "#fff8eb", dark: str = "#231b15") -> str:
    try:
        value = (bg or "").strip().lstrip("#")
        if len(value) == 3:
            value = "".join(ch * 2 for ch in value)
        if len(value) != 6:
            raise ValueError("Expected a 6-digit hex color")
        r = int(value[0:2], 16)
        g = int(value[2:4], 16)
        b = int(value[4:6], 16)
        luminance = ((0.2126 * r) + (0.7152 * g) + (0.0722 * b)) / 255.0
        return dark if luminance >= 0.58 else light
    except Exception:
        return dark

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
        self.v = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.h = ttk.Scrollbar(self, orient="horizontal", command=self.canvas.xview)

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
        # Match inner width to canvas width so content reflows
        try:
            w = max(1, self.canvas.winfo_width() if e is None else e.width)
            self.canvas.itemconfigure(self.inner_id, width=w)
        except Exception:
            pass
        self._update_scrollbars()

def ask_text(parent, title: str, label: str) -> Optional[str]:
    win = tk.Toplevel(parent)
    win.title(title)
    win.transient(parent)
    win.grab_set()
    win.resizable(False, False)
    ttk.Label(win, text=label).pack(anchor="w", padx=12, pady=(12, 6))
    var = tk.StringVar()
    ent = ttk.Entry(win, textvariable=var, width=48)
    ent.pack(fill="x", padx=12, pady=(0, 10))
    ent.focus_set()
    out = {"v": None}
    def ok():
        out["v"] = var.get().strip()
        win.destroy()
    row = ttk.Frame(win)
    row.pack(fill="x", padx=12, pady=(0, 12))
    ttk.Button(row, text="OK", command=ok).pack(side="left")
    ttk.Button(row, text="Cancel", command=win.destroy).pack(side="left", padx=(8, 0))
    win.wait_window()
    return out["v"]
