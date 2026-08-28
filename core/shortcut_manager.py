from __future__ import annotations
import sys
from pathlib import Path

class ShortcutManager:
    def create(self, profile_name: str) -> tuple[bool, str]:
        if sys.platform != "win32": return False, "Desktop shortcuts are only available on Windows."
        try:
            from win32com.client import Dispatch
            from win32com.shell import shell, shellcon
            desktop = Path(shell.SHGetFolderPath(0, shellcon.CSIDL_DESKTOPDIRECTORY, None, 0))
            safe_name = "".join(c for c in profile_name if c not in '<>:"/\\|?*').strip().rstrip(".") or "App Manager Profile"
            shortcut_path = desktop / f"{safe_name}.lnk"
            shell = Dispatch("WScript.Shell"); shortcut = shell.CreateShortCut(str(shortcut_path))
            if getattr(sys, "frozen", False): shortcut.Targetpath = sys.executable; shortcut.Arguments = f'--profile "{profile_name}"'
            else: shortcut.Targetpath = sys.executable; shortcut.Arguments = f'"{Path(__file__).resolve().parents[1] / "main.py"}" --profile "{profile_name}"'
            shortcut.WorkingDirectory = str(Path(sys.executable).parent); shortcut.IconLocation = sys.executable; shortcut.save()
            return True, f"Shortcut created: {shortcut_path.name}"
        except Exception as exc: return False, f"Could not create shortcut: {exc}"
