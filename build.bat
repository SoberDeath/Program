@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title AppManager V1.1 // BUILD SYSTEM
color 0B

set "ANIM=%~dp0build_animation.py"
set "ICON_GEN=%~dp0generate_icon.py"

rem Initial animated boot sequence. The animation finishes on the final build menu.
if exist "%ANIM%" (
    where py >nul 2>&1
    if not errorlevel 1 (
        py -3 "%ANIM%"
    ) else (
        where python >nul 2>&1
        if not errorlevel 1 python "%ANIM%"
    )
)

:menu
if not "%choice%"=="" set "choice="
if exist "%ANIM%" call :draw_menu
echo.
set /p "choice=  SELECT MODE  ^> "
if "%choice%"=="1" goto normal
if "%choice%"=="2" goto technical
if "%choice%"=="3" exit /b 0
goto menu

:normal
call :quick_screen 0 "INITIALIZING BUILD PIPELINE"
call :quick_screen 10 "VERIFYING PYTHON ENVIRONMENT"
cmd /d /c "py -3 --version >nul 2>&1" || goto quick_python_error
call :quick_screen 18 "GENERATING APP ICON"
cmd /d /c "py -3 generate_icon.py >nul 2>&1" || goto quick_build_error
call :quick_screen 25 "SYNCING BUILD DEPENDENCIES"
cmd /d /c "py -3 -m pip install --upgrade -r requirements.txt >nul 2>&1" || goto quick_build_error
call :quick_screen 45 "PURGING PREVIOUS BUILD CACHE"
if exist "build" cmd /d /c "rmdir /s /q build >nul 2>&1"
call :quick_screen 55 "COMPILING APPMANAGER V1.1"
cmd /d /c "py -3 -m PyInstaller --noconfirm --clean AppManager.spec >nul 2>&1" || goto quick_build_error
call :quick_screen 95 "VERIFYING RELEASE ARTIFACT"
if not exist "dist\AppManager\AppManager.exe" goto quick_build_error
call :quick_screen 100 "BUILD COMPLETE"
timeout /t 1 /nobreak >nul
call :draw_header
echo.
echo                 APPMANAGER V1.1 READY
echo.
echo          %CD%\dist\AppManager\AppManager.exe
echo.
pause
goto menu

:technical
call :draw_header
echo.
echo  TECHNICAL BUILD // VERBOSE TELEMETRY
echo.
call :progress 0 "INITIALIZING TECHNICAL PIPELINE"
echo.
call :progress 10 "VERIFYING PYTHON ENVIRONMENT"
py -3 --version || goto python_error
echo.
call :progress 18 "GENERATING APP ICON"
py -3 generate_icon.py || goto build_error
echo.
call :progress 25 "SYNCING BUILD DEPENDENCIES"
echo  --------------------------------------------------------------------
py -3 -m pip install --upgrade -r requirements.txt || goto build_error
echo  --------------------------------------------------------------------
echo.
call :progress 45 "PURGING PREVIOUS BUILD CACHE"
if exist "build" (
    echo  REMOVE  ^>  %CD%\build
    rmdir /s /q "build"
) else (
    echo  CACHE   ^>  CLEAN
)
echo.
call :progress 55 "PYINSTALLER COMPILATION"
echo  --------------------------------------------------------------------
py -3 -m PyInstaller --noconfirm --clean AppManager.spec || goto build_error
echo  --------------------------------------------------------------------
echo.
call :progress 95 "VERIFYING RELEASE ARTIFACT"
if not exist "dist\AppManager\AppManager.exe" goto build_error
echo  FOUND   ^>  %CD%\dist\AppManager\AppManager.exe
echo.
call :progress 100 "TECHNICAL BUILD COMPLETE"
echo.
echo  APPMANAGER V1.1 READY // BUILD PIPELINE NOMINAL
echo  RELEASE  ^>  %CD%\dist\AppManager\AppManager.exe
echo.
pause
goto menu

:quick_screen
set "pct=%~1"
set "msg=%~2"
where py >nul 2>&1
if not errorlevel 1 (
    py -3 "%ANIM%" --quick %pct% "%msg%"
    exit /b 0
)
where python >nul 2>&1
if not errorlevel 1 (
    python "%ANIM%" --quick %pct% "%msg%"
    exit /b 0
)
exit /b 0

:progress
set "pct=%~1"
set "msg=%~2"
set "bar=........................................"
if %pct% GEQ 10 set "bar=####...................................."
if %pct% GEQ 18 set "bar=#######................................."
if %pct% GEQ 25 set "bar=##########.............................."
if %pct% GEQ 45 set "bar=##################......................"
if %pct% GEQ 55 set "bar=######################.................."
if %pct% GEQ 95 set "bar=######################################.."
if %pct% GEQ 100 set "bar=########################################"
echo.
echo  [%bar%] %pct%%%
echo  ^> %msg%
exit /b 0

:draw_menu
where py >nul 2>&1
if not errorlevel 1 (
    py -3 "%ANIM%" --menu
    exit /b 0
)
where python >nul 2>&1
if not errorlevel 1 python "%ANIM%" --menu
exit /b 0

:draw_header
where py >nul 2>&1
if not errorlevel 1 (
    py -3 "%ANIM%" --header
    exit /b 0
)
where python >nul 2>&1
if not errorlevel 1 python "%ANIM%" --header
exit /b 0

:quick_python_error
call :draw_header
echo.
echo  [ERROR] Python 3 was not found.
echo  Run TECHNICAL BUILD for diagnostic information.
echo.
pause
goto menu

:quick_build_error
call :draw_header
echo.
echo  [FAILED] Quick Build could not complete.
echo  Run option [2] TECHNICAL BUILD to see the full error output.
echo.
pause
goto menu

:python_error
echo.
echo  [ERROR] PYTHON 3 NOT DETECTED
echo  Install Python 3 and verify that the 'py' launcher is available.
echo.
pause
goto menu

:build_error
echo.
echo  [FAILED] BUILD PIPELINE INTERRUPTED
echo  Run [2] TECHNICAL BUILD for complete diagnostic output.
echo.
pause
goto menu
