@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title AppManager V1.0 - Build
color 0B

:menu
cls
call :logo
echo.
echo  ================================================================
echo   BUILD MODE
echo  ================================================================
echo.
echo   [1] Normal Build
 echo       Clean interface with build progress only.
echo.
echo   [2] Technical Build
 echo       Shows detailed pip / PyInstaller output and progress stages.
echo.
echo   [3] Exit
echo.
set /p "choice=  Select an option [1-3]: "

if "%choice%"=="1" goto normal
if "%choice%"=="2" goto technical
if "%choice%"=="3" exit /b 0
goto menu

:normal
cls
call :logo
echo.
call :progress 0 "Starting build"
call :progress 10 "Checking Python"
py -3 --version >nul 2>&1 || goto python_error

call :progress 20 "Installing build dependencies"
py -3 -m pip install --upgrade -r requirements.txt >nul 2>&1 || goto build_error

call :progress 45 "Preparing PyInstaller"
if exist "build" rmdir /s /q "build" >nul 2>&1

call :progress 55 "Building AppManager.exe"
py -3 -m PyInstaller --noconfirm --clean AppManager.spec >nul 2>&1 || goto build_error

call :progress 95 "Finalizing build"
if not exist "dist\AppManager\AppManager.exe" goto build_error
call :progress 100 "Build complete"
echo.
echo  ================================================================
echo   SUCCESS
 echo  ================================================================
echo   AppManager V1.0 has been built successfully.
echo.
echo   EXE:
echo   %CD%\dist\AppManager\AppManager.exe
echo  ================================================================
echo.
pause
goto menu

:technical
cls
call :logo
echo.
echo  ================================================================
echo   TECHNICAL BUILD MODE
 echo   Detailed output is enabled.
echo  ================================================================
echo.
call :progress 0 "Starting technical build"
echo.

call :progress 10 "Checking Python installation"
py -3 --version || goto python_error
echo.

call :progress 20 "Installing / updating dependencies"
echo  ---------------------------------------------------------------
py -3 -m pip install --upgrade -r requirements.txt || goto build_error
echo  ---------------------------------------------------------------
echo.

call :progress 45 "Cleaning previous build cache"
if exist "build" (
    echo   Removing: %CD%\build
    rmdir /s /q "build"
) else (
    echo   No previous build cache found.
)
echo.

call :progress 55 "Running PyInstaller"
echo  ---------------------------------------------------------------
py -3 -m PyInstaller --noconfirm --clean AppManager.spec || goto build_error
echo  ---------------------------------------------------------------
echo.

call :progress 95 "Verifying executable"
if not exist "dist\AppManager\AppManager.exe" (
    echo   [ERROR] Expected executable was not created.
    goto build_error
)
echo   Found: %CD%\dist\AppManager\AppManager.exe
echo.

call :progress 100 "Technical build complete"
echo.
echo  ================================================================
echo   SUCCESS - AppManager V1.0
 echo  ================================================================
echo   Output:
echo   %CD%\dist\AppManager\AppManager.exe
echo  ================================================================
echo.
pause
goto menu

:progress
set "pct=%~1"
set "msg=%~2"
echo   [%pct%%%] %msg%
exit /b 0

:python_error
echo.
echo  ================================================================
echo   ERROR: Python 3 was not found.
echo   Install Python 3 and make sure the 'py' launcher is available.
echo  ================================================================
echo.
pause
goto menu

:build_error
echo.
echo  ================================================================
echo   BUILD FAILED
 echo   The build stopped because one of the commands returned an error.
echo   Run option [2] Technical Build to see the full error output.
echo  ================================================================
echo.
pause
goto menu

:logo
echo.
echo      AAA   PPPP   PPPP   M   M   AAA   N   N   AAA   GGGG EEEEE RRRR
echo     A   A  P   P  P   P  MM MM  A   A  NN  N  A   A G     E     R   R
echo     AAAAA  PPPP   PPPP   M M M  AAAAA  N N N  AAAAA G GGG EEEE  RRRR
echo     A   A  P      P      M   M  A   A  N  NN  A   A G   G E     R  R
echo     A   A  P      P      M   M  A   A  N   N  A   A  GGG  EEEEE R   R
echo.
echo                         AppManager V1.0
exit /b 0
