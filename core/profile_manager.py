from __future__ import annotations

import re
import threading
import uuid
from copy import deepcopy
from typing import Any, Callable

from .config_manager import ConfigManager
from .process_manager import ProcessManager

EventCallback = Callable[[str, str, int, int], None]


class ProfileManager:
    def __init__(self, config: ConfigManager, processes: ProcessManager) -> None:
        self.config, self.processes = config, processes

    @property
    def profiles(self) -> list[dict[str, Any]]:
        return self.config.data["profiles"]

    def get(self, identifier: str) -> dict[str, Any] | None:
        key = identifier.casefold()
        return next((p for p in self.profiles if str(p.get("id", "")).casefold() == key or str(p.get("name", "")).casefold() == key), None)

    def save_profile(self, profile: dict[str, Any]) -> dict[str, Any]:
        item = deepcopy(profile)
        item.setdefault("id", re.sub(r"[^a-z0-9]+", "-", str(item.get("name", "profile")).lower()).strip("-") + "-" + uuid.uuid4().hex[:6])
        item.setdefault("description", "")
        item.setdefault("icon", "◆")
        item.setdefault("open_apps", [])
        item.setdefault("close_apps", [])
        existing = self.get(str(item["id"]))
        if existing:
            existing.clear(); existing.update(item)
        else:
            self.profiles.append(item)
        self.config.save()
        return item

    def delete(self, identifier: str) -> None:
        self.config.data["profiles"] = [p for p in self.profiles if p.get("id") != identifier]
        self.config.save()

    def duplicate(self, identifier: str) -> dict[str, Any]:
        source = deepcopy(self.get(identifier) or {})
        source.pop("id", None)
        source["name"] = f"{source.get('name', 'Profile')} Copy"
        return self.save_profile(source)

    def run_async(self, profile: dict[str, Any], callback: EventCallback, done: Callable[[int, int], None]) -> threading.Thread:
        def work() -> None:
            actions = list(profile.get("close_apps", [])) + list(profile.get("open_apps", []))
            total, warnings, errors, completed = len(actions), 0, 0, 0
            settings = self.config.data["settings"]
            for name in profile.get("close_apps", []):
                status, message = self.processes.close_by_name(str(name), float(settings["graceful_close_timeout"]))
                completed += 1; warnings += status == "warning"; errors += status == "error"
                callback(status, message, completed, total)
            if profile.get("close_apps") and profile.get("open_apps"):
                self.processes.delay(float(settings["close_launch_delay"]))
            for app in profile.get("open_apps", []):
                status, message = self.processes.launch(str(app.get("path", "")), bool(settings["skip_running_apps"]))
                completed += 1; warnings += status == "warning"; errors += status == "error"
                callback(status, message, completed, total)
            done(warnings, errors)
        thread = threading.Thread(target=work, name="profile-runner", daemon=True)
        thread.start()
        return thread
