from __future__ import annotations

import tkinter.font as tkfont
from tkinter import ttk

from ..constants import DEFAULT_BUTTON_COLORS
from ..services import theme_service
from .style import (
    FONT_BODY,
    FONT_BODY_FAMILY,
    FONT_CODE_BOLD,
    FONT_HEADING_FAMILY,
    FONT_PANEL_TITLE,
    FONT_STATUS,
)


def build_styles(app) -> None:
    style = ttk.Style(app.root)
    try:
        style.theme_use("clam")
    except Exception:
        pass
    try:
        style.configure("Profile.TCombobox", padding=(6, 4))
    except Exception:
        pass

    try:
        tkfont.nametofont("TkDefaultFont").configure(
            family=FONT_BODY_FAMILY, size=FONT_BODY[1]
        )
        tkfont.nametofont("TkTextFont").configure(
            family=FONT_BODY_FAMILY, size=FONT_BODY[1]
        )
        tkfont.nametofont("TkFixedFont").configure(
            family=FONT_BODY_FAMILY, size=FONT_BODY[1]
        )
        tkfont.nametofont("TkMenuFont").configure(
            family=FONT_BODY_FAMILY, size=FONT_BODY[1]
        )
        tkfont.nametofont("TkHeadingFont").configure(
            family=FONT_HEADING_FAMILY, size=FONT_BODY[1], weight="bold"
        )
    except Exception:
        pass

    style.configure("TButton", padding=(8, 5), borderwidth=2, relief="ridge")
    style.configure("Header.TButton", padding=(10, 5), borderwidth=1, relief="flat")
    style.configure("Primary.TButton", padding=(8, 5), borderwidth=2, relief="ridge")
    style.configure("Danger.TButton", padding=(8, 5), borderwidth=2, relief="ridge")
    style.configure("TLabelframe", borderwidth=2, relief="groove")


def apply_theme(app) -> None:
    colors = app.effective_colors()
    button_colors = theme_service.effective_button_colors(app.prefs)
    style = ttk.Style(app.root)
    selection_bg, selection_fg = theme_service.selection_palette(
        button_colors.get("primary", DEFAULT_BUTTON_COLORS["primary"])
    )
    panel_text = theme_service.ensure_text_contrast(
        colors["panel"], preferred=colors["text"], minimum=4.5
    )
    panel2_text = theme_service.ensure_text_contrast(
        colors["panel2"], preferred=colors["text"], minimum=4.5
    )
    hint_fg = theme_service.ensure_text_contrast(
        colors["panel"], preferred=colors["muted"], minimum=3.4
    )
    bg_hint_fg = theme_service.ensure_text_contrast(
        colors["bg"], preferred=colors["muted"], minimum=3.4
    )
    entry_fg = theme_service.ensure_text_contrast(
        colors["entry"], preferred=colors["text"], minimum=4.5
    )
    entry_disabled_bg = theme_service.blend_colors(colors["entry"], colors["panel"], 0.25)
    entry_disabled_fg = theme_service.ensure_text_contrast(
        entry_disabled_bg,
        preferred=theme_service.blend_colors(entry_fg, colors["panel"], 0.35),
        minimum=3.0,
    )

    _configure_base_styles(
        app,
        style,
        colors,
        panel_text,
        panel2_text,
        bg_hint_fg,
        entry_fg,
        entry_disabled_bg,
        entry_disabled_fg,
        selection_bg,
        selection_fg,
    )
    _configure_button_styles(app, style, colors, button_colors)
    _configure_profile_dropdown_style(
        app,
        style,
        colors,
        button_colors,
        entry_fg,
        entry_disabled_bg,
        entry_disabled_fg,
    )
    _configure_notebook_styles(style, colors, panel_text, panel2_text)
    _configure_root_surfaces(app, colors)
    _configure_status_bar(app, colors)
    _configure_context_menu(app, colors, panel_text, hint_fg)
    _configure_header(app, style, colors, button_colors)
    _configure_profile_controls(app, colors, panel_text, panel2_text, hint_fg)
    _configure_editor(app, colors, selection_bg, selection_fg)
    _configure_helper(app, colors, panel_text, panel2_text, hint_fg)

def _configure_base_styles(
    app,
    style: ttk.Style,
    colors: dict,
    panel_text: str,
    panel2_text: str,
    bg_hint_fg: str,
    entry_fg: str,
    entry_disabled_bg: str,
    entry_disabled_fg: str,
    selection_bg: str,
    selection_fg: str,
) -> None:
    style.configure(".", background=colors["bg"], foreground=colors["text"])
    style.configure("TFrame", background=colors["bg"])
    style.configure("TLabel", background=colors["bg"], foreground=colors["text"])
    style.configure("TLabelframe", background=colors["bg"], foreground=colors["text"])
    style.configure("TLabelframe.Label", background=colors["bg"], foreground=colors["text"])
    style.configure("DialogPanel.TFrame", background=colors["panel"])
    style.configure("DialogPanel.TLabel", background=colors["panel"], foreground=panel_text)
    style.configure("DialogPanel.TRadiobutton", background=colors["panel"], foreground=panel_text)
    style.map(
        "DialogPanel.TRadiobutton",
        background=[("active", colors["panel"])],
        foreground=[("disabled", bg_hint_fg), ("active", panel_text)],
    )
    style.configure("TCheckbutton", background=colors["bg"], foreground=colors["text"])
    style.map("TCheckbutton", foreground=[("disabled", bg_hint_fg)])
    style.configure("TRadiobutton", background=colors["bg"], foreground=colors["text"])
    style.map("TRadiobutton", foreground=[("disabled", bg_hint_fg)])
    style.configure("TEntry", fieldbackground=colors["entry"], foreground=entry_fg)
    style.map(
        "TEntry",
        fieldbackground=[("disabled", entry_disabled_bg), ("readonly", colors["entry"])],
        foreground=[("disabled", entry_disabled_fg), ("readonly", entry_fg)],
    )
    style.configure(
        "TCombobox",
        fieldbackground=colors["entry"],
        background=colors["entry"],
        foreground=entry_fg,
    )
    style.configure(
        "Profile.TCombobox",
        fieldbackground=colors["entry"],
        background=colors["entry"],
        foreground=entry_fg,
    )
    style.map(
        "TCombobox",
        fieldbackground=[("readonly", colors["entry"]), ("disabled", entry_disabled_bg)],
        background=[("readonly", colors["entry"]), ("disabled", entry_disabled_bg)],
        foreground=[("readonly", entry_fg), ("disabled", entry_disabled_fg)],
    )
    style.map(
        "Profile.TCombobox",
        fieldbackground=[("readonly", colors["entry"]), ("disabled", entry_disabled_bg)],
        background=[("readonly", colors["entry"]), ("disabled", entry_disabled_bg)],
        foreground=[("readonly", entry_fg), ("disabled", entry_disabled_fg)],
    )
    try:
        style.configure("TCombobox", arrowcolor=entry_fg, arrowsize=12)
        style.configure("Profile.TCombobox", arrowcolor=entry_fg, arrowsize=12)
        style.map(
            "TCombobox",
            arrowcolor=[("readonly", entry_fg), ("disabled", entry_disabled_fg)],
        )
        style.map(
            "Profile.TCombobox",
            arrowcolor=[("readonly", entry_fg), ("disabled", entry_disabled_fg)],
        )
    except Exception:
        pass

    style.configure("TSpinbox", fieldbackground=colors["entry"], foreground=entry_fg)
    style.map(
        "TSpinbox",
        fieldbackground=[("disabled", entry_disabled_bg)],
        foreground=[("disabled", entry_disabled_fg)],
    )

    try:
        app.root.option_add("*TCombobox*Listbox.background", colors["entry"])
        app.root.option_add("*TCombobox*Listbox.foreground", entry_fg)
        app.root.option_add("*TCombobox*Listbox.selectBackground", selection_bg)
        app.root.option_add("*TCombobox*Listbox.selectForeground", selection_fg)
    except Exception:
        pass

    style.configure(
        "Treeview",
        background=colors["entry"],
        fieldbackground=colors["entry"],
        foreground=entry_fg,
        bordercolor=colors.get("border", colors["panel2"]),
    )
    style.configure("Treeview.Heading", background=colors["panel2"], foreground=panel2_text)
    style.map(
        "Treeview",
        background=[("selected", selection_bg)],
        foreground=[("selected", selection_fg)],
    )


def _configure_button_styles(app, style: ttk.Style, colors: dict, button_colors: dict) -> None:
    secondary_bg = button_colors.get("secondary", colors["panel"])
    if app.prefs.get("mode") == "dark" and secondary_bg in ("#ffffff", "white"):
        secondary_bg = colors["panel"]
    secondary_palette = theme_service.button_palette(secondary_bg, colors["bg"], colors["text"])
    _configure_button_style(style, "TButton", secondary_palette)

    toolbar_bg = button_colors.get("toolbar", secondary_bg)
    if app.prefs.get("mode") == "dark" and toolbar_bg in ("#ffffff", "white"):
        toolbar_bg = colors["panel"]
    toolbar_palette = theme_service.button_palette(toolbar_bg, colors["bg"], colors["text"])
    _configure_button_style(style, "Toolbar.TButton", toolbar_palette)

    primary_bg = button_colors.get("primary", DEFAULT_BUTTON_COLORS["primary"])
    primary_palette = theme_service.button_palette(primary_bg, colors["bg"], "#ffffff")
    _configure_button_style(style, "Primary.TButton", primary_palette)

    danger_bg = button_colors.get("danger", DEFAULT_BUTTON_COLORS["danger"])
    danger_palette = theme_service.button_palette(danger_bg, colors["bg"], "#ffffff")
    _configure_button_style(style, "Danger.TButton", danger_palette)


def _configure_profile_dropdown_style(
    app,
    style: ttk.Style,
    colors: dict,
    button_colors: dict,
    entry_fg: str,
    entry_disabled_bg: str,
    entry_disabled_fg: str,
) -> None:
    arrow_bg = button_colors.get("secondary", colors["panel"])
    if app.prefs.get("mode") == "dark" and arrow_bg in ("#ffffff", "white"):
        arrow_bg = colors["panel"]
    arrow_palette = theme_service.button_palette(
        arrow_bg,
        colors["bg"],
        colors["text"],
    )
    style.configure(
        "Profile.TCombobox",
        fieldbackground=colors["entry"],
        background=arrow_palette["bg"],
        foreground=entry_fg,
        bordercolor=arrow_palette["border"],
        darkcolor=arrow_palette["border"],
        lightcolor=colors["entry"],
        arrowcolor=arrow_palette["fg"],
        arrowsize=13,
        padding=(8, 5),
    )
    style.map(
        "Profile.TCombobox",
        fieldbackground=[
            ("disabled", entry_disabled_bg),
            ("readonly", colors["entry"]),
        ],
        background=[
            ("disabled", arrow_palette["disabled_bg"]),
            ("active", arrow_palette["active_bg"]),
            ("readonly", arrow_palette["bg"]),
        ],
        foreground=[
            ("disabled", entry_disabled_fg),
            ("readonly", entry_fg),
        ],
        arrowcolor=[
            ("disabled", arrow_palette["disabled_fg"]),
            ("active", arrow_palette["active_fg"]),
            ("readonly", arrow_palette["fg"]),
        ],
    )


def _configure_button_style(style: ttk.Style, style_name: str, palette: dict) -> None:
    style.configure(
        style_name,
        background=palette["bg"],
        foreground=palette["fg"],
        bordercolor=palette["border"],
        darkcolor=palette["border"],
        lightcolor=palette["active_bg"],
        focuscolor=palette["focus"],
    )
    style.map(
        style_name,
        background=[("disabled", palette["disabled_bg"]), ("active", palette["active_bg"])],
        foreground=[("disabled", palette["disabled_fg"]), ("active", palette["active_fg"])],
    )


def _configure_notebook_styles(
    style: ttk.Style, colors: dict, panel_text: str, panel2_text: str
) -> None:
    style.configure("TNotebook", background=colors["bg"])
    style.configure("TNotebook.Tab", background=colors["panel"], foreground=panel_text)
    style.map(
        "TNotebook.Tab",
        background=[("selected", colors["panel2"]), ("active", colors["panel2"])],
        foreground=[("selected", panel2_text), ("active", panel2_text)],
    )

def _configure_root_surfaces(app, colors: dict) -> None:
    app.root.configure(bg=colors["bg"])
    app.body.set_canvas_bg(colors["bg"])
    for frame_name in (
        "workspace",
        "left_sidebar",
        "editor_workspace",
        "right_sidebar",
    ):
        frame = getattr(app, frame_name, None)
        if frame is not None:
            try:
                frame.configure(bg=colors["bg"])
            except Exception:
                pass


def _configure_status_bar(app, colors: dict) -> None:
    try:
        footer_bg = colors["panel"]
        status_bg = colors["panel2"]
        status_fg = theme_service.ensure_text_contrast(
            status_bg, preferred=colors["text"], minimum=4.5
        )
        app.footer.configure(
            bg=footer_bg,
            highlightbackground=colors["border"],
            highlightcolor=colors["border"],
        )
        app.bottom_bar.configure(bg=footer_bg)
        app.action_row.configure(bg=footer_bg)
        app.status_frame.configure(
            bg=status_bg,
            highlightbackground=colors["border"],
            highlightcolor=colors["border"],
        )
        app.status_label.configure(bg=status_bg, fg=status_fg, font=FONT_STATUS)
    except Exception:
        pass


def _configure_context_menu(app, colors: dict, panel_text: str, hint_fg: str) -> None:
    menu_bg = colors["panel"]
    menu_active_bg = theme_service.blend_colors(colors["panel2"], colors["accent"], 0.18)
    menu_active_fg = theme_service.ensure_text_contrast(
        menu_active_bg, preferred=colors["text"], minimum=4.5
    )
    try:
        app._ctx_menu.configure(
            bg=menu_bg,
            fg=panel_text,
            activebackground=menu_active_bg,
            activeforeground=menu_active_fg,
            disabledforeground=hint_fg,
            bd=1,
            relief="solid",
        )
    except Exception:
        pass


def _configure_header(app, style: ttk.Style, colors: dict, button_colors: dict) -> None:
    header_bg = button_colors.get(
        "header",
        button_colors.get("primary", DEFAULT_BUTTON_COLORS["header"]),
    )
    header_palette = theme_service.button_palette(header_bg, colors["bg"], colors["text"])
    header_fg = header_palette["fg"]
    border_target = (
        "#ffffff" if theme_service.relative_luminance(header_bg) < 0.45 else "#000000"
    )
    header_border = theme_service.blend_colors(header_bg, border_target, 0.16)
    action_target = (
        "#ffffff" if theme_service.relative_luminance(header_bg) < 0.45 else "#000000"
    )
    action_bg = theme_service.blend_colors(header_bg, action_target, 0.10)
    action_palette = theme_service.button_palette(action_bg, header_bg, header_fg)
    subtitle_fg = theme_service.ensure_text_contrast(
        header_bg,
        preferred=theme_service.blend_colors(header_fg, header_bg, 0.35),
        minimum=3.2,
    )
    app.header.configure(
        bg=header_bg,
        highlightbackground=header_border,
        highlightcolor=header_border,
    )
    app.header_brand.configure(bg=header_bg)
    app.header_titles.configure(bg=header_bg)
    app.header_actions.configure(bg=header_bg)
    app.header_mark.configure(bg=header_bg, fg=header_fg)
    app.header_title.configure(bg=header_bg, fg=header_fg)
    app.header_subtitle.configure(bg=header_bg, fg=subtitle_fg)
    _configure_button_style(style, "Header.TButton", action_palette)
    app.btn_dark.configure(
        text=("Light Mode" if app.prefs.get("mode") == "dark" else "Dark Mode")
    )


def _configure_profile_controls(
    app, colors: dict, panel_text: str, panel2_text: str, hint_fg: str
) -> None:
    try:
        panel_bg = colors["panel"]
        footer_bg = colors["panel2"]
        for frame in (
            app.profile_panel,
            app.profile_target_group,
            app.profile_combo_wrap,
            app.profile_export_group,
            app.profile_export_row,
            app.profile_export_actions,
        ):
            frame.configure(bg=panel_bg)
        app.profile_panel.configure(
            highlightbackground=colors["border"],
            highlightcolor=colors["border"],
        )
        for title in (app.profile_target_title, app.profile_export_title):
            title.configure(bg=panel_bg, fg=panel_text, font=FONT_PANEL_TITLE)
        for hint in (app.profile_target_hint, app.profile_export_hint):
            hint.configure(bg=panel_bg, fg=hint_fg)
        app.profile_footer.configure(bg=footer_bg)
        app.info_label.configure(
            bg=footer_bg,
            fg=panel2_text,
            highlightbackground=colors["border"],
            highlightcolor=colors["border"],
        )
    except Exception:
        pass


def _configure_editor(app, colors: dict, selection_bg: str, selection_fg: str) -> None:
    editor_panel_fg = theme_service.ensure_text_contrast(
        colors["panel"], preferred=colors["text"], minimum=4.5
    )
    try:
        style = ttk.Style(app.root)
        app.editor_panel.configure(
            bg=colors["panel"],
            highlightbackground=colors["border"],
            highlightcolor=colors["border"],
        )
        for frame in (app.editor_header, app.editor_toolbar):
            frame.configure(bg=colors["panel"])
        app.editor_title.configure(
            bg=colors["panel"], fg=editor_panel_fg, font=FONT_PANEL_TITLE
        )
        app.editor_frame.configure(
            bg=colors["editor_bg"],
            highlightbackground=colors["border"],
            highlightcolor=colors["border"],
        )
        style.configure(
            "Editor.TCheckbutton",
            background=colors["panel"],
            foreground=editor_panel_fg,
        )
        style.map(
            "Editor.TCheckbutton",
            background=[("active", colors["panel"])],
            foreground=[("disabled", editor_panel_fg), ("active", editor_panel_fg)],
        )
    except Exception:
        pass
    app.editor.configure(
        bg=colors["editor_bg"],
        fg=colors["editor_fg"],
        insertbackground=colors["editor_fg"],
        selectbackground=selection_bg,
        selectforeground=selection_fg,
        font=(FONT_BODY_FAMILY, int(app.prefs.get("editor_font_size", 11) or 11)),
    )


def _configure_helper(
    app, colors: dict, panel_text: str, panel2_text: str, hint_fg: str
) -> None:
    try:
        helper_font = str(app.prefs.get("helper_font_family") or FONT_BODY_FAMILY)
        app.helper.configure(
            bg=colors["panel"],
            highlightbackground=colors["border"],
            highlightcolor=colors["border"],
        )
        for frame in (app.helper_header, app._path_preview_frame):
            frame.configure(bg=colors["panel"])
        app.helper_title.configure(
            bg=colors["panel"], fg=panel_text, font=FONT_PANEL_TITLE
        )
        app.helper_subtitle.configure(bg=colors["panel"], fg=hint_fg)
        app._helper_card.configure(
            bg=colors["panel2"],
            highlightbackground=colors["border"],
            highlightcolor=colors["border"],
        )
        app._helper_card_title.configure(
            bg=colors["panel2"], fg=panel2_text, font=FONT_PANEL_TITLE
        )
        app._helper_display.configure(
            bg=colors["panel2"], fg=panel2_text, font=(helper_font, FONT_BODY[1])
        )
        for card in (
            app._atmo_layout,
            app._switch_layout,
            app._titleid_layout,
            app._retro_layout,
            app._generic_layout,
        ):
            card.configure(
                bg=colors["panel"],
                highlightbackground=colors["border"],
                highlightcolor=colors["border"],
            )
        for subframe in (
            app._atmo_path_row,
            app._switch_layout_template_frame,
            app._switch_inputs,
            app._titleid_template_frame,
            app._titleid_inputs,
            app._retro_layout_template_frame,
            app._retro_inputs,
            app._generic_layout_template_frame,
        ):
            template_frames = (
                app._atmo_path_row,
                app._switch_layout_template_frame,
                app._titleid_template_frame,
                app._retro_layout_template_frame,
                app._generic_layout_template_frame,
            )
            subframe.configure(
                bg=colors["panel2"] if subframe in template_frames else colors["panel"]
            )
        for heading in (
            app._atmo_title,
            app._switch_layout_heading,
            app._titleid_layout_heading,
            app._retro_layout_heading,
            app._generic_layout_heading,
        ):
            heading.configure(bg=colors["panel"], fg=panel_text)
        app._path_preview_title.configure(
            bg=colors["panel"], fg=panel_text, font=FONT_PANEL_TITLE
        )
        app._path_preview_label.configure(
            bg=colors["panel2"],
            fg=panel2_text,
            highlightbackground=colors["border"],
            highlightcolor=colors["border"],
        )
        for hint in (
            app._atmo_hint,
            app._atmo_path_note,
            app._switch_layout_hint,
            app._switch_layout_note_label,
            app._titleid_hint,
            app._titleid_note_label,
            app._retro_layout_hint,
            app._retro_layout_note_label,
            app._generic_layout_hint,
            app._generic_layout_note_label,
        ):
            hint.configure(bg=colors["panel"], fg=hint_fg)
        for template_label in (
            app._switch_layout_template_label,
            app._titleid_template_label,
            app._retro_layout_template_label,
            app._generic_layout_template_label,
        ):
            template_label.configure(bg=colors["panel2"], fg=panel2_text, font=FONT_CODE_BOLD)
        for widget in (app._atmo_prefix_1, app._atmo_prefix_2, app._atmo_suffix):
            widget.configure(bg=colors["panel2"], fg=panel2_text, font=FONT_CODE_BOLD)
        for widget in (
            app._switch_tid_title,
            app._switch_bid_title,
            app._titleid_label,
            app._core_label,
        ):
            widget.configure(bg=colors["panel"], fg=panel_text)
        app._on_helper_configure()
    except Exception:
        pass
