# HelaKatha (Singlish to Sinhala Input Tool)

A complete, production-ready desktop input method tool for Linux distributions (written in Python 3 using PyQt6 and `pynput`). The application functions exactly like the "Google Singlish Input Tool"—it captures phonetic Singlish keyboard input globally, matches syllables against phonetic transliteration rules and autocomplete dictionaries, displays an elegant candidate list near the cursor, and injects the selected Sinhala script back into the active application.

---

## 1. System Prerequisites

To run this desktop application on Linux, make sure you have Python 3.10+ installed and the required system and Python dependencies:

### A. System Packages (APT/DNF/Pacman)
Universal installer `install.sh` will automatically fetch and install these on modern distros.
*   **xclip / xsel** (recommended for clipboard utility fallback):
    ```bash
    sudo apt update
    sudo apt install -y xclip xsel
    ```

### B. Python Dependencies
Install the graphical user interface framework (`PyQt6`) and the global input hook library (`pynput`) via virtual environment:
```bash
pip install PyQt6 pynput
```

### C. Display Server Compatibility (X11 / Wayland)
The application utilizes global keyboard hooking and coordinate-based floating window positioning.
*   **X11 (Xorg):** Out of the box, `pynput` and `PyQt6` have native permission to capture and inject keys globally.
*   **Wayland:** Wayland has strict process-isolation security boundaries that block applications from sniffing keys globally.
    *   **Workaround:** The application is programmed to force the X11 backend (`os.environ["QT_QPA_PLATFORM"] = "xcb"`). This allows it to run smoothly on default Wayland sessions under **Xwayland**, enabling the global hook to capture keys from any Xwayland-supported application (such as Google Chrome, VS Code, Discord, and terminals).
    *   For full system-wide coverage of all native Wayland applications, it is highly recommended to select the **Ubuntu on Xorg** session at the login screen.

---

## 2. Key Features

### A. Focus-Stealing & Caret Fix
Both the floating `CandidateWindow` and the `NotificationOSD` use the `Qt.WindowType.X11BypassWindowManagerHint` window flag. This completely prevents the window manager from stealing keyboard focus from your active text editor, resolving the hidden text cursor (caret) bug.

### B. Layout-Independent Injection (GNOME Fix)
On Linux/GNOME, simulating Unicode keystrokes by rewriting keyboard maps causes collisions with the OS keyboard layout daemon, leading to jumbled characters (e.g., `ම` replacing `්`). HelaKatha solves this by utilizing **clipboard paste injection** (`Shift + Insert`):
*   Saves your current clipboard.
*   Copies the transliterated word.
*   Triggers paste and runs a non-blocking Qt `QEventLoop` for 100ms. This keeps the GUI event loop responsive to X11 clipboard requests from the target application, preventing clipboard timeouts.
*   Restores/clears the clipboard cleanly after pasting, leaving no trace.
*   Falls back to direct typing if clipboard access is denied.

### C. Draggable Language Switcher Bar
A tiny, sleek floating language indicator (`[සි]` or `[EN]`) sits on your desktop (positioned near the bottom right by default):
*   Click it to toggle instantly between English and Sinhala modes.
*   Click and drag it to place it anywhere on your screen.
*   Uses double-buffering logic to distinguish click events from drags.

### D. Unicode & Legacy (Normal) Font Modes
Sri Lankan print/publishing workflows often rely on legacy (Normal) fonts like `FM Abhaya` or `DL-Manel` that map Sinhala glyphs to Latin keyboard layout codes (e.g. typing `wïud` to render `අම්මා` in FM Abhaya). The app has a dedicated settings tab supporting both systems:
*   **Import Fonts:** Choose and import any `.ttf` file dynamically.
*   **Legacy Mode:** If checked, the app uses 502 official UCSC transliteration rules to convert your Sinhala Unicode on the fly into FM Abhaya ASCII codes.
*   The `CandidateWindow` dynamically renders suggestions using your loaded font. If legacy mode is active, the candidates display their legacy representations (e.g. `wïud`) but look like proper Sinhala to you since the candidate box itself is styled using the imported font!

### E. Settings Persistence
Active configuration settings (loaded font path, font family, and legacy state) are automatically saved to `~/.gemini/antigravity-cli/settings.json` and persist across application restarts.

---

## 3. Project Directory Structure

The project layout is clean, modular, and self-contained:

```text
singlish-input-tool/
├── README.md          # Project setup, running instructions, and guide
├── engine.py          # Phonetic Singlish transliteration parser, 502 legacy rules & dictionaries
├── ui.py              # Modern Catppuccin-themed PyQt6 Windows (Candidate Box, Language Bar, OSD, Settings)
└── main.py            # Main HelaKatha app loop, background threads, settings loader, and event listeners
```

---

## 4. Setup & Running Instructions

The application supports automated installation and virtual environment isolation to ensure compatibility with **any Linux distribution** (Ubuntu/Debian, Fedora/RHEL, Arch, etc.) and bypass PEP 668 blocks.

### Option A: Automated Installation (Recommended for any Distro)
1.  Navigate into the project directory:
    ```bash
    cd singlish-input-tool
    ```
2.  Run the automated installer script:
    ```bash
    ./install.sh
    ```
    *This script will automatically detect your package manager, install system dependencies, configure a local Python virtual environment, create a desktop launcher (`helakatha.desktop`), and add it to your system autostart.*

3.  Search for **"HelaKatha"** in your desktop application menu to launch it, or reboot your system.

### Option B: Manual Setup
1.  Install packages:
    *   **Ubuntu/Debian:** `sudo apt install python3-pip python3-venv xclip xsel`
    *   **Fedora:** `sudo dnf install python3-pip python3-virtualenv xclip xsel`
    *   **Arch:** `sudo pacman -S python-pip xclip xsel`
2.  Set up and activate virtual environment:
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    pip install PyQt6 pynput
    ```
3.  Run the application manually:
    ```bash
    python3 main.py
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
