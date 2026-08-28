from __future__ import annotations

import json
import logging
import shutil
import time
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from threading import RLock
from typing import Any, Callable

LOGGER = logging.getLogger(__name__)
DEFAULT_CONFIG: dict[str, Any] = {
    "profiles": [],
    "settings": {
        "skip_running_apps": True,
        "minimize_to_tray": True,
        "start_with_windows": False,
        "close_launch_delay": 0.5,
        "graceful_close_timeout": 3.0,
        "ui_scaling": 1.0,
    },
}


class ConfigManager:
    """Loads and atomically persists validated local configuration."""

    def __init__(self, path: Path) -> None:
        started = time.perf_counter()
        self.path = path
        self._lock = RLock()
        self.warning: str | None = None
        self.data = self._load()
        self._last_saved = json.dumps(self.data, indent=2, ensure_ascii=False)
        LOGGER.debug("Configuration loaded in %.3f seconds", time.perf_counter() - started)

    def _load(self) -> dict[str, Any]:
        if not self.path.exists():
            data = deepcopy(DEFAULT_CONFIG)
            self._write(data)
            return data
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
            if not isinstance(raw, dict) or not isinstance(raw.get("profiles", []), list):
                raise ValueError("Configuration root is invalid")
            result = deepcopy(DEFAULT_CONFIG)
            result["profiles"] = [p for p in raw.get("profiles", []) if isinstance(p, dict)]
            if isinstance(raw.get("settings"), dict):
                result["settings"].update(raw["settings"])
            settings = result["settings"]
            settings["skip_running_apps"] = bool(settings["skip_running_apps"])
            settings["minimize_to_tray"] = bool(settings["minimize_to_tray"])
            settings["start_with_windows"] = bool(settings["start_with_windows"])
            settings["close_launch_delay"] = min(3.0, max(0.0, self._number(settings["close_launch_delay"], 0.5)))
            settings["graceful_close_timeout"] = min(10.0, max(0.1, self._number(settings["graceful_close_timeout"], 3.0)))
            settings["ui_scaling"] = min(1.4, max(0.8, self._number(settings["ui_scaling"], 1.0)))
            return result
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            backup = self.path.with_name(f"config.corrupt-{stamp}.json")
            try:
                shutil.copy2(self.path, backup)
            except OSError:
                LOGGER.exception("Could not back up invalid configuration")
            self.warning = f"The configuration was invalid and was reset. Backup: {backup.name}"
            LOGGER.warning("Resetting invalid configuration: %s", exc)
            data = deepcopy(DEFAULT_CONFIG)
            self._write(data)
            return data

    @staticmethod
    def _number(value: Any, fallback: float) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return fallback

    def _write(self, data: dict[str, Any]) -> None:
        serialized = json.dumps(data, indent=2, ensure_ascii=False)
        if getattr(self, "_last_saved", None) == serialized and self.path.exists():
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(".tmp")
        temporary.write_text(serialized, encoding="utf-8")
        temporary.replace(self.path)
        self._last_saved = serialized

    def save(self) -> None:
        with self._lock:
            self._write(self.data)

    def update(self, mutator: Callable[[dict[str, Any]], None]) -> None:
        with self._lock:
            mutator(self.data)
            self._write(self.data)
