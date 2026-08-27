import json
from pathlib import Path
from core.config_manager import ConfigManager
from core.process_manager import ProcessManager
from core.profile_manager import ProfileManager

def test_config_roundtrip_and_recovery(tmp_path):
    path = tmp_path / "config.json"; manager = ConfigManager(path); manager.data["settings"]["close_launch_delay"] = 1.2; manager.save()
    assert ConfigManager(path).data["settings"]["close_launch_delay"] == 1.2
    path.write_text("{broken", encoding="utf-8"); recovered = ConfigManager(path)
    assert recovered.warning and json.loads(path.read_text())["profiles"] == []
    assert list(tmp_path.glob("config.corrupt-*.json"))

def test_profile_crud(tmp_path):
    manager = ProfileManager(ConfigManager(tmp_path / "config.json"), ProcessManager())
    item = manager.save_profile({"name": "Work", "open_apps": [], "close_apps": []}); assert manager.get("Work")
    copy = manager.duplicate(item["id"]); assert copy["name"] == "Work Copy"
    manager.delete(item["id"]); assert manager.get(item["id"]) is None

def test_missing_launch_and_process_are_safe():
    processes = ProcessManager()
    assert processes.launch("certainly-missing-app.exe", True)[0] == "error"
    assert processes.close_by_name("certainly-missing-app.exe", .1)[0] == "warning"
    assert __import__("os").getpid() in processes.protected_pids
