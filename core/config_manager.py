from __future__ import annotations

import json
import logging
import shutil
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
        self.path = path
        self._lock = RLock()
        self.warning: str | None = None
        self.data = self._load()

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

    def _write(self, data: dict[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(".tmp")
        temporary.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        temporary.replace(self.path)

    def save(self) -> None:
        with self._lock:
            self._write(self.data)

    def update(self, mutator: Callable[[dict[str, Any]], None]) -> None:
        with self._lock:
            mutator(self.data)
            self._write(self.data)
