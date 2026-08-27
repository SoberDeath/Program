from __future__ import annotations

import os
import subprocess
import time
from pathlib import Path
from typing import Any

import psutil


class ProcessManager:
    """Safely inspects, starts, and stops desktop processes."""

    def __init__(self) -> None:
        self.protected_pids = {os.getpid(), os.getppid()}

    @staticmethod
    def _safe_info(process: psutil.Process) -> dict[str, Any] | None:
        try:
            info = process.as_dict(attrs=["pid", "name", "exe", "username"])
            info["name"] = info.get("name") or "Unknown"
            info["exe"] = info.get("exe") or ""
            return info
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            return None

    def running_processes(self, include_system: bool = False) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        for process in psutil.process_iter():
            info = self._safe_info(process)
            if not info:
                continue
            if not include_system and (not info["exe"] or info["pid"] <= 4):
                continue
            items.append(info)
        return sorted(items, key=lambda item: str(item["name"]).lower())

    def is_running(self, executable: str) -> bool:
        target_path = os.path.normcase(os.path.abspath(executable))
        target_name = Path(executable).name.casefold()
        for process in psutil.process_iter(["name", "exe"]):
            try:
                name = (process.info.get("name") or "").casefold()
                path = process.info.get("exe")
                if name == target_name or (path and os.path.normcase(os.path.abspath(path)) == target_path):
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return False

    def close_by_name(self, process_name: str, timeout: float) -> tuple[str, str]:
        target = Path(process_name).name.casefold()
        matches: list[psutil.Process] = []
        for process in psutil.process_iter(["pid", "name"]):
            try:
                if process.pid not in self.protected_pids and (process.info["name"] or "").casefold() == target:
                    matches.append(process)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        if not matches:
            return "warning", f"{process_name} was not running"
        errors = 0
        for process in matches:
            try:
                process.terminate()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                errors += 1
        _, alive = psutil.wait_procs(matches, timeout=max(0.1, timeout))
        for process in alive:
            try:
                process.kill()
                process.wait(timeout=1)
            except (psutil.Error, OSError):
                errors += 1
        return ("error", f"Could not close {process_name}") if errors else ("success", f"{process_name} closed")

    def launch(self, path: str, skip_running: bool) -> tuple[str, str]:
        name = Path(path).stem or path
        if not Path(path).is_file():
            return "error", f"{name}: executable was not found"
        if skip_running and self.is_running(path):
            return "warning", f"{name} was already running"
        try:
            subprocess.Popen([path], cwd=str(Path(path).parent), close_fds=True)
            return "success", f"{name} opened"
        except (OSError, ValueError) as exc:
            return "error", f"{name} could not open: {exc}"

    @staticmethod
    def delay(seconds: float) -> None:
        time.sleep(max(0.0, seconds))
