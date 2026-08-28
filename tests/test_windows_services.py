"""Contract tests for Windows integrations using deterministic API doubles."""
import sys
import types

from core.startup_manager import StartupManager


def test_startup_manager_writes_and_removes_current_user_run_key(monkeypatch):
    values = {}
    winreg = types.ModuleType("winreg")
    winreg.HKEY_CURRENT_USER = 1; winreg.KEY_SET_VALUE = 2; winreg.REG_SZ = 3
    class Key:
        def __enter__(self): return self
        def __exit__(self, *_args): return None
    winreg.OpenKey = lambda *_args: Key()
    winreg.SetValueEx = lambda _key, name, _reserved, _kind, value: values.__setitem__(name, value)
    def remove(_key, name):
        if name not in values: raise FileNotFoundError
        values.pop(name)
    winreg.DeleteValue = remove
    monkeypatch.setitem(sys.modules, "winreg", winreg)
    monkeypatch.setattr(sys, "platform", "win32")
    manager = StartupManager()
    assert manager.set_enabled(True)[0] and values[manager.NAME]
    assert manager.set_enabled(False)[0] and manager.NAME not in values


def test_tray_menu_open_profile_and_exit_callbacks(monkeypatch):
    calls = []
    pystray = types.ModuleType("pystray")
    class MenuItem:
        def __init__(self, text, action, **_kwargs): self.text, self.action = text, action
    class Menu:
        SEPARATOR = object()
        def __init__(self, *items): self.items = items
    class Icon:
        def __init__(self, _name, _image, _title, menu): self.menu, self.stopped = menu, False
        def run(self): return None
        def stop(self): self.stopped = True
    pystray.MenuItem, pystray.Menu, pystray.Icon = MenuItem, Menu, Icon
    pillow = types.ModuleType("PIL")
    class Source:
        def __enter__(self): return self
        def __exit__(self, *_args): return None
        def convert(self, _mode): return self
        def resize(self, _size, _method): return self
    class Image:
        class Resampling: LANCZOS = 1
        @staticmethod
        def open(*_args): return Source()
        @staticmethod
        def new(*_args): return Source()
    pillow.Image = Image
    monkeypatch.setitem(sys.modules, "pystray", pystray)
    monkeypatch.setitem(sys.modules, "PIL", pillow)
    sys.modules.pop("core.tray_manager", None)
    from core.tray_manager import TrayManager
    manager = TrayManager(lambda: calls.append("open"), lambda profile: calls.append(profile["name"]), lambda: calls.append("exit"))
    manager.start([{"name": "Gaming"}])
    items = [item for item in manager.icon.menu.items if item is not Menu.SEPARATOR]
    items[0].action(None, None); items[1].action(None, None); items[2].action(None, None)
    assert calls == ["open", "Gaming", "exit"]
    manager.stop()
