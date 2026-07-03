@echo off
cd /d "%~dp0"

:: Check if virtual environment exists
if not exist ".venv\Scripts\pythonw.exe" (
    echo [ERROR] Virtual environment not found. Please run 'install.bat' first.
    pause
    exit /b 1
)

:: Start the application in windowed mode (no terminal console window showing)
start "" ".venv\Scripts\pythonw.exe" "main.py"
