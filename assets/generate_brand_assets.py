from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parent
APP_NAME = "Cheat Editor Manager Tool"
TAGLINE = "Retro-ready cheat editing and export"
COLORS = {
    "ink": (19, 16, 13, 255),
    "shell": (43, 35, 29, 255),
    "shell_hi": (70, 60, 49, 255),
    "screen": (244, 228, 195, 255),
    "screen_shadow": (212, 191, 154, 255),
    "accent": (202, 76, 45, 255),
    "accent_hi": (237, 142, 62, 255),
    "mint": (119, 216, 170, 255),
    "sand": (236, 218, 185, 255),
    "border": (106, 82, 63, 255),
    "paper": (250, 243, 225, 255),
}


def load_font(size: int, *, bold: bool = False):
    candidates = []
    if bold:
        candidates.extend([
            r"C:\Windows\Fonts\bahnschrift.ttf",
            r"C:\Windows\Fonts\segoeuib.ttf",
            r"C:\Windows\Fonts\consolab.ttf",
            r"C:\Windows\Fonts\courbd.ttf",
        ])
    else:
        candidates.extend([
            r"C:\Windows\Fonts\bahnschrift.ttf",
            r"C:\Windows\Fonts\segoeui.ttf",
            r"C:\Windows\Fonts\consola.ttf",
            r"C:\Windows\Fonts\cour.ttf",
        ])
    for candidate in candidates:
        path = Path(candidate)
        if path.exists():
            try:
                return ImageFont.truetype(str(path), size=size)
            except Exception:
                continue
    return ImageFont.load_default()


def draw_dpad(draw: ImageDraw.ImageDraw, origin: tuple[int, int], size: int, color: tuple[int, int, int, int]):
    x, y = origin
    arm = size // 3
    draw.rounded_rectangle((x + arm, y, x + arm * 2, y + size), radius=arm // 2, fill=color)
    draw.rounded_rectangle((x, y + arm, x + size, y + arm * 2), radius=arm // 2, fill=color)


def draw_console_mark(size: int) -> Image.Image:
    canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(canvas)
    pad = int(size * 0.08)
    shadow = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    sdraw = ImageDraw.Draw(shadow)
    sdraw.rounded_rectangle(
        (pad, pad + int(size * 0.04), size - pad, size - pad + int(size * 0.04)),
        radius=int(size * 0.16),
        fill=(0, 0, 0, 120),
    )
    shadow = shadow.filter(ImageFilter.GaussianBlur(radius=max(4, size // 42)))
    canvas.alpha_composite(shadow)

    body = (pad, pad, size - pad, size - pad)
    draw.rounded_rectangle(body, radius=int(size * 0.16), fill=COLORS["shell"], outline=COLORS["border"], width=max(2, size // 64))
    draw.rounded_rectangle(
        (pad + int(size * 0.03), pad + int(size * 0.03), size - pad - int(size * 0.03), pad + int(size * 0.18)),
        radius=int(size * 0.1),
        fill=COLORS["accent"],
    )
    draw.rectangle(
        (pad + int(size * 0.09), pad + int(size * 0.12), size - pad - int(size * 0.09), pad + int(size * 0.145)),
        fill=COLORS["accent_hi"],
    )

    bezel = (pad + int(size * 0.16), pad + int(size * 0.2), size - pad - int(size * 0.16), pad + int(size * 0.5))
    draw.rounded_rectangle(bezel, radius=int(size * 0.06), fill=COLORS["ink"])
    screen = (bezel[0] + int(size * 0.03), bezel[1] + int(size * 0.03), bezel[2] - int(size * 0.03), bezel[3] - int(size * 0.03))
    draw.rounded_rectangle(screen, radius=int(size * 0.04), fill=COLORS["screen"], outline=COLORS["screen_shadow"], width=max(1, size // 96))

    font_code = load_font(max(18, size // 10), bold=True)
    font_mini = load_font(max(12, size // 18), bold=False)
    draw.text((screen[0] + int(size * 0.03), screen[1] + int(size * 0.025)), "[ ]", font=font_code, fill=COLORS["mint"])
    draw.text((screen[0] + int(size * 0.05), screen[1] + int(size * 0.12)), "0400 0000", font=font_mini, fill=COLORS["ink"])
    draw.text((screen[0] + int(size * 0.05), screen[1] + int(size * 0.16)), "0000 0063", font=font_mini, fill=COLORS["accent"])
    cursor_x = screen[2] - int(size * 0.11)
    draw.rounded_rectangle((cursor_x, screen[1] + int(size * 0.07), cursor_x + int(size * 0.015), screen[3] - int(size * 0.07)), radius=2, fill=COLORS["accent_hi"])

    dpad_size = int(size * 0.14)
    draw_dpad(draw, (pad + int(size * 0.18), pad + int(size * 0.62)), dpad_size, COLORS["sand"])
    btn_r = int(size * 0.045)
    bx = size - pad - int(size * 0.27)
    by = pad + int(size * 0.68)
    draw.ellipse((bx, by, bx + btn_r * 2, by + btn_r * 2), fill=COLORS["accent_hi"])
    draw.ellipse((bx + int(size * 0.08), by - int(size * 0.06), bx + int(size * 0.08) + btn_r * 2, by - int(size * 0.06) + btn_r * 2), fill=COLORS["accent"])
    for dx in (int(size * 0.34), int(size * 0.41), int(size * 0.48)):
        draw.rounded_rectangle((pad + dx, pad + int(size * 0.77), pad + dx + int(size * 0.04), pad + int(size * 0.79)), radius=3, fill=COLORS["shell_hi"])

    pen = [
        (screen[2] - int(size * 0.19), screen[3] - int(size * 0.02)),
        (screen[2] - int(size * 0.13), screen[3] + int(size * 0.04)),
        (screen[2] - int(size * 0.06), screen[3] - int(size * 0.03)),
        (screen[2] - int(size * 0.12), screen[3] - int(size * 0.09)),
    ]
    draw.polygon(pen, fill=COLORS["accent_hi"])
    draw.polygon([pen[2], (pen[2][0] + int(size * 0.025), pen[2][1] - int(size * 0.025)), pen[3]], fill=COLORS["paper"])
    return canvas


def make_logo_wide(mark: Image.Image, width: int, height: int, watermark: bool = False) -> Image.Image:
    canvas = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(canvas)
    mark_size = int(height * 0.8)
    mark_img = mark.resize((mark_size, mark_size), Image.Resampling.LANCZOS)
    mark_y = (height - mark_size) // 2
    canvas.alpha_composite(mark_img, (int(height * 0.08), mark_y))

    title_font = load_font(max(30, height // 5), bold=True)
    subtitle_font = load_font(max(16, height // 10), bold=False)
    label_font = load_font(max(12, height // 12), bold=True)
    text_x = int(height * 0.08) + mark_size + int(height * 0.08)
    title_y = int(height * 0.18)
    subtitle_y = title_y + int(height * 0.33)
    label_y = subtitle_y + int(height * 0.26)

    if watermark:
        title_fill = (244, 228, 195, 40)
        subtitle_fill = (237, 142, 62, 32)
        label_fill = (119, 216, 170, 28)
        chip_fill = (202, 76, 45, 36)
    else:
        title_fill = COLORS["paper"]
        subtitle_fill = COLORS["accent_hi"]
        label_fill = COLORS["paper"]
        chip_fill = COLORS["accent"]

    draw.text((text_x, title_y), APP_NAME, font=title_font, fill=title_fill)
    draw.text((text_x, subtitle_y), TAGLINE, font=subtitle_font, fill=subtitle_fill)
    chip_box = (text_x, label_y, min(width - int(height * 0.08), text_x + int(width * 0.46)), label_y + int(height * 0.16))
    draw.rounded_rectangle(chip_box, radius=12, fill=chip_fill)
    draw.text((text_x + int(height * 0.04), label_y + int(height * 0.025)), "SWITCH | RETROARCH | EMULATORS", font=label_font, fill=label_fill)
    return canvas


def make_watermark(mark: Image.Image) -> Image.Image:
    watermark = make_logo_wide(mark, 1400, 360, watermark=True)
    glow = Image.new("RGBA", watermark.size, (0, 0, 0, 0))
    gdraw = ImageDraw.Draw(glow)
    gdraw.rounded_rectangle((0, 40, watermark.width, watermark.height - 40), radius=60, fill=(237, 142, 62, 10))
    glow = glow.filter(ImageFilter.GaussianBlur(24))
    return Image.alpha_composite(glow, watermark)


def save_png(path: Path, image: Image.Image):
    image.save(path, format="PNG")


def main() -> None:
    mark_master = draw_console_mark(1024)
    save_png(ROOT / "icon-master.png", mark_master)
    save_png(ROOT / "icon-256.png", mark_master.resize((256, 256), Image.Resampling.LANCZOS))
    save_png(ROOT / "mark-48.png", mark_master.resize((48, 48), Image.Resampling.LANCZOS))
    save_png(ROOT / "mark-96.png", mark_master.resize((96, 96), Image.Resampling.LANCZOS))
    save_png(ROOT / "logo-header.png", make_logo_wide(mark_master, 920, 220))
    save_png(ROOT / "logo-wide.png", make_logo_wide(mark_master, 1280, 320))
    save_png(ROOT / "watermark-ui.png", make_logo_wide(mark_master, 560, 160, watermark=True))
    save_png(ROOT / "watermark.png", make_watermark(mark_master))

    icon = mark_master.resize((256, 256), Image.Resampling.LANCZOS)
    icon.save(
        ROOT / "app-icon.ico",
        format="ICO",
        sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)],
    )

    (ROOT / "README.md").write_text(
        "# Brand Assets\n\n"
        "Generated retro-console branding for Cheat Editor Manager Tool.\n\n"
        "Files:\n"
        "- `app-icon.ico`: Windows executable icon\n"
        "- `icon-256.png`: app icon image\n"
        "- `mark-48.png`: compact UI mark\n"
        "- `logo-header.png`: header and hero logo\n"
        "- `logo-wide.png`: wide wordmark\n"
        "- `watermark-ui.png`: compact translucent watermark for the app UI\n"
        "- `watermark.png`: large translucent watermark panel art\n"
        "- `generate_brand_assets.py`: source generator\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()


