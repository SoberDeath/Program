# App Manager

App Manager is an offline, dark-themed Windows workspace launcher. Profiles close distracting applications, pause for a configurable interval, and open the applications you need without freezing the interface.

## Features

- Unlimited searchable profiles with create, edit, duplicate, delete, and desktop-shortcut actions.
- Safe process control with graceful termination, timeout fallback, protected App Manager PID, and duplicate-launch detection.
- Live progress, per-application results, process browser, configurable timings, startup registration, and dynamic system tray profiles.
- Atomic JSON persistence with automatic recovery and timestamped backup of corrupt configuration.

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

Run `build.bat`. The checked-in PyInstaller specification bundles CustomTkinter theme data, the default configuration, Windows tray backend, and COM modules. The standalone executable is written to `dist\AppManager.exe`.

Configuration and logs are stored beside the script or packaged executable. App Manager does not connect to the internet.
