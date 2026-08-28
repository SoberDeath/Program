from pathlib import Path

from PIL import Image, ImageDraw

OUT_DIR = Path("assets")
OUT_DIR.mkdir(exist_ok=True)

TRANSPARENT = (0, 0, 0, 0)
BG = (7, 12, 20, 255)
CYAN = (48, 221, 230, 255)
CYAN_DARK = (17, 92, 108, 255)
WHITE = (238, 251, 252, 255)


def _scale(value: float, size: int) -> int:
    return max(1, round(value * size))


def draw_icon(size: int) -> Image.Image:
    """Render the icon natively at *size* instead of downscaling one master.

    Windows uses very small 16/20/24/32 px icon frames in title bars and the
    taskbar. Native rendering keeps edges aligned to actual pixels and avoids
    the blurry/dirty appearance caused by shrinking complex 1024 px artwork.
    """
    img = Image.new("RGBA", (size, size), TRANSPARENT)
    d = ImageDraw.Draw(img)

    pad = _scale(0.06, size)
    radius = _scale(0.21, size)
    d.rounded_rectangle((pad, pad, size - pad - 1, size - pad - 1), radius=radius, fill=BG)

    # Minimal cyan top-left launcher notch. It gives the tile a recognizable
    # AppManager silhouette without adding noisy detail at 16 px.
    notch = _scale(0.22, size)
    d.polygon(
        [
            (pad, pad + notch),
            (pad, pad + _scale(0.13, size)),
            (pad + _scale(0.13, size), pad),
            (pad + notch, pad),
        ],
        fill=CYAN,
    )

    # Main mark: a single stylised "A"/launch glyph. One bold symbol is much
    # more legible in the Windows title bar than the previous AM monogram.
    left = _scale(0.25, size)
    right = _scale(0.75, size)
    top = _scale(0.22, size)
    bottom = _scale(0.76, size)
    mid = size // 2
    stroke = max(2, _scale(0.105 if size >= 32 else 0.12, size))

    d.line((left, bottom, mid, top), fill=CYAN, width=stroke)
    d.line((mid, top, right, bottom), fill=WHITE, width=stroke)

    cross_y = _scale(0.57, size)
    cross_left = _scale(0.36, size)
    cross_right = _scale(0.64, size)
    cross_h = max(2, _scale(0.075, size))
    d.rounded_rectangle(
        (cross_left, cross_y, cross_right, cross_y + cross_h),
        radius=max(1, cross_h // 3),
        fill=CYAN,
    )

    # Small terminal/status bar at larger sizes only. It is intentionally
    # omitted below 32 px to keep the tiny frames clean.
    if size >= 32:
        bar_w = _scale(0.22, size)
        bar_h = max(2, _scale(0.045, size))
        bar_x = size - pad - _scale(0.14, size) - bar_w
        bar_y = size - pad - _scale(0.13, size)
        d.rounded_rectangle(
            (bar_x, bar_y, bar_x + bar_w, bar_y + bar_h),
            radius=max(1, bar_h // 2),
            fill=CYAN_DARK if size < 64 else CYAN,
        )

    return img


# Native frames used by Windows Explorer, title bars and taskbar.
sizes = [16, 20, 24, 32, 40, 48, 64, 96, 128, 192, 256]
frames = [draw_icon(size) for size in sizes]

# 1024px PNG for tray/UI previews and future packaging assets.
png = draw_icon(1024)
png.save(OUT_DIR / "appmanager.png", optimize=True)

# Store each native-size frame in the .ico so Windows does not have to rescale
# a mismatched bitmap. Use the largest frame as the base ICO image.
frames[-1].save(
    OUT_DIR / "appmanager.ico",
    format="ICO",
    append_images=frames[:-1],
    sizes=[(size, size) for size in sizes],
)

# Also write individual PNG frames for visual debugging if needed.
preview_dir = OUT_DIR / "icon_sizes"
preview_dir.mkdir(exist_ok=True)
for size, frame in zip(sizes, frames):
    frame.save(preview_dir / f"appmanager_{size}.png", optimize=True)

print("Generated AppManager Windows icon set")
print("  assets/appmanager.ico")
print("  assets/appmanager.png")
print("  assets/icon_sizes/appmanager_16.png ... appmanager_256.png")
