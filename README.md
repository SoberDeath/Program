# App Manager

App Manager is an offline, dark-themed Windows workspace launcher. Profiles close distracting applications, pause for a configurable interval, and open the applications you need without freezing the interface.

## Features

- Unlimited searchable profiles with create, edit, duplicate, delete, and desktop-shortcut actions.
- Safe process control with graceful termination, timeout fallback, protected App Manager PID, and duplicate-launch detection.
- Live progress, per-application results, process browser, configurable timings, startup registration, and dynamic system tray profiles.
- Atomic JSON persistence with automatic recovery and timestamped backup of corrupt configuration.
- Lightweight Unicode navigation symbols and native CustomTkinter controls require no bundled image assets.
- Cached pages, debounced in-memory search, lazy executable details, and a four-worker background pool keep navigation responsive.

## Run from source

Requires Python 3.10+ on Windows.

```powershell
py -3 -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

Run a saved profile immediately:

```powershell
python main.py --profile "Gaming"
```

## Build

Run `build.bat`. The checked-in PyInstaller specification creates a fast-starting **onedir** distribution at `dist\AppManager\AppManager.exe`. It bundles CustomTkinter theme data, the default configuration, Windows tray backend, and COM modules without paying the extraction cost of a onefile executable on every launch.

Configuration and logs are stored beside the script or packaged executable. App Manager does not connect to the internet.

Useful performance timings are written to `app_manager.log` at debug level for configuration loading, window construction, navigation, dashboard rendering, process snapshots, and process rendering.
