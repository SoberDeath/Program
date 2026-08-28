from __future__ import annotations

import os
import random
import sys
import time

CYAN = "\033[96m"
DIM = "\033[2m"
RESET = "\033[0m"
HIDE_CURSOR = "\033[?25l"
SHOW_CURSOR = "\033[?25h"
HOME = "\033[H"
CLEAR = "\033[2J"

WIDTH = 70
TITLE = "APPMANAGER"
GLITCH_CHARS = "#/\\01_<>"


def centered(text: str) -> str:
    return text.center(WIDTH)


def box(lines: list[str]) -> str:
    top = "+" + "=" * WIDTH + "+"
    body = ["|" + centered(line) + "|" for line in lines]
    return "\n".join([top, *body, top])


def render(title: str, status: str, scan: int = -1) -> str:
    scan_width = 38
    if scan < 0:
        scanline = ""
    else:
        scan = max(0, min(scan, scan_width - 1))
        scanline = "[" + "=" * scan + ">" + "." * (scan_width - scan - 1) + "]"

    lines = [
        "",
        title,
        "",
        "VERSION 1.0",
        "WINDOWS WORKSPACE CONTROL SYSTEM",
        "",
        scanline,
        status,
        "",
    ]
    return box(lines)


def draw(frame: str) -> None:
    sys.stdout.write(HOME + CYAN + frame + RESET)
    sys.stdout.flush()


def glitch_title() -> str:
    chars = list(TITLE)
    count = random.randint(1, 3)
    for idx in random.sample(range(len(chars)), count):
        chars[idx] = random.choice(GLITCH_CHARS)
    return " ".join(chars)


def main() -> None:
    if os.name != "nt":
        return

    # Enable ANSI/VT processing in modern Windows terminals.
    os.system("")
    sys.stdout.write(HIDE_CURSOR + CLEAR + HOME)
    sys.stdout.flush()

    try:
        # Build the name up from a single character.
        reveal = ["A", "APP", "APPMA", "APPMANA", "APPMANAGER"]
        for text in reveal:
            draw(render(" ".join(text), "INITIALIZING..."))
            time.sleep(0.10)

        # Short controlled glitch sequence.
        for _ in range(7):
            draw(render(glitch_title(), "SIGNAL LOCK // ACQUIRING"))
            time.sleep(0.055)

        # Lock the final wordmark and run a scanline across it.
        final_title = "A P P M A N A G E R"
        for position in range(0, 38, 3):
            draw(render(final_title, "BOOT SEQUENCE // ONLINE", position))
            time.sleep(0.035)

        draw(render(final_title, "SYSTEM READY // BUILD CONTROL ONLINE", 37))
        time.sleep(0.35)
    finally:
        sys.stdout.write(SHOW_CURSOR + RESET)
        sys.stdout.flush()


if __name__ == "__main__":
    main()
