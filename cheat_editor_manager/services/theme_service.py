from __future__ import annotations

import re
from typing import Optional

from ..constants import DEFAULT_BUTTON_COLORS, DEFAULT_THEME_DARK, DEFAULT_THEME_LIGHT


def effective_colors(prefs: dict) -> dict:
    defaults = dict(DEFAULT_THEME_DARK if prefs.get("mode") == "dark" else DEFAULT_THEME_LIGHT)
    base = dict(defaults)
    if prefs.get("custom_theme_enabled"):
        base.update(prefs.get("custom_theme", {}))
    return sanitize_theme_colors(base, defaults)


def normalize_hex_color(value: str, fallback: str = "#000000") -> str:
    raw = (value or "").strip()
    if re.fullmatch(r"#[0-9a-fA-F]{6}", raw):
        return raw.lower()
    return fallback.lower()


def relative_luminance(color: str) -> float:
    value = normalize_hex_color(color, "#000000").lstrip("#")
    rgb = [int(value[i:i + 2], 16) / 255.0 for i in (0, 2, 4)]
    def _linear(channel: float) -> float:
        return channel / 12.92 if channel <= 0.04045 else ((channel + 0.055) / 1.055) ** 2.4
    r, g, b = (_linear(channel) for channel in rgb)
    return (0.2126 * r) + (0.7152 * g) + (0.0722 * b)


def contrast_ratio(fg: str, bg: str) -> float:
    light = max(relative_luminance(fg), relative_luminance(bg))
    dark = min(relative_luminance(fg), relative_luminance(bg))
    return (light + 0.05) / (dark + 0.05)


def blend_colors(start: str, end: str, amount: float) -> str:
    start = normalize_hex_color(start, "#000000").lstrip("#")
    end = normalize_hex_color(end, "#000000").lstrip("#")
    amount = max(0.0, min(1.0, float(amount)))
    out = []
    for idx in (0, 2, 4):
        s = int(start[idx:idx + 2], 16)
        e = int(end[idx:idx + 2], 16)
        out.append(f"{round(s + ((e - s) * amount)):02x}")
    return f"#{''.join(out)}"


def ensure_text_contrast(bg: str, *, preferred: Optional[str] = None, light: str = "#fff8eb", dark: str = "#231b15", minimum: float = 4.5) -> str:
    bg = normalize_hex_color(bg, "#ffffff")
    candidates = []
    if preferred:
        candidates.append(normalize_hex_color(preferred, dark if relative_luminance(bg) >= 0.5 else light))
    for candidate in (light, dark, "#ffffff", "#000000"):
        normalized = normalize_hex_color(candidate, dark)
        if normalized not in candidates:
            candidates.append(normalized)
    if candidates and contrast_ratio(candidates[0], bg) >= minimum:
        return candidates[0]
    return max(candidates, key=lambda candidate: contrast_ratio(candidate, bg))


def selection_palette(accent: str, preferred_text: str = "#ffffff") -> tuple[str, str]:
    bg = normalize_hex_color(accent, DEFAULT_BUTTON_COLORS["primary"])
    fg = ensure_text_contrast(bg, preferred=preferred_text, minimum=4.5)
    return bg, fg


def button_palette(bg: str, surface_bg: str, preferred_text: str, *, minimum: float = 4.5, disabled_minimum: float = 3.0) -> dict:
    bg = normalize_hex_color(bg, surface_bg)
    surface_bg = normalize_hex_color(surface_bg, bg)
    fg = ensure_text_contrast(bg, preferred=preferred_text, minimum=minimum)
    active_target = "#ffffff" if relative_luminance(bg) < 0.45 else "#000000"
    active_bg = blend_colors(bg, active_target, 0.14)
    active_fg = ensure_text_contrast(active_bg, preferred=fg, minimum=minimum)
    disabled_bg = blend_colors(bg, surface_bg, 0.42)
    disabled_pref = blend_colors(fg, surface_bg, 0.45)
    disabled_fg = ensure_text_contrast(disabled_bg, preferred=disabled_pref, minimum=disabled_minimum)
    border_target = "#000000" if relative_luminance(bg) >= 0.55 else "#ffffff"
    border = blend_colors(bg, border_target, 0.22)
    if contrast_ratio(border, surface_bg) < 1.25:
        border = blend_colors(surface_bg, fg, 0.3)
    focus = blend_colors(bg, fg, 0.55)
    return {"bg": bg, "fg": fg, "active_bg": active_bg, "active_fg": active_fg, "disabled_bg": disabled_bg, "disabled_fg": disabled_fg, "border": border, "focus": focus}


def sanitize_theme_colors(colors: dict, defaults: dict) -> dict:
    fixed = {key: normalize_hex_color(colors.get(key, value), value) for key, value in defaults.items()}
    fixed["text"] = ensure_text_contrast(fixed["bg"], preferred=fixed["text"], minimum=4.5)
    fixed["muted"] = ensure_text_contrast(fixed["panel"], preferred=fixed["muted"], minimum=3.4)
    fixed["editor_fg"] = ensure_text_contrast(fixed["editor_bg"], preferred=fixed["editor_fg"], minimum=4.5)
    if contrast_ratio(fixed["panel2"], fixed["panel"]) < 1.08:
        shift = "#000000" if relative_luminance(fixed["panel"]) >= 0.55 else "#ffffff"
        fixed["panel2"] = blend_colors(fixed["panel"], shift, 0.08)
    if contrast_ratio(fixed["entry"], fixed["panel"]) < 1.08:
        shift = "#000000" if relative_luminance(fixed["panel"]) >= 0.55 else "#ffffff"
        fixed["entry"] = blend_colors(fixed["panel"], shift, 0.06)
    if contrast_ratio(fixed["border"], fixed["bg"]) < 1.2 and contrast_ratio(fixed["border"], fixed["panel"]) < 1.2:
        fixed["border"] = blend_colors(fixed["bg"], fixed["text"], 0.32)
    if contrast_ratio(fixed["accent"], fixed["bg"]) < 2.2:
        shift = "#000000" if relative_luminance(fixed["bg"]) >= 0.55 else "#ffffff"
        fixed["accent"] = blend_colors(fixed["accent"], shift, 0.22)
    return fixed
