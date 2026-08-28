from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

SIZE = 512
OUT_DIR = Path("assets")
OUT_DIR.mkdir(exist_ok=True)

img = Image.new("RGBA", (SIZE, SIZE), (10, 14, 20, 255))
draw = ImageDraw.Draw(img)

# Neon cyan terminal-inspired icon: rounded square, inner frame, and AM monogram.
cyan = (88, 210, 212, 255)
dim = (35, 95, 103, 255)
white = (230, 246, 246, 255)

pad = 34
draw.rounded_rectangle((pad, pad, SIZE - pad, SIZE - pad), radius=72, outline=cyan, width=18)
draw.rounded_rectangle((pad + 28, pad + 28, SIZE - pad - 28, SIZE - pad - 28), radius=52, outline=dim, width=5)

# Draw a clean geometric AM mark without external font files.
# A
x0, y0 = 120, 150
x1, y1 = 246, 360
draw.line((x0, y1, (x0 + x1) // 2, y0), fill=cyan, width=30)
draw.line(((x0 + x1) // 2, y0, x1, y1), fill=cyan, width=30)
draw.line((153, 285, 214, 285), fill=cyan, width=24)

# M
mx0, mx1 = 275, 398
my0, my1 = 160, 360
draw.line((mx0, my1, mx0, my0), fill=white, width=28)
draw.line((mx0, my0, (mx0 + mx1) // 2, 270), fill=white, width=28)
draw.line(((mx0 + mx1) // 2, 270, mx1, my0), fill=white, width=28)
draw.line((mx1, my0, mx1, my1), fill=white, width=28)

# Small terminal cursor accent.
draw.rectangle((355, 390, 405, 408), fill=cyan)

png_path = OUT_DIR / "appmanager.png"
ico_path = OUT_DIR / "appmanager.ico"
img.save(png_path)
img.save(ico_path, sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
print(f"Generated {ico_path} and {png_path}")
