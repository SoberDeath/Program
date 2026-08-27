"""App Manager application entry point."""
from __future__ import annotations
import argparse, logging, sys
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

def main() -> int:
    root = app_directory(); logging.basicConfig(filename=root / "app_manager.log", level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    config = ConfigManager(root / "config.json"); processes = ProcessManager(); profiles = ProfileManager(config, processes); args = parse_args()
    from gui.main_window import MainWindow
    window = MainWindow(config, profiles, processes)
    if args.profile:
        profile = profiles.get(args.profile)
        if profile: window.after(150, lambda: window.run_profile(profile))
        else: window.after(150, lambda: window.show_status("error", f'Profile "{args.profile}" was not found.'))
    window.mainloop(); return 0

if __name__ == "__main__": raise SystemExit(main())
