from __future__ import annotations
import os, sys
from pathlib import Path

class ShortcutManager:
    def create(self, profile_name: str) -> tuple[bool, str]:
        if sys.platform != "win32": return False, "Desktop shortcuts are only available on Windows."
        try:
            from win32com.client import Dispatch
            desktop = Path(os.environ.get("USERPROFILE", str(Path.home()))) / "Desktop"
            shortcut_path = desktop / f"{''.join(c for c in profile_name if c not in '<>:"/\\|?*')}.lnk"
            shell = Dispatch("WScript.Shell"); shortcut = shell.CreateShortCut(str(shortcut_path))
            if getattr(sys, "frozen", False): shortcut.Targetpath = sys.executable; shortcut.Arguments = f'--profile "{profile_name}"'
            else: shortcut.Targetpath = sys.executable; shortcut.Arguments = f'"{Path(__file__).resolve().parents[1] / "main.py"}" --profile "{profile_name}"'
            shortcut.WorkingDirectory = str(Path(sys.executable).parent); shortcut.IconLocation = sys.executable; shortcut.save()
            return True, f"Shortcut created: {shortcut_path.name}"
        except Exception as exc: return False, f"Could not create shortcut: {exc}"
