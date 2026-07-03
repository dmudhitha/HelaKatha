@echo off
setlocal enabledelayedexpansion

echo ==============================================
echo       HelaKatha Windows Build System
echo ==============================================

:: 1. Check if virtual environment exists
if not exist ".venv\Scripts\python.exe" (
    echo [ERROR] Virtual environment (.venv) not found. Please run 'install.bat' first.
    pause
    exit /b 1
)

:: 2. Install PyInstaller
echo.
echo [1/4] Checking and installing PyInstaller...
.venv\Scripts\pip.exe install pyinstaller
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install PyInstaller.
    pause
    exit /b 1
)

:: 3. Generate icon.ico
echo.
echo [2/4] Generating native Windows application icon...
.venv\Scripts\python.exe generate_icon.py
if %errorlevel% neq 0 (
    echo [WARNING] Failed to generate icon.ico. Default executable icon will be used.
)

:: 4. Build executable
echo.
echo [3/4] Building standalone executable using PyInstaller...
if exist icon.ico (
    .venv\Scripts\pyinstaller.exe --clean --noconsole --onefile --icon=icon.ico --name HelaKatha main.py
) else (
    .venv\Scripts\pyinstaller.exe --clean --noconsole --onefile --name HelaKatha main.py
)

if %errorlevel% neq 0 (
    echo [ERROR] PyInstaller build failed.
    pause
    exit /b 1
)
echo [INFO] Standalone executable created successfully at: dist\HelaKatha.exe

:: 5. Locate Inno Setup compiler (ISCC.exe)
echo.
echo [4/4] Checking for Inno Setup compiler...
set "ISCC_PATH="

:: Try finding in PATH
where ISCC.exe >nul 2>&1
if %errorlevel% equ 0 (
    for /f "tokens=*" %%i in ('where ISCC.exe') do set "ISCC_PATH=%%i"
)

:: Try standard installation paths
if "%ISCC_PATH%"=="" (
    if exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" (
        set "ISCC_PATH=C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
    ) else if exist "C:\Program Files\Inno Setup 6\ISCC.exe" (
        set "ISCC_PATH=C:\Program Files\Inno Setup 6\ISCC.exe"
    )
)

:: Compile installer if ISCC.exe is found
if not "%ISCC_PATH%"=="" (
    echo [INFO] Found Inno Setup compiler at: "!ISCC_PATH!"
    echo Compiling installer...
    "!ISCC_PATH!" setup.iss
    if !errorlevel! equ 0 (
        echo.
        echo ==============================================
        echo [SUCCESS] Windows Installer created successfully:
        echo           HelaKathaSetup.exe
        echo ==============================================
    ) else (
        echo [ERROR] Inno Setup compilation failed.
    )
) else (
    echo.
    echo ==============================================================
    echo [WARNING] Inno Setup compiler (ISCC.exe) was not found.
    echo.
    echo A standalone executable was built successfully at:
    echo dist\HelaKatha.exe
    echo.
    echo To compile the standard Setup Wizard installer (HelaKathaSetup.exe):
    echo 1. Install Inno Setup (run: winget install JRSoftware.InnoSetup).
    echo 2. Run this script again, or right-click 'setup.iss' and select 'Compile'.
    echo ==============================================================
)

pause
