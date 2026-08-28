from __future__ import annotations

import sys
import threading
from functools import partial
from pathlib import Path
from typing import Any, Callable

from PIL import Image, ImageDraw
import pystray


class TrayManager:
    """Owns the Windows notification-area icon and profile menu."""

    def __init__(
        self,
        open_window: Callable[[], None],
        run_profile: Callable[[dict[str, Any]], None],
        exit_app: Callable[[], None],
    ) -> None:
        self.open_window = open_window
        self.run_profile = run_profile
        self.exit_app = exit_app
        self.icon: pystray.Icon | None = None
        self._lock = threading.RLock()
        self._thread: threading.Thread | None = None

    @staticmethod
    def _asset_path(name: str) -> Path:
        """Resolve bundled assets in source and PyInstaller builds."""
        bundle_root = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[1]))
        candidate = bundle_root / "assets" / name
        if candidate.exists():
            return candidate
        return Path(__file__).resolve().parents[1] / "assets" / name

    @classmethod
    def _load_icon_image(cls) -> Image.Image:
        """Load the branded icon, with a safe fallback if assets are missing."""
        for filename in ("appmanager.png", "appmanager.ico"):
            path = cls._asset_path(filename)
            if path.exists():
                with Image.open(path) as source:
                    return source.convert("RGBA").resize((64, 64), Image.Resampling.LANCZOS)

        # Fallback keeps the tray usable even when running from an incomplete
        # source checkout. It intentionally matches the AppManager palette.
        image = Image.new("RGBA", (64, 64), (7, 11, 17, 255))
        draw = ImageDraw.Draw(image)
        draw.rounded_rectangle((5, 5, 59, 59), radius=12, outline=(54, 224, 230, 255), width=3)
        draw.line((16, 45, 23, 18, 30, 45), fill=(54, 224, 230, 255), width=4)
        draw.line((36, 45, 36, 20, 44, 34, 52, 20, 52, 45), fill=(225, 248, 249, 255), width=4)
        return image

    def _open_action(self, icon: pystray.Icon, item: pystray.MenuItem) -> None:
        self.open_window()

    def _profile_action(self, profile: dict[str, Any], icon: pystray.Icon, item: pystray.MenuItem) -> None:
        self.run_profile(profile)

    def _exit_action(self, icon: pystray.Icon, item: pystray.MenuItem) -> None:
        self.exit_app()

    def _build_menu(self, profiles: list[dict[str, Any]]) -> pystray.Menu:
        items: list[Any] = [
            pystray.MenuItem("Open AppManager", self._open_action, default=True),
            pystray.Menu.SEPARATOR,
        ]

        if profiles:
            for profile in profiles:
                label = str(profile.get("name") or "Profile")
                items.append(pystray.MenuItem(label, partial(self._profile_action, profile)))
        else:
            items.append(pystray.MenuItem("No profiles configured", None, enabled=False))

        items.extend([
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Exit AppManager", self._exit_action),
        ])
        return pystray.Menu(*items)

    def start(self, profiles: list[dict[str, Any]]) -> None:
        """Start or rebuild the notification-area icon."""
        with self._lock:
            self.stop()
            image = self._load_icon_image()
            menu = self._build_menu(profiles)
            self.icon = pystray.Icon(
                "AppManager",
                image,
                "AppManager 1.1",
                menu,
            )
            icon = self.icon
            self._thread = threading.Thread(
                target=icon.run,
                daemon=True,
                name="appmanager-system-tray",
            )
            self._thread.start()

    def stop(self) -> None:
        with self._lock:
            icon = self.icon
            self.icon = None
            if icon is not None:
                try:
                    icon.stop()
                except Exception:
                    # Shutdown should never prevent the main application from
                    # closing or rebuilding the tray menu.
                    pass
            self._thread = None
