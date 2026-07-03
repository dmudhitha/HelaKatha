# HelaKatha (Singlish to Sinhala Input Tool) - Windows Version

A complete, production-ready desktop input method tool for Windows (written in Python 3 using PyQt6 and `pynput`). The application functions exactly like the "Google Singlish Input Tool"—it captures phonetic Singlish keyboard input globally, matches syllables against phonetic transliteration rules and autocomplete dictionaries, displays an elegant candidate list near the cursor, and injects the selected Sinhala script back into the active application.

---

## 1. System Prerequisites

To run this desktop application on Windows, make sure you have Python 3.10+ installed and added to your system PATH:

1. Download the installer from the [Official Python Website](https://www.python.org/downloads/).
2. Run the installer and **MUST check the box that says "Add Python.exe to PATH"** before clicking install.
3. Everything else is handled automatically by the installer script (`install.bat`).

---

## 2. Key Features

### A. Focus-Stealing & Caret Fix
Both the floating `CandidateWindow` and the `NotificationOSD` use flags that prevent Windows from stealing keyboard focus from your active text editor. This allows you to type continuously without losing cursor caret visibility.

### B. Layout-Independent Injection (Windows Paste Fix)
Simulating raw Unicode keystrokes can cause collisions with active keyboard layouts, leading to jumbled characters. HelaKatha solves this by utilizing **clipboard paste injection** (`Ctrl + V`):
*   Saves your current clipboard.
*   Copies the transliterated word.
*   Triggers paste and runs a non-blocking Qt event loop for 100ms so the target application has time to paste.
*   Restores your original clipboard content immediately after, leaving no trace.
*   Falls back to direct typing if clipboard access is denied.

### C. Draggable Language Switcher Bar
A tiny, sleek floating language indicator (`[සි]` or `[EN]`) sits on your desktop (positioned near the bottom right by default):
*   Click it to toggle instantly between English and Sinhala modes.
*   Click and drag it to place it anywhere on your screen.

### D. Unicode & Legacy (Normal) Font Modes
Sri Lankan print/publishing workflows often rely on legacy (Normal) fonts like `FM Abhaya` or `DL-Manel` that map Sinhala glyphs to Latin keyboard layout codes. The app has a dedicated settings tab supporting both systems:
*   **Import Fonts:** Choose and import any `.ttf` file dynamically.
*   **Legacy Mode:** If checked, the app uses 502 official UCSC transliteration rules to convert your Sinhala Unicode on the fly into FM Abhaya ASCII codes.
*   The `CandidateWindow` dynamically renders suggestions using your loaded font. If legacy mode is active, the candidates display their legacy representations (e.g. `wïud`) but look like proper Sinhala to you since the candidate box itself is styled using the imported font!

### E. Settings Persistence
Active configuration settings (loaded font path, font family, and legacy state) are automatically saved to `%USERPROFILE%\.gemini\antigravity-cli\settings.json` and persist across application restarts.

---

## 3. Project Directory Structure

The Windows version project layout is clean, modular, and self-contained:

```text
windows/
├── README.md          # Setup and running instructions for Windows
├── engine.py          # Phonetic Singlish transliteration parser
├── ui.py              # Modern Catppuccin-themed PyQt6 Windows (using Segoe UI system font)
├── main.py            # Main HelaKatha app loop, background threads, and hotkeys
├── requirements.txt   # Python package dependencies
├── install.bat        # Automated virtual environment setup and desktop shortcut creator
└── run.bat            # Silent background launcher utilizing pythonw.exe
```

---

## 4. Setup & Running Instructions

### Option A: Automated Installation (Recommended)
1. Double-click the `install.bat` file in this directory.
2. It will automatically check for Python, set up a virtual environment in `.venv`, install all packages from `requirements.txt`, and create a desktop shortcut named **HelaKatha**.
3. Double-click the newly created **HelaKatha** shortcut on your Desktop to launch the application.

### Option B: Manual Setup
1. Open Command Prompt (`cmd`) or PowerShell in this directory.
2. Create a virtual environment:
   ```cmd
   python -m venv .venv
   ```
3. Activate the virtual environment:
   ```cmd
   .venv\Scripts\activate.bat
   ```
4. Install requirements:
   ```cmd
   pip install -r requirements.txt
   ```
5. Run the application:
   - For interactive mode with logs:
     ```cmd
     python main.py
     ```
   - For background silent mode (no command prompt window):
     ```cmd
     pythonw main.py
     ```

Once running, you will see a green **"HelaKatha: ENABLED"** notification fade in and out in the center of your screen. A purple icon (`සි`) will also appear in your system tray and a draggable language pill will appear on your desktop.

### How to Use:
*   **Toggle State:** Press `Ctrl + Space` anywhere or click the floating language bar to toggle the HelaKatha tool ON or OFF.
*   **Type phonetically:** Open any text editor or browser search bar. Type `amma`. You will see a dark suggestion box slide in near your cursor:
    ```text
    1. අම්ම
    2. අම්මා
    3. අම්මලා
    4. amma
    ```
*   **Selection:** Press `Space` to select the first candidate (`අම්ම`). Press a number key (e.g., `2`) to select that specific candidate. Selecting a candidate automatically appends a trailing space for fast typing.
*   **Type English:** Press `4` (or the index of the English word) to insert the English word `amma` without toggling off the input tool.
*   **Dismiss:** Press `Esc` to hide the candidate window and keep the typed English characters as they are.
*   **Font & Legacy Settings:** Right-click the system tray icon and select **"Typing Guide (Help)"** (or double-click the tray icon). Select the **Font Settings** tab to import a custom `.ttf` font or enable/disable **Legacy / Normal Font Mode**.

---

## 5. Compiling Standalone Executable & Setup Installer

If you want to package the application so that it runs as a standalone `.exe` without requiring Python, or if you want to generate a standard installer wizard (`HelaKathaSetup.exe`), follow these steps:

1. Make sure you have run `install.bat` at least once to create the virtual environment.
2. (Optional) Install **Inno Setup** to compile the setup installer wizard (run: `winget install JRSoftware.InnoSetup` in a command prompt or download from the Inno Setup website).
3. Double-click **`build_installer.bat`**.
4. The script will:
   - Install `pyinstaller` in your virtual environment.
   - Run `generate_icon.py` to render the Windows `icon.ico`.
   - Compile `main.py` into a single standalone program: `dist\HelaKatha.exe`.
   - Compile `setup.iss` with Inno Setup to create the setup wizard installer: **`HelaKathaSetup.exe`**.

If you share the resulting `HelaKathaSetup.exe`, users can install HelaKatha like any other Windows application without having to install Python or know how to run scripts!

