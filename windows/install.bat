@echo off
setlocal enabledelayedexpansion

echo ==============================================
echo       HelaKatha Windows Installer
echo ==============================================

:: Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in your PATH.
    echo Please install Python 3.10+ from https://www.python.org/ and check "Add Python to PATH" during installation.
    pause
    exit /b 1
)

echo [1/3] Creating virtual environment (.venv)...
python -m venv .venv
if %errorlevel% neq 0 (
    echo [ERROR] Failed to create virtual environment.
    pause
    exit /b 1
)

echo [2/3] Installing dependencies...
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\pip.exe install -r requirements.txt
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install dependencies.
    pause
    exit /b 1
)

echo [3/3] Creating Desktop Shortcut...
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    "$s = (New-Object -ComObject WScript.Shell).CreateShortcut('%USERPROFILE%\Desktop\HelaKatha.lnk');" ^
    "$s.TargetPath = '%~dp0run.bat';" ^
    "$s.WorkingDirectory = '%~dp0';" ^
    "$s.IconLocation = 'shell32.dll,44';" ^
    "$s.Save();"

if %errorlevel% equ 0 (
    echo [INFO] Desktop shortcut 'HelaKatha' created successfully!
) else (
    echo [WARNING] Failed to create desktop shortcut.
)

echo ==============================================
echo Installation complete!
echo Double-click 'HelaKatha' on your Desktop or run 'run.bat' to start.
echo ==============================================
pause
