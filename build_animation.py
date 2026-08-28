from __future__ import annotations

import os
import random
import shutil
import sys
import time

from app_version import APP_VERSION_SHORT

CYAN = "\033[96m"
BRIGHT = "\033[1;96m"
RESET = "\033[0m"
HIDE_CURSOR = "\033[?25l"
SHOW_CURSOR = "\033[?25h"
HOME = "\033[H"
CLEAR = "\033[2J"

BANNER = [
    " █████╗ ██████╗ ██████╗ ███╗   ███╗ █████╗ ███╗   ██╗ █████╗  ██████╗ ███████╗██████╗ ",
    "██╔══██╗██╔══██╗██╔══██╗████╗ ████║██╔══██╗████╗  ██║██╔══██╗██╔════╝ ██╔════╝██╔══██╗",
    "███████║██████╔╝██████╔╝██╔████╔██║███████║██╔██╗ ██║███████║██║  ███╗█████╗  ██████╔╝",
    "██╔══██║██╔═══╝ ██╔═══╝ ██║╚██╔╝██║██╔══██║██║╚██╗██║██╔══██║██║   ██║██╔══╝  ██╔══██╗",
    "██║  ██║██║     ██║     ██║ ╚═╝ ██║██║  ██║██║ ╚████║██║  ██║╚██████╔╝███████╗██║  ██║",
    "╚═╝  ╚═╝╚═╝     ╚═╝     ╚═╝     ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝╚═╝  ╚═╝ ╚═════╝ ╚══════╝╚═╝  ╚═╝",
]
GLITCH_CHARS = "#/\\01_<>░▒▓"
SCAN_WIDTH = 54


def terminal_width() -> int:
    return max(118, shutil.get_terminal_size((130, 38)).columns)


def center(line: str, width: int) -> str:
    return line.center(width)


def banner_box(lines: list[str]) -> str:
    width = terminal_width()
    content_width = max(len(line) for line in BANNER)
    inner = content_width + 8
    top = "╔" + "═" * inner + "╗"
    bottom = "╚" + "═" * inner + "╝"
    out = [center(top, width), center("║" + " " * inner + "║", width)]
    for line in lines:
        out.append(center("║    " + line.ljust(content_width) + "    ║", width))
    out.append(center("║" + " " * inner + "║", width))
    out.append(center("║" + (f"──────────────  VERSION {APP_VERSION_SHORT}  ──────────────").center(inner) + "║", width))
    out.append(center("║" + "WINDOWS WORKSPACE CONTROL SYSTEM".center(inner) + "║", width))
    out.append(center("║" + " " * inner + "║", width))
    out.append(center(bottom, width))
    return "\n".join(out)


def menu_box() -> str:
    width = terminal_width(); inner = 86
    top = "╔" + "═" * inner + "╗"; bottom = "╚" + "═" * inner + "╝"
    out = [
        center(top, width),
        center("║" + "──────────────  BUILD CONTROL  ──────────────".center(inner) + "║", width),
        center("║" + " " * inner + "║", width),
        center("║" + "   [1]  QUICK BUILD         Progress screen only".ljust(inner) + "║", width),
        center("║" + "   [2]  TECHNICAL BUILD     Full compiler / PyInstaller output".ljust(inner) + "║", width),
        center("║" + "   [3]  EXIT                Close build system".ljust(inner) + "║", width),
        center("║" + " " * inner + "║", width),
        center(bottom, width),
    ]
    return "\n".join(out)


def progress_box(percent: int, message: str) -> str:
    width = terminal_width(); inner = 86
    filled = round(50 * max(0, min(percent, 100)) / 100)
    bar = "[" + "█" * filled + "░" * (50 - filled) + f"]  {percent:>3}%"
    top = "╔" + "═" * inner + "╗"; bottom = "╚" + "═" * inner + "╝"
    out = [
        center(top, width),
        center("║" + "──────────────  QUICK BUILD  ──────────────".center(inner) + "║", width),
        center("║" + " " * inner + "║", width),
        center("║" + bar.center(inner) + "║", width),
        center("║" + " " * inner + "║", width),
        center("║" + message.center(inner) + "║", width),
        center("║" + "PLEASE WAIT...".center(inner) + "║", width),
        center("║" + " " * inner + "║", width),
        center(bottom, width),
    ]
    return "\n".join(out)


def final_screen() -> str:
    return banner_box(BANNER) + "\n\n" + menu_box()


def quick_screen(percent: int, message: str) -> str:
    return banner_box(BANNER) + "\n\n" + progress_box(percent, message)


def draw(frame: str) -> None:
    sys.stdout.write(HOME + BRIGHT + frame + RESET + "\033[J"); sys.stdout.flush()


def reveal_frames() -> list[list[str]]:
    max_width = max(len(line) for line in BANNER)
    frames = [[line[:visible] for line in BANNER] for visible in range(3, max_width + 6, 5)]
    frames.append(BANNER[:]); return frames


def glitch(lines: list[str]) -> list[str]:
    result = [list(line) for line in lines]
    positions = [(r, c) for r, row in enumerate(result) for c, ch in enumerate(row) if ch != " "]
    for row, col in random.sample(positions, min(random.randint(8, 18), len(positions))):
        result[row][col] = random.choice(GLITCH_CHARS)
    return ["".join(line) for line in result]


def animated_frame(lines: list[str], status: str, progress: int | None = None) -> str:
    width = terminal_width(); out = [banner_box(lines)]
    if progress is not None:
        progress = max(0, min(progress, SCAN_WIDTH))
        out += ["", center("[" + "█" * progress + "░" * (SCAN_WIDTH - progress) + "]", width)]
    out += ["", center(status, width)]
    return "\n".join(out)


def animate() -> None:
    sys.stdout.write(HIDE_CURSOR + CLEAR + HOME); sys.stdout.flush()
    try:
        for lines in reveal_frames():
            draw(animated_frame(lines, "INITIALIZING // ASSEMBLING APPMANAGER")); time.sleep(0.045)
        for index in range(8):
            draw(animated_frame(glitch(BANNER) if index % 2 == 0 else BANNER, "SIGNAL LOCK // STABILIZING")); time.sleep(0.05)
        for amount in range(0, SCAN_WIDTH + 1, 3):
            draw(animated_frame(BANNER, "BOOT SEQUENCE // SYSTEM CHECK", amount)); time.sleep(0.025)
        draw(animated_frame(BANNER, "SYSTEM READY // BUILD CONTROL ONLINE", SCAN_WIDTH)); time.sleep(0.25)
        draw(final_screen())
    finally:
        sys.stdout.write(SHOW_CURSOR + RESET); sys.stdout.flush()


def render_menu() -> None:
    sys.stdout.write(CLEAR + HOME); draw(final_screen())


def render_header() -> None:
    sys.stdout.write(CLEAR + HOME); draw(banner_box(BANNER))


def render_quick() -> None:
    try: percent = int(sys.argv[2])
    except (IndexError, ValueError): percent = 0
    message = " ".join(sys.argv[3:]).strip() or "WORKING"
    sys.stdout.write(CLEAR + HOME); draw(quick_screen(percent, message))


def main() -> None:
    if os.name != "nt": return
    try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError): pass
    os.system("")
    mode = sys.argv[1].lower() if len(sys.argv) > 1 else "animate"
    if mode == "--menu": render_menu()
    elif mode == "--header": render_header()
    elif mode == "--quick": render_quick()
    else: animate()


if __name__ == "__main__":
    main()
