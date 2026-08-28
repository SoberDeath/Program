@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title AppManager V1.0 // BUILD SYSTEM
color 0B

:menu
cls
call :logo
echo.
echo       +------------------------------------------------------------------+
echo       ^|                         BUILD CONTROL                            ^|
echo       +------------------------------------------------------------------+
echo       ^|                                                                  ^|
echo       ^|   [1]  QUICK BUILD        Progress screen only                    ^|
echo       ^|   [2]  TECHNICAL BUILD    Full compiler / PyInstaller output     ^|
echo       ^|   [3]  EXIT               Close build system                     ^|
echo       ^|                                                                  ^|
echo       +------------------------------------------------------------------+
echo.
set /p "choice=            SELECT MODE  ^> "

if "%choice%"=="1" goto normal
if "%choice%"=="2" goto technical
if "%choice%"=="3" exit /b 0
goto menu

:normal
call :quick_screen 0 "INITIALIZING BUILD PIPELINE"
call :quick_screen 10 "VERIFYING PYTHON ENVIRONMENT"
cmd /d /c "py -3 --version >nul 2>&1" || goto quick_python_error

call :quick_screen 20 "SYNCING BUILD DEPENDENCIES"
cmd /d /c "py -3 -m pip install --upgrade -r requirements.txt >nul 2>&1" || goto quick_build_error

call :quick_screen 45 "PURGING PREVIOUS BUILD CACHE"
if exist "build" cmd /d /c "rmdir /s /q build >nul 2>&1"

call :quick_screen 55 "COMPILING APPMANAGER"
cmd /d /c "py -3 -m PyInstaller --noconfirm --clean AppManager.spec >nul 2>&1" || goto quick_build_error

call :quick_screen 95 "VERIFYING RELEASE ARTIFACT"
if not exist "dist\AppManager\AppManager.exe" goto quick_build_error

call :quick_screen 100 "BUILD COMPLETE"
timeout /t 1 /nobreak >nul
cls
call :logo
echo.
echo       +------------------------------------------------------------------+
echo       ^|                    APPMANAGER V1.0 READY                         ^|
echo       +------------------------------------------------------------------+
echo.
echo          %CD%\dist\AppManager\AppManager.exe
echo.
pause
goto menu

:technical
cls
call :logo
call :modebar "TECHNICAL BUILD // VERBOSE TELEMETRY"
echo.
call :progress 0 "INITIALIZING TECHNICAL PIPELINE"
echo.
call :progress 10 "VERIFYING PYTHON ENVIRONMENT"
py -3 --version || goto python_error
echo.
call :progress 20 "SYNCING BUILD DEPENDENCIES"
echo       --------------------------------------------------------------------
py -3 -m pip install --upgrade -r requirements.txt || goto build_error
echo       --------------------------------------------------------------------
echo.
call :progress 45 "PURGING PREVIOUS BUILD CACHE"
if exist "build" (
    echo          REMOVE  ^>  %CD%\build
    rmdir /s /q "build"
) else (
    echo          CACHE   ^>  CLEAN
)
echo.
call :progress 55 "PYINSTALLER COMPILATION"
echo       --------------------------------------------------------------------
py -3 -m PyInstaller --noconfirm --clean AppManager.spec || goto build_error
echo       --------------------------------------------------------------------
echo.
call :progress 95 "VERIFYING RELEASE ARTIFACT"
if not exist "dist\AppManager\AppManager.exe" goto build_error
echo          FOUND   ^>  %CD%\dist\AppManager\AppManager.exe
echo.
call :progress 100 "TECHNICAL BUILD COMPLETE"
echo.
echo       +------------------------------------------------------------------+
echo       ^|  [OK] APPMANAGER V1.0 READY // BUILD PIPELINE NOMINAL             ^|
echo       +------------------------------------------------------------------+
echo.
echo          RELEASE  ^>  %CD%\dist\AppManager\AppManager.exe
echo.
pause
goto menu

:quick_screen
set "pct=%~1"
set "msg=%~2"
set "bar=........................................"
if %pct% GEQ 10 set "bar=####...................................."
if %pct% GEQ 20 set "bar=########................................"
if %pct% GEQ 45 set "bar=##################......................"
if %pct% GEQ 55 set "bar=######################.................."
if %pct% GEQ 95 set "bar=######################################.."
if %pct% GEQ 100 set "bar=########################################"
cls
call :logo
echo.
echo       ====================================================================
echo                               QUICK BUILD
echo       ====================================================================
echo.
echo.
echo                [%bar%] %pct%%%
echo.
echo                     %msg%
echo.
echo.
echo                         PLEASE WAIT...
exit /b 0

:progress
set "pct=%~1"
set "msg=%~2"
set "bar=........................................"
if %pct% GEQ 10 set "bar=####...................................."
if %pct% GEQ 20 set "bar=########................................"
if %pct% GEQ 45 set "bar=##################......................"
if %pct% GEQ 55 set "bar=######################.................."
if %pct% GEQ 95 set "bar=######################################.."
if %pct% GEQ 100 set "bar=########################################"
echo.
echo       [%bar%] %pct%%%
echo       ^> %msg%
exit /b 0

:modebar
echo.
echo       ====================================================================
echo          %~1
echo       ====================================================================
exit /b 0

:quick_python_error
cls
call :logo
echo.
echo       [ERROR] Python 3 was not found.
echo.
echo       Run TECHNICAL BUILD for diagnostic information.
echo.
pause
goto menu

:quick_build_error
cls
call :logo
echo.
echo       [FAILED] Quick Build could not complete.
echo.
echo       Run option [2] TECHNICAL BUILD to see the full error output.
echo.
pause
goto menu

:python_error
echo.
echo       +------------------------------------------------------------------+
echo       ^|  [ERROR] PYTHON 3 NOT DETECTED                                   ^|
echo       +------------------------------------------------------------------+
echo          Install Python 3 and verify that the 'py' launcher is available.
echo.
pause
goto menu

:build_error
echo.
echo       +------------------------------------------------------------------+
echo       ^|  [FAILED] BUILD PIPELINE INTERRUPTED                              ^|
echo       +------------------------------------------------------------------+
echo          Run [2] TECHNICAL BUILD for complete diagnostic output.
echo.
pause
goto menu

:logo
echo.
echo.
echo          ################################################################
echo          ##                                                            ##
echo          ##        ___    ____   ____    __  __    _    _   _          ##
echo          ##       / _ \  ^|  _ \ ^|  _ \  ^|  \/  ^|  / \  ^| \ ^| ^|         ##
echo          ##      / /_\ \ ^| ^|_) ^|^| ^|_) ^| ^| ^|\/^| ^| / _ \ ^|  \^| ^|         ##
echo          ##      ^|  _  ^|^|  __/ ^|  __/  ^| ^|  ^| ^|/ ___ \^| ^|\  ^|         ##
echo          ##      ^|_^| ^|_^|^|_^|    ^|_^|     ^|_^|  ^|_^|_/   \_\_^| \_^|         ##
echo          ##                                                            ##
echo          ##                    M A N A G E R                           ##
echo          ##                                                            ##
echo          ################################################################
echo.
echo                       APPMANAGER // VERSION 1.0
echo                    WINDOWS WORKSPACE CONTROL SYSTEM
echo.
exit /b 0
