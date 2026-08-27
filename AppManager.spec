from PyInstaller.utils.hooks import collect_data_files

datas = collect_data_files("customtkinter") + [("config.json", ".")]

a = Analysis(["main.py"], pathex=[], binaries=[], datas=datas,
             hiddenimports=["pystray._win32", "win32com.client", "pythoncom", "pywintypes"],
             hookspath=[], hooksconfig={}, runtime_hooks=[], excludes=[], noarchive=False)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, a.binaries, a.datas, [], name="AppManager", debug=False,
          bootloader_ignore_signals=False, strip=False, upx=True, console=False,
          disable_windowed_traceback=False, argv_emulation=False, target_arch=None, codesign_identity=None, entitlements_file=None)
