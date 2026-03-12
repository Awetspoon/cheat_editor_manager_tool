from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

APP_NAME = "Cheat Editor Manager Tool"
TAGLINE = "Retro-ready cheat editing and export"
CHANNEL_TEXT = "SWITCH  RETROARCH  EMULATORS"

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ASSETS_DIR = PROJECT_ROOT / "assets"

COLORS = {
    "bg_top": (24, 18, 14, 255),
    "bg_bottom": (54, 36, 26, 255),
    "panel": (78, 54, 38, 255),
    "panel_hi": (104, 73, 51, 255),
    "line": (146, 109, 79, 255),
    "screen": (252, 237, 201, 255),
    "screen_shadow": (217, 189, 143, 255),
    "ink": (29, 22, 17, 255),
    "accent": (232, 104, 44, 255),
    "accent_hi": (255, 174, 90, 255),
    "mint": (130, 232, 182, 255),
    "paper": (250, 240, 220, 255),
    "shadow": (0, 0, 0, 130),
}


def load_font(size: int, *, bold: bool = False, mono: bool = False) -> ImageFont.ImageFont:
    candidates: list[str] = []
    if mono:
        if bold:
            candidates.extend(
                [
                    r"C:\\Windows\\Fonts\\consolab.ttf",
                    r"C:\\Windows\\Fonts\\courbd.ttf",
                ]
            )
        else:
            candidates.extend(
                [
                    r"C:\\Windows\\Fonts\\consola.ttf",
                    r"C:\\Windows\\Fonts\\cour.ttf",
                ]
            )
    else:
        if bold:
            candidates.extend(
                [
                    r"C:\\Windows\\Fonts\\bahnschrift.ttf",
                    r"C:\\Windows\\Fonts\\segoeuib.ttf",
                    r"C:\\Windows\\Fonts\\arialbd.ttf",
                ]
            )
        else:
            candidates.extend(
                [
                    r"C:\\Windows\\Fonts\\bahnschrift.ttf",
                    r"C:\\Windows\\Fonts\\segoeui.ttf",
                    r"C:\\Windows\\Fonts\\arial.ttf",
                ]
            )

    for candidate in candidates:
        path = Path(candidate)
        if not path.exists():
            continue
        try:
            return ImageFont.truetype(str(path), size=size)
        except Exception:
            continue
    return ImageFont.load_default()


def gradient_background(size: tuple[int, int], *, translucent: bool = False) -> Image.Image:
    width, height = size
    alpha = 72 if translucent else 255
    canvas = Image.new("RGBA", size, COLORS["bg_top"][:3] + (alpha,))
    draw = ImageDraw.Draw(canvas)

    for y in range(height):
        t = y / max(1, height - 1)
        r = int(COLORS["bg_top"][0] * (1 - t) + COLORS["bg_bottom"][0] * t)
        g = int(COLORS["bg_top"][1] * (1 - t) + COLORS["bg_bottom"][1] * t)
        b = int(COLORS["bg_top"][2] * (1 - t) + COLORS["bg_bottom"][2] * t)
        draw.line((0, y, width, y), fill=(r, g, b, alpha))

    stripe_alpha = 22 if not translucent else 10
    for x in range(-height, width, 42):
        draw.line((x, 0, x + height, height), fill=(255, 255, 255, stripe_alpha), width=2)

    return canvas


def draw_dpad(draw: ImageDraw.ImageDraw, origin: tuple[int, int], size: int, color: tuple[int, int, int, int]) -> None:
    x, y = origin
    arm = max(2, size // 3)
    draw.rounded_rectangle((x + arm, y, x + arm * 2, y + size), radius=max(1, arm // 2), fill=color)
    draw.rounded_rectangle((x, y + arm, x + size, y + arm * 2), radius=max(1, arm // 2), fill=color)


def draw_mark(size: int = 1024) -> Image.Image:
    canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))

    shadow = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    sdraw = ImageDraw.Draw(shadow)
    pad = int(size * 0.08)
    sdraw.rounded_rectangle(
        (pad, pad + int(size * 0.05), size - pad, size - pad + int(size * 0.05)),
        radius=int(size * 0.16),
        fill=COLORS["shadow"],
    )
    shadow = shadow.filter(ImageFilter.GaussianBlur(max(4, size // 48)))
    canvas.alpha_composite(shadow)

    draw = ImageDraw.Draw(canvas)
    body = (pad, pad, size - pad, size - pad)
    draw.rounded_rectangle(
        body,
        radius=int(size * 0.16),
        fill=COLORS["panel"],
        outline=COLORS["line"],
        width=max(2, size // 64),
    )

    top_band = (pad + int(size * 0.03), pad + int(size * 0.03), size - pad - int(size * 0.03), pad + int(size * 0.19))
    draw.rounded_rectangle(top_band, radius=int(size * 0.1), fill=COLORS["accent"])
    draw.rectangle(
        (top_band[0] + int(size * 0.06), top_band[1] + int(size * 0.09), top_band[2] - int(size * 0.06), top_band[1] + int(size * 0.12)),
        fill=COLORS["accent_hi"],
    )

    bezel = (pad + int(size * 0.16), pad + int(size * 0.22), size - pad - int(size * 0.16), pad + int(size * 0.52))
    draw.rounded_rectangle(bezel, radius=int(size * 0.06), fill=COLORS["ink"])
    screen = (
        bezel[0] + int(size * 0.03),
        bezel[1] + int(size * 0.03),
        bezel[2] - int(size * 0.03),
        bezel[3] - int(size * 0.03),
    )
    draw.rounded_rectangle(
        screen,
        radius=int(size * 0.04),
        fill=COLORS["screen"],
        outline=COLORS["screen_shadow"],
        width=max(1, size // 96),
    )

    title_font = load_font(max(20, size // 10), bold=True, mono=True)
    code_font = load_font(max(12, size // 20), mono=True)
    draw.text((screen[0] + int(size * 0.03), screen[1] + int(size * 0.02)), "[Infinite HP]", font=title_font, fill=COLORS["mint"])
    draw.text((screen[0] + int(size * 0.05), screen[1] + int(size * 0.12)), "0400 0000", font=code_font, fill=COLORS["ink"])
    draw.text((screen[0] + int(size * 0.05), screen[1] + int(size * 0.16)), "0000 0063", font=code_font, fill=COLORS["accent"])

    cursor_x = screen[2] - int(size * 0.12)
    draw.rounded_rectangle(
        (cursor_x, screen[1] + int(size * 0.065), cursor_x + int(size * 0.014), screen[3] - int(size * 0.065)),
        radius=2,
        fill=COLORS["accent_hi"],
    )

    draw_dpad(draw, (pad + int(size * 0.19), pad + int(size * 0.64)), int(size * 0.13), COLORS["paper"])
    btn_r = int(size * 0.045)
    bx = size - pad - int(size * 0.29)
    by = pad + int(size * 0.69)
    draw.ellipse((bx, by, bx + btn_r * 2, by + btn_r * 2), fill=COLORS["accent_hi"])
    draw.ellipse((bx + int(size * 0.085), by - int(size * 0.06), bx + int(size * 0.085) + btn_r * 2, by - int(size * 0.06) + btn_r * 2), fill=COLORS["accent"])

    for dx in (int(size * 0.35), int(size * 0.42), int(size * 0.49)):
        draw.rounded_rectangle(
            (pad + dx, pad + int(size * 0.78), pad + dx + int(size * 0.04), pad + int(size * 0.8)),
            radius=3,
            fill=COLORS["panel_hi"],
        )

    pen = [
        (screen[2] - int(size * 0.2), screen[3] - int(size * 0.02)),
        (screen[2] - int(size * 0.13), screen[3] + int(size * 0.04)),
        (screen[2] - int(size * 0.06), screen[3] - int(size * 0.04)),
        (screen[2] - int(size * 0.13), screen[3] - int(size * 0.1)),
    ]
    draw.polygon(pen, fill=COLORS["accent_hi"])
    draw.polygon([pen[2], (pen[2][0] + int(size * 0.025), pen[2][1] - int(size * 0.025)), pen[3]], fill=COLORS["paper"])

    return canvas


def make_wordmark(mark: Image.Image, size: tuple[int, int], *, translucent: bool = False) -> Image.Image:
    width, height = size
    canvas = Image.new("RGBA", size, (0, 0, 0, 0))
    bg = gradient_background(size, translucent=translucent)

    if not translucent:
        canvas.alpha_composite(bg)

    mark_size = int(height * 0.75)
    mark_x = int(height * 0.1)
    mark_y = (height - mark_size) // 2
    canvas.alpha_composite(mark.resize((mark_size, mark_size), Image.Resampling.LANCZOS), (mark_x, mark_y))

    draw = ImageDraw.Draw(canvas)

    title_font = load_font(max(20, height // 5), bold=True)
    subtitle_font = load_font(max(11, height // 10), bold=False)
    chip_font = load_font(max(10, height // 12), bold=True, mono=True)

    text_x = mark_x + mark_size + int(height * 0.09)
    title_y = int(height * 0.2)
    subtitle_y = title_y + int(height * 0.32)
    chip_y = subtitle_y + int(height * 0.24)

    if translucent:
        title_fill = (250, 240, 220, 56)
        subtitle_fill = (255, 174, 90, 44)
        chip_fill = (232, 104, 44, 52)
        chip_text = (250, 240, 220, 54)
    else:
        title_fill = COLORS["paper"]
        subtitle_fill = COLORS["accent_hi"]
        chip_fill = COLORS["accent"]
        chip_text = COLORS["paper"]

    draw.text((text_x, title_y), APP_NAME, font=title_font, fill=title_fill)
    draw.text((text_x, subtitle_y), TAGLINE, font=subtitle_font, fill=subtitle_fill)

    chip_width = min(width - text_x - int(height * 0.12), int(width * 0.43))
    chip_box = (text_x, chip_y, text_x + max(120, chip_width), chip_y + int(height * 0.16))
    draw.rounded_rectangle(chip_box, radius=10, fill=chip_fill)
    draw.text((text_x + int(height * 0.03), chip_y + int(height * 0.03)), CHANNEL_TEXT, font=chip_font, fill=chip_text)

    return canvas


def make_splash(mark: Image.Image, size: tuple[int, int]) -> Image.Image:
    canvas = gradient_background(size)
    draw = ImageDraw.Draw(canvas)
    width, height = size

    orb = Image.new("RGBA", size, (0, 0, 0, 0))
    odraw = ImageDraw.Draw(orb)
    odraw.ellipse(
        (int(width * 0.52), int(height * 0.1), int(width * 1.05), int(height * 0.9)),
        fill=(255, 174, 90, 40),
    )
    orb = orb.filter(ImageFilter.GaussianBlur(max(8, width // 90)))
    canvas.alpha_composite(orb)

    wordmark = make_wordmark(mark, (int(width * 0.76), int(height * 0.32)))
    canvas.alpha_composite(wordmark, (int(width * 0.08), int(height * 0.14)))

    card = (
        int(width * 0.1),
        int(height * 0.57),
        int(width * 0.9),
        int(height * 0.86),
    )
    draw.rounded_rectangle(card, radius=28, fill=(33, 25, 19, 175), outline=(167, 129, 92, 180), width=2)

    mono = load_font(max(18, height // 26), mono=True)
    line_h = int(height * 0.055)
    lines = [
        "Profile: Atmosphere (CFW)",
        "Path: atmosphere/contents/<TID>/cheats/<BID>.txt",
        "Quick Export status: READY",
    ]
    for i, line in enumerate(lines):
        draw.text((card[0] + 28, card[1] + 20 + i * line_h), line, font=mono, fill=(250, 240, 220, 230))

    return canvas


def make_square_badge(mark: Image.Image, size: int = 1024) -> Image.Image:
    canvas = gradient_background((size, size))
    mark_size = int(size * 0.68)
    mx = (size - mark_size) // 2
    my = int(size * 0.1)
    canvas.alpha_composite(mark.resize((mark_size, mark_size), Image.Resampling.LANCZOS), (mx, my))

    draw = ImageDraw.Draw(canvas)
    title_font = load_font(max(30, size // 16), bold=True)
    subtitle_font = load_font(max(16, size // 30), bold=False)
    draw.text((int(size * 0.14), int(size * 0.8)), "Cheat Editor", font=title_font, fill=COLORS["paper"])
    draw.text((int(size * 0.14), int(size * 0.86)), "Manager Tool", font=title_font, fill=COLORS["accent_hi"])
    draw.text((int(size * 0.14), int(size * 0.93)), TAGLINE, font=subtitle_font, fill=(250, 240, 220, 210))
    return canvas


def save_png(path: Path, image: Image.Image) -> None:
    image.save(path, format="PNG")


def main() -> None:
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)

    master = draw_mark(1024)
    save_png(ASSETS_DIR / "icon-master.png", master)

    icon_sizes = [16, 32, 48, 64, 96, 128, 256, 512]
    for size in icon_sizes:
        save_png(ASSETS_DIR / f"icon-{size}.png", master.resize((size, size), Image.Resampling.LANCZOS))

    save_png(ASSETS_DIR / "icon-256.png", master.resize((256, 256), Image.Resampling.LANCZOS))
    save_png(ASSETS_DIR / "mark-48.png", master.resize((48, 48), Image.Resampling.LANCZOS))
    save_png(ASSETS_DIR / "mark-96.png", master.resize((96, 96), Image.Resampling.LANCZOS))

    save_png(ASSETS_DIR / "wordmark-360.png", make_wordmark(master, (360, 96)))
    save_png(ASSETS_DIR / "logo-header.png", make_wordmark(master, (920, 220)))
    save_png(ASSETS_DIR / "logo-wide.png", make_wordmark(master, (1280, 320)))
    save_png(ASSETS_DIR / "logo-square.png", make_square_badge(master, 1024))

    save_png(ASSETS_DIR / "watermark-ui.png", make_wordmark(master, (560, 160), translucent=True))
    save_png(ASSETS_DIR / "watermark.png", make_wordmark(master, (1400, 360), translucent=True))

    save_png(ASSETS_DIR / "splash-1366x768.png", make_splash(master, (1366, 768)))
    save_png(ASSETS_DIR / "splash-1920x1080.png", make_splash(master, (1920, 1080)))
    save_png(ASSETS_DIR / "social-card.png", make_splash(master, (1200, 630)))

    master.resize((256, 256), Image.Resampling.LANCZOS).save(
        ASSETS_DIR / "app-icon.ico",
        format="ICO",
        sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)],
    )

    (ASSETS_DIR / "README.md").write_text(
        "# Brand Assets\n\n"
        "Generated brand kit for Cheat Editor Manager Tool.\n\n"
        "Run `python assets/generate_brand_assets.py` to regenerate everything.\n\n"
        "Core runtime files used by the app:\n"
        "- `app-icon.ico`\n"
        "- `icon-256.png`\n"
        "- `mark-48.png`\n"
        "- `wordmark-360.png`\n\n"
        "Additional brand files:\n"
        "- `icon-master.png`\n"
        "- `icon-16.png`, `icon-32.png`, `icon-48.png`, `icon-64.png`, `icon-96.png`, `icon-128.png`, `icon-256.png`, `icon-512.png`\n"
        "- `mark-96.png`\n"
        "- `logo-header.png`, `logo-wide.png`, `logo-square.png`\n"
        "- `watermark-ui.png`, `watermark.png`\n"
        "- `splash-1366x768.png`, `splash-1920x1080.png`, `social-card.png`\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
