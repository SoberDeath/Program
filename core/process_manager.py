from __future__ import annotations

import os
import subprocess
import sys
import time
import logging
from pathlib import Path
from typing import Any

import psutil

LOGGER = logging.getLogger(__name__)

BACKGROUND_PROCESS_NAMES = {
    "audiodg.exe", "conhost.exe", "csrss.exe", "ctfmon.exe", "dllhost.exe",
    "dwm.exe", "fontdrvhost.exe", "lsass.exe", "memory compression", "registry",
    "services.exe", "sihost.exe", "smss.exe", "spoolsv.exe", "svchost.exe",
    "system", "system idle process", "taskhostw.exe", "wininit.exe", "winlogon.exe",
}


class ProcessManager:
    """Safely inspects, starts, and stops desktop processes."""

    def __init__(self, psutil_module: Any = psutil) -> None:
        self.psutil = psutil_module
        self.protected_pids = {os.getpid(), os.getppid()}

    @staticmethod
    def _window_process_ids() -> set[int]:
        if sys.platform != "win32":
            return set()
        try:
            import win32gui
            import win32process
            pids: set[int] = set()
            def collect(hwnd: int, _: object) -> bool:
                if win32gui.IsWindowVisible(hwnd) and win32gui.GetWindowText(hwnd).strip():
                    _, pid = win32process.GetWindowThreadProcessId(hwnd)
                    pids.add(pid)
                return True
            win32gui.EnumWindows(collect, None)
            return pids
        except (ImportError, OSError):
            return set()

    def process_snapshot(self, include_system: bool = False) -> list[dict[str, Any]]:
        """Collect PID and name once; expensive properties are deliberately lazy."""
        started = time.perf_counter()
        window_pids = set() if include_system else self._window_process_ids()
        items: list[dict[str, Any]] = []
        for process in self.psutil.process_iter(["pid", "name"]):
            try:
                pid = int(process.info.get("pid", process.pid))
                name = str(process.info.get("name") or "Unknown")
            except (self.psutil.NoSuchProcess, self.psutil.AccessDenied, self.psutil.ZombieProcess, TypeError, ValueError):
                continue
            if not include_system and (
                pid <= 4
                or name.casefold() in BACKGROUND_PROCESS_NAMES
                or (window_pids and pid not in window_pids)
            ):
                continue
            items.append({"pid": pid, "name": name})
        result = sorted(items, key=lambda item: (str(item["name"]).casefold(), item["pid"]))
        LOGGER.debug("Process snapshot (%d rows) took %.3f seconds", len(result), time.perf_counter() - started)
        return result

    def process_executable(self, pid: int) -> str:
        """Resolve an executable path lazily for a displayed process row."""
        try:
            return str(self.psutil.Process(pid).exe() or "")
        except (self.psutil.NoSuchProcess, self.psutil.AccessDenied, self.psutil.ZombieProcess, OSError):
            return ""

    def running_processes(self, include_system: bool = False) -> list[dict[str, Any]]:
        """Compatibility helper returning a snapshot with lazy paths resolved."""
        items = self.process_snapshot(include_system)
        for item in items:
            item["exe"] = self.process_executable(item["pid"])
        return items

    def is_running(self, executable: str) -> bool:
        target_path = os.path.normcase(os.path.abspath(executable))
        target_name = Path(executable).name.casefold()
        for process in self.psutil.process_iter(["name", "exe"]):
            try:
                name = (process.info.get("name") or "").casefold()
                path = process.info.get("exe")
                if name == target_name or (path and os.path.normcase(os.path.abspath(path)) == target_path):
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return False

    @staticmethod
    def _request_windows_close(pid: int) -> bool:
        """Post WM_CLOSE to every top-level window owned by *pid*.

        This asks GUI applications to save state and close normally.  A process
        without a window is handled by the terminate fallback below.
        """
        if sys.platform != "win32":
            return False
        try:
            import win32con
            import win32gui
            windows: list[int] = []
            def collect(hwnd: int, _: object) -> bool:
                _, owner_pid = __import__("win32process").GetWindowThreadProcessId(hwnd)
                if owner_pid == pid and win32gui.IsWindow(hwnd):
                    windows.append(hwnd)
                return True
            win32gui.EnumWindows(collect, None)
            for hwnd in windows:
                win32gui.PostMessage(hwnd, win32con.WM_CLOSE, 0, 0)
            return bool(windows)
        except (ImportError, OSError):
            return False

    def close_by_name(self, process_name: str, timeout: float) -> tuple[str, str]:
        target = Path(process_name).name.casefold()
        matches: list[psutil.Process] = []
        for process in self.psutil.process_iter(["pid", "name"]):
            try:
                if process.pid not in self.protected_pids and (process.info["name"] or "").casefold() == target:
                    matches.append(process)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        if not matches:
            return "warning", f"{process_name} was not running"
        errors = 0
        requested: list[Any] = []
        for process in matches:
            try:
                if not self._request_windows_close(process.pid):
                    process.terminate()
                requested.append(process)
            except (self.psutil.NoSuchProcess, self.psutil.AccessDenied):
                errors += 1
        _, alive = self.psutil.wait_procs(requested, timeout=max(0.1, timeout))
        for process in alive:
            try:
                process.kill()
                process.wait(timeout=1)
            except (self.psutil.Error, OSError):
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
