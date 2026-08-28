import json
import os
import threading
import time
from pathlib import Path
from core.config_manager import ConfigManager
from core.process_manager import ProcessManager
from core.profile_manager import ProfileManager
from main import configure_logging, writable_data_directory

def test_config_roundtrip_and_recovery(tmp_path):
    path = tmp_path / "config.json"; manager = ConfigManager(path); manager.data["settings"]["close_launch_delay"] = 1.2; manager.save()
    assert ConfigManager(path).data["settings"]["close_launch_delay"] == 1.2
    path.write_text("{broken", encoding="utf-8"); recovered = ConfigManager(path)
    assert recovered.warning and json.loads(path.read_text())["profiles"] == []
    assert list(tmp_path.glob("config.corrupt-*.json"))

def test_logging_writes_to_local_data_directory(tmp_path):
    import logging
    root = writable_data_directory(tmp_path)
    path = configure_logging(root)
    logging.getLogger("verification").warning("verified log output")
    logging.shutdown()
    assert path.exists() and "verified log output" in path.read_text(encoding="utf-8")

def test_config_normalizes_unsafe_setting_values(tmp_path):
    path = tmp_path / "config.json"
    path.write_text(json.dumps({"profiles": [], "settings": {"close_launch_delay": -20, "graceful_close_timeout": "bad", "ui_scaling": 99}}))
    settings = ConfigManager(path).data["settings"]
    assert settings["close_launch_delay"] == 0
    assert settings["graceful_close_timeout"] == 3
    assert settings["ui_scaling"] == 1.4

def test_unchanged_configuration_is_not_rewritten(tmp_path):
    path = tmp_path / "config.json"
    manager = ConfigManager(path)
    before = path.stat().st_mtime_ns
    time.sleep(.002)
    manager.save()
    assert path.stat().st_mtime_ns == before

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

def test_real_subprocess_launch_and_delay():
    processes = ProcessManager()
    executable = "/bin/true"
    if Path(executable).exists():
        assert processes.launch(executable, False)[0] == "success"
    started = time.monotonic(); processes.delay(.02)
    assert time.monotonic() - started >= .018

class FakeProcess:
    def __init__(self, pid, name, alive=True):
        self.pid, self.info, self.alive = pid, {"pid": pid, "name": name, "exe": f"/apps/{name}"}, alive
        self.terminated = self.killed = False
    def terminate(self): self.terminated = True
    def kill(self): self.killed = True; self.alive = False
    def wait(self, timeout): return 0
    def as_dict(self, attrs): return {**self.info, "username": "user"}

class FakePsutil:
    class Error(Exception): pass
    class NoSuchProcess(Error): pass
    class AccessDenied(Error): pass
    class ZombieProcess(Error): pass
    def __init__(self, processes, force_alive=False): self.processes, self.force_alive = processes, force_alive
    def process_iter(self, _attrs=None): return iter(self.processes)
    def wait_procs(self, processes, timeout):
        alive = list(processes) if self.force_alive else []
        return ([p for p in processes if p not in alive], alive)

def test_process_snapshot_requests_only_pid_and_name():
    process = FakeProcess(44, "Example.exe")
    class LightweightPsutil(FakePsutil):
        def process_iter(self, attrs=None):
            assert attrs == ["pid", "name"]
            return iter(self.processes)
    snapshot = ProcessManager(LightweightPsutil([process])).process_snapshot(False)
    assert snapshot == [{"pid": 44, "name": "Example.exe"}]
    assert "exe" not in snapshot[0]

def test_close_protects_self_and_force_kills_survivor(monkeypatch):
    own = FakeProcess(os.getpid(), "AppManager.exe")
    target = FakeProcess(4242, "AppManager.exe")
    fake = FakePsutil([own, target], force_alive=True)
    manager = ProcessManager(fake)
    monkeypatch.setattr(manager, "_request_windows_close", lambda _pid: False)
    status, _ = manager.close_by_name("appmanager.exe", .1)
    assert status == "success"
    assert not own.terminated and not own.killed
    assert target.terminated and target.killed

def test_running_detection_matches_name_and_path(tmp_path):
    executable = tmp_path / "Example.exe"; executable.write_bytes(b"")
    process = FakeProcess(44, "Example.exe"); process.info["exe"] = str(executable)
    assert ProcessManager(FakePsutil([process])).is_running(str(executable))

def test_profile_runner_is_async_ordered_and_resilient(tmp_path):
    class Processes:
        def __init__(self): self.calls = []
        def close_by_name(self, name, timeout): self.calls.append(("close", name, timeout)); return "success", f"{name} closed"
        def delay(self, seconds): self.calls.append(("delay", seconds))
        def launch(self, path, skip): self.calls.append(("open", path, skip)); return "warning", "already running"
    config = ConfigManager(tmp_path / "config.json"); process = Processes(); manager = ProfileManager(config, process)
    profile = manager.save_profile({"name": "Gaming", "close_apps": ["Work.exe"], "open_apps": [{"name": "Game", "path": "Game.exe"}]})
    events, complete = [], threading.Event()
    started = time.monotonic(); thread = manager.run_async(profile, lambda *event: events.append(event), lambda w, e: (events.append(("done", w, e)), complete.set()))
    assert time.monotonic() - started < .1 and thread.daemon
    assert complete.wait(1)
    assert [call[0] for call in process.calls] == ["close", "delay", "open"]
    assert events[-1] == ("done", 1, 0)
    assert events[0][2:] == (1, 2) and events[1][2:] == (2, 2)
