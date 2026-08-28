from __future__ import annotations

import os
import random
import shutil
import sys
import time

CYAN = "\033[96m"
BRIGHT = "\033[1;96m"
DIM = "\033[2;36m"
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
    return max(110, shutil.get_terminal_size((120, 30)).columns)


def center(line: str, width: int) -> str:
    return line.center(width)


def frame_banner(lines: list[str], status: str = "", progress: int | None = None) -> str:
    width = terminal_width()
    content_width = max(len(line) for line in BANNER)
    top = "╔" + "═" * (content_width + 4) + "╗"
    bottom = "╚" + "═" * (content_width + 4) + "╝"

    output = [center(top, width)]
    for line in lines:
        output.append(center("║  " + line.ljust(content_width) + "  ║", width))
    output.append(center(bottom, width))
    output.append("")
    output.append(center("APPMANAGER  //  VERSION 1.0", width))
    output.append(center("WINDOWS WORKSPACE CONTROL SYSTEM", width))

    if progress is not None:
        progress = max(0, min(progress, SCAN_WIDTH))
        bar = "[" + "█" * progress + "░" * (SCAN_WIDTH - progress) + "]"
        output.extend(["", center(bar, width)])

    if status:
        output.append(center(status, width))

    return "\n".join(output)


def draw(frame: str, colour: str = CYAN) -> None:
    sys.stdout.write(HOME + colour + frame + RESET + "\033[J")
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

    for row, col in random.sample(positions, min(random.randint(7, 18), len(positions))):
        result[row][col] = random.choice(GLITCH_CHARS)
    return ["".join(line) for line in result]


def main() -> None:
    if os.name != "nt":
        return

    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError):
        pass

    # Trigger VT/ANSI support in Windows Terminal and modern consoles.
    os.system("")
    sys.stdout.write(HIDE_CURSOR + CLEAR + HOME)
    sys.stdout.flush()

    try:
        # 1. Large APPMANAGER wordmark builds from left to right.
        for lines in reveal_frames():
            draw(frame_banner(lines, "INITIALIZING // ASSEMBLING WORDMARK"), BRIGHT)
            time.sleep(0.055)

        # 2. Short glitch burst while keeping the exact same drawing area.
        for index in range(9):
            lines = glitch(BANNER) if index % 2 == 0 else BANNER
            draw(frame_banner(lines, "SIGNAL LOCK // STABILIZING"), BRIGHT)
            time.sleep(0.055)

        # 3. Clean banner + scanline/progress sweep.
        for amount in range(0, SCAN_WIDTH + 1, 3):
            draw(frame_banner(BANNER, "BOOT SEQUENCE // SYSTEM CHECK", amount), CYAN)
            time.sleep(0.035)

        # 4. Final locked frame.
        draw(frame_banner(BANNER, "SYSTEM READY // BUILD CONTROL ONLINE", SCAN_WIDTH), BRIGHT)
        time.sleep(0.45)
    finally:
        sys.stdout.write(SHOW_CURSOR + RESET)
        sys.stdout.flush()


if __name__ == "__main__":
    main()
