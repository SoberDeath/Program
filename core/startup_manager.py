from __future__ import annotations
import sys
from pathlib import Path

class StartupManager:
    KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
    NAME = "AppManager"

    @staticmethod
    def command() -> str:
        target = Path(sys.executable if getattr(sys, "frozen", False) else Path(__file__).resolve().parents[1] / "main.py")
        return f'"{target}"' if getattr(sys, "frozen", False) else f'"{sys.executable}" "{target}"'

    def set_enabled(self, enabled: bool) -> tuple[bool, str]:
        if sys.platform != "win32": return False, "Windows startup is only available on Windows."
        try:
            import winreg
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, self.KEY, 0, winreg.KEY_SET_VALUE) as key:
                if enabled: winreg.SetValueEx(key, self.NAME, 0, winreg.REG_SZ, self.command())
                else:
                    try: winreg.DeleteValue(key, self.NAME)
                    except FileNotFoundError: pass
            return True, "Startup preference updated."
        except OSError as exc: return False, f"Could not update startup: {exc}"
