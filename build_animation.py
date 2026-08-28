from __future__ import annotations

import os
import random
import shutil
import sys
import time

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
    return max(118, shutil.get_terminal_size((120, 36)).columns)


def center(line: str, width: int) -> str:
    return line.center(width)


def framed_banner(lines: list[str], status: str = "", progress: int | None = None) -> str:
    width = terminal_width()
    content_width = max(len(line) for line in BANNER)
    top = "╔" + "═" * (content_width + 4) + "╗"
    bottom = "╚" + "═" * (content_width + 4) + "╝"

    out = [center(top, width)]
    for line in lines:
        out.append(center("║  " + line.ljust(content_width) + "  ║", width))
    out.append(center("║" + " " * (content_width + 4) + "║", width))
    out.append(center("║" + "VERSION 1.0".center(content_width + 4) + "║", width))
    out.append(center("║" + "WINDOWS WORKSPACE CONTROL SYSTEM".center(content_width + 4) + "║", width))
    out.append(center(bottom, width))

    if progress is not None:
        progress = max(0, min(progress, SCAN_WIDTH))
        bar = "[" + "█" * progress + "░" * (SCAN_WIDTH - progress) + "]"
        out.extend(["", center(bar, width)])
    if status:
        out.append(center(status, width))
    return "\n".join(out)


def build_menu() -> str:
    width = terminal_width()
    menu_width = 82
    top = "╔" + "═" * menu_width + "╗"
    split = "╠" + "═" * menu_width + "╣"
    bottom = "╚" + "═" * menu_width + "╝"
    rows = [
        top,
        "║" + "BUILD CONTROL".center(menu_width) + "║",
        split,
        "║" + "".ljust(menu_width) + "║",
        "║" + "   [1]  QUICK BUILD        Progress screen only".ljust(menu_width) + "║",
        "║" + "   [2]  TECHNICAL BUILD    Full compiler / PyInstaller output".ljust(menu_width) + "║",
        "║" + "   [3]  EXIT               Close build system".ljust(menu_width) + "║",
        "║" + "".ljust(menu_width) + "║",
        bottom,
    ]
    return "\n".join(center(row, width) for row in rows)


def final_screen() -> str:
    return framed_banner(BANNER) + "\n\n" + build_menu()


def draw(frame: str, clear_tail: bool = True) -> None:
    tail = "\033[J" if clear_tail else ""
    sys.stdout.write(HOME + BRIGHT + frame + RESET + tail)
    sys.stdout.flush()


def reveal_frames() -> list[list[str]]:
    max_width = max(len(line) for line in BANNER)
    frames: list[list[str]] = []
    for visible in range(4, max_width + 5, 6):
        frames.append([line[:visible] for line in BANNER])
    frames.append(BANNER[:])
    return frames


def glitch(lines: list[str]) -> list[str]:
    result = [list(line) for line in lines]
    positions: list[tuple[int, int]] = []
    for row, line in enumerate(result):
        for col, char in enumerate(line):
            if char != " ":
                positions.append((row, col))
    if not positions:
        return lines
    for row, col in random.sample(positions, min(random.randint(8, 20), len(positions))):
        result[row][col] = random.choice(GLITCH_CHARS)
    return ["".join(line) for line in result]


def animate() -> None:
    sys.stdout.write(HIDE_CURSOR + CLEAR + HOME)
    sys.stdout.flush()
    try:
        for lines in reveal_frames():
            draw(framed_banner(lines, "INITIALIZING // ASSEMBLING WORDMARK"))
            time.sleep(0.05)

        for index in range(10):
            lines = glitch(BANNER) if index % 2 == 0 else BANNER
            draw(framed_banner(lines, "SIGNAL LOCK // STABILIZING"))
            time.sleep(0.05)

        for amount in range(0, SCAN_WIDTH + 1, 3):
            draw(framed_banner(BANNER, "BOOT SEQUENCE // SYSTEM CHECK", amount))
            time.sleep(0.03)

        draw(framed_banner(BANNER, "SYSTEM READY // BUILD CONTROL ONLINE", SCAN_WIDTH))
        time.sleep(0.30)
        draw(final_screen())
    finally:
        sys.stdout.write(SHOW_CURSOR + RESET)
        sys.stdout.flush()


def render_menu() -> None:
    sys.stdout.write(CLEAR + HOME)
    draw(final_screen())


def render_header() -> None:
    sys.stdout.write(CLEAR + HOME)
    draw(framed_banner(BANNER))


def main() -> None:
    if os.name != "nt":
        return
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError):
        pass
    os.system("")

    mode = sys.argv[1].lower() if len(sys.argv) > 1 else "animate"
    if mode == "--menu":
        render_menu()
    elif mode == "--header":
        render_header()
    else:
        animate()


if __name__ == "__main__":
    main()
