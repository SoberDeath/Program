from pathlib import Path

from PIL import Image, ImageDraw

MASTER = 1024
OUT_DIR = Path("assets")
OUT_DIR.mkdir(exist_ok=True)

TRANSPARENT = (0, 0, 0, 0)
BG = (8, 12, 19, 255)
CYAN = (54, 224, 230, 255)
CYAN_DARK = (13, 95, 108, 255)
WHITE = (235, 252, 253, 255)


def make_master() -> Image.Image:
    """Create a simple icon designed to remain readable at 16–32 px."""
    img = Image.new("RGBA", (MASTER, MASTER), TRANSPARENT)
    d = ImageDraw.Draw(img)

    # Large rounded tile. Avoid thin decorative borders: they become visual
    # noise in the Windows title bar and taskbar.
    d.rounded_rectangle((58, 58, 966, 966), radius=220, fill=BG)

    # Cyan upper-left accent gives the mark a recognizable silhouette even at
    # 16 px without depending on tiny letters.
    d.polygon([(58, 278), (58, 220), (220, 58), (278, 58)], fill=CYAN)

    # Bold stylised A / launcher chevron.
    d.polygon(
        [(205, 730), (405, 270), (485, 270), (620, 585), (535, 585),
         (445, 385), (310, 730)],
        fill=CYAN,
    )
    d.rounded_rectangle((326, 548, 536, 625), radius=28, fill=CYAN)

    # M is deliberately broad and simple. Thick strokes survive Windows icon
    # downscaling substantially better than the previous line-based monogram.
    stroke = 92
    d.rounded_rectangle((570, 320, 570 + stroke, 735), radius=30, fill=WHITE)
    d.rounded_rectangle((805, 320, 805 + stroke, 735), radius=30, fill=WHITE)
    d.polygon([(570, 320), (662, 320), (735, 490), (808, 320), (897, 320),
               (760, 615), (710, 615)], fill=WHITE)

    # Small cyan status/cursor element, intentionally chunky.
    d.rounded_rectangle((690, 790, 850, 850), radius=24, fill=CYAN)

    return img


def make_icon_frame(master: Image.Image, size: int) -> Image.Image:
    # Render from the master for each requested size. A small sharpening pass
    # would create halos, so use clean LANCZOS resampling only.
    return master.resize((size, size), Image.Resampling.LANCZOS)


master = make_master()
master.save(OUT_DIR / "appmanager.png", optimize=True)

# Explicit Windows shell/title-bar/taskbar sizes. Keeping each representation
# in the ICO prevents Windows from stretching a single low-resolution frame.
sizes = [16, 20, 24, 32, 40, 48, 64, 96, 128, 192, 256]
frames = [make_icon_frame(master, size) for size in sizes]
frames[-1].save(
    OUT_DIR / "appmanager.ico",
    format="ICO",
    append_images=frames[:-1],
    sizes=[(size, size) for size in sizes],
)

print("Generated AppManager icon:")
print("  assets/appmanager.png  1024x1024 master")
print("  assets/appmanager.ico  native Windows 16-256px frames")
