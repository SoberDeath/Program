"""App Manager application entry point."""
from __future__ import annotations
import argparse, logging, os, sys
from pathlib import Path
from core.config_manager import ConfigManager
from core.process_manager import ProcessManager
from core.profile_manager import ProfileManager

def app_directory() -> Path:
    return Path(sys.executable).parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parent

def parse_args():
    parser = argparse.ArgumentParser(description="Launch and close applications using profiles.")
    parser.add_argument("--profile", help="Run a profile by name or ID immediately")
    return parser.parse_args()

def writable_data_directory(root: Path) -> Path:
    """Choose a writable local directory without requiring elevation."""
    try:
        root.mkdir(parents=True, exist_ok=True)
        probe = root / ".write-test"
        probe.touch(); probe.unlink()
        return root
    except OSError:
        fallback = Path(os.environ.get("LOCALAPPDATA", Path.home())) / "AppManager"
        fallback.mkdir(parents=True, exist_ok=True)
        return fallback

def configure_logging(data_root: Path) -> Path:
    log_path = data_root / "app_manager.log"
    logging.basicConfig(filename=log_path, level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s", force=True)
    return log_path

def main() -> int:
    started = __import__("time").perf_counter()
    root = writable_data_directory(app_directory())
    configure_logging(root)
    logging.getLogger(__name__).info("App Manager starting (version 1.0.0)")
    config = ConfigManager(root / "config.json"); processes = ProcessManager(); profiles = ProfileManager(config, processes); args = parse_args()
    from gui.main_window import MainWindow
    window = MainWindow(config, profiles, processes)
    logging.getLogger(__name__).info("Startup reached main loop in %.3f seconds", __import__("time").perf_counter() - started)
    if args.profile:
        profile = profiles.get(args.profile)
        if profile: window.after(150, lambda: window.run_profile(profile))
        else: window.after(150, lambda: window.show_status("error", f'Profile "{args.profile}" was not found.'))
    window.mainloop(); return 0

if __name__ == "__main__": raise SystemExit(main())
