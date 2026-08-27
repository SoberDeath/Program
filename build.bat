@echo off
setlocal
cd /d "%~dp0"
echo [App Manager] Installing build dependencies...
py -3 -m pip install --upgrade -r requirements.txt || exit /b 1
echo [App Manager] Building standalone Windows executable...
py -3 -m PyInstaller --noconfirm --clean AppManager.spec || exit /b 1
echo.
echo Build complete: %CD%\dist\AppManager.exe
endlocal
