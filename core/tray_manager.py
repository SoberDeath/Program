from __future__ import annotations
import threading
from typing import Callable, Any
from PIL import Image
import pystray

class TrayManager:
    def __init__(self, open_window: Callable[[], None], run_profile: Callable[[dict[str, Any]], None], exit_app: Callable[[], None]) -> None:
        self.open_window, self.run_profile, self.exit_app = open_window, run_profile, exit_app
        self.icon: pystray.Icon | None = None
        self._lock = threading.RLock()

    def start(self, profiles: list[dict[str, Any]]) -> None:
        with self._lock:
            self.stop()
            # pystray requires a Pillow image, so generate one in memory.
            # No image file is shipped or read at runtime.
            image = Image.new("RGB", (64, 64), (91, 110, 246))
            items = [pystray.MenuItem("Open App Manager", lambda _icon, _item: self.open_window(), default=True), pystray.Menu.SEPARATOR]
            items += [pystray.MenuItem(str(p.get("name", "Profile")), lambda _i, _x, profile=p: self.run_profile(profile)) for p in profiles]
            items += [pystray.Menu.SEPARATOR, pystray.MenuItem("Exit", lambda _icon, _item: self.exit_app())]
            self.icon = pystray.Icon("AppManager", image, "App Manager", pystray.Menu(*items))
            threading.Thread(target=self.icon.run, daemon=True, name="system-tray").start()

    def stop(self) -> None:
        with self._lock:
            if self.icon:
                self.icon.stop(); self.icon = None
