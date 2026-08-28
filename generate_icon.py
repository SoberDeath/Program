from pathlib import Path

from PIL import Image, ImageDraw

# Render at a large master resolution and downsample every Windows icon size
# independently. This keeps the title-bar/taskbar variants much sharper than
# asking Windows to scale one small bitmap.
MASTER = 1024
OUT_DIR = Path("assets")
OUT_DIR.mkdir(exist_ok=True)

BG = (7, 11, 17, 255)
PANEL = (13, 22, 31, 255)
CYAN = (54, 224, 230, 255)
CYAN_DIM = (22, 111, 122, 255)
WHITE = (225, 248, 249, 255)


def make_master() -> Image.Image:
    img = Image.new("RGBA", (MASTER, MASTER), BG)
    d = ImageDraw.Draw(img)

    # Strong silhouette first: this is what remains readable at 16x16/24x24.
    d.rounded_rectangle((70, 70, 954, 954), radius=190, fill=PANEL)
    d.rounded_rectangle((70, 70, 954, 954), radius=190, outline=CYAN, width=34)
    d.rounded_rectangle((112, 112, 912, 912), radius=150, outline=CYAN_DIM, width=10)

    # Geometric AM monogram. No font dependency, so builds are reproducible.
    # A: wide, heavy strokes with a high crossbar for small-size legibility.
    d.line((210, 720, 350, 300), fill=CYAN, width=78)
    d.line((350, 300, 490, 720), fill=CYAN, width=78)
    d.line((270, 555, 430, 555), fill=CYAN, width=62)

    # M: deliberately separated from A so the mark does not become a blob.
    d.line((555, 720, 555, 320), fill=WHITE, width=72)
    d.line((555, 320, 690, 535), fill=WHITE, width=72)
    d.line((690, 535, 825, 320), fill=WHITE, width=72)
    d.line((825, 320, 825, 720), fill=WHITE, width=72)

    # Terminal cursor is kept large enough to survive at taskbar size.
    d.rounded_rectangle((705, 785, 830, 820), radius=10, fill=CYAN)
    return img


def resized(master: Image.Image, size: int) -> Image.Image:
    return master.resize((size, size), Image.Resampling.LANCZOS)


master = make_master()
master.save(OUT_DIR / "appmanager.png", optimize=True)

# Pillow stores all requested representations inside one .ico. Including the
# intermediate sizes prevents blurry Windows title-bar/taskbar scaling.
sizes = [16, 20, 24, 32, 40, 48, 64, 96, 128, 192, 256]
frames = [resized(master, size) for size in sizes]
frames[-1].save(
    OUT_DIR / "appmanager.ico",
    format="ICO",
    append_images=frames[:-1],
    sizes=[(size, size) for size in sizes],
)

print("Generated high-resolution AppManager icon set:")
print("  assets/appmanager.png  (1024x1024 master)")
print("  assets/appmanager.ico  (16..256px Windows icon set)")
