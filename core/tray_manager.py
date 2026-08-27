from __future__ import annotations
import threading
from typing import Callable, Any
from PIL import Image, ImageDraw
import pystray

class TrayManager:
    def __init__(self, open_window: Callable[[], None], run_profile: Callable[[dict[str, Any]], None], exit_app: Callable[[], None]) -> None:
        self.open_window, self.run_profile, self.exit_app = open_window, run_profile, exit_app
        self.icon: pystray.Icon | None = None

    def start(self, profiles: list[dict[str, Any]]) -> None:
        self.stop()
        image = Image.new("RGB", (64, 64), "#10131a"); draw = ImageDraw.Draw(image)
        draw.rounded_rectangle((10, 10, 54, 54), 12, fill="#6c7cff"); draw.ellipse((26, 26, 38, 38), fill="white")
        items = [pystray.MenuItem("Open App Manager", self.open_window), pystray.Menu.SEPARATOR]
        items += [pystray.MenuItem(str(p.get("name", "Profile")), lambda _i, _x, profile=p: self.run_profile(profile)) for p in profiles]
        items += [pystray.Menu.SEPARATOR, pystray.MenuItem("Exit", self.exit_app)]
        self.icon = pystray.Icon("AppManager", image, "App Manager", pystray.Menu(*items))
        threading.Thread(target=self.icon.run, daemon=True, name="system-tray").start()

    def stop(self) -> None:
        if self.icon:
            self.icon.stop(); self.icon = None
